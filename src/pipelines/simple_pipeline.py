# src/pipelines/simple_pipeline.py
import os
import time
import logging
from typing import Dict, Any, Optional

from .base_pipeline import IPipeline
from src.utils.temp_file_manager import TempFileManager
from src.core.video_database import VideoDatabase, VideoRecord
from src.core.git_versioning import GitVersioning

logger = logging.getLogger("TikSimPro")

class SimplePipeline(IPipeline):
    """Simple pipeline with unified temporary file management"""
    
    def __init__(self, output_dir: str = "output", auto_publish: bool = False, 
                 video_duration: int = 60, video_dimensions = [1080, 1920], fps: int = 30):
        super().__init__()
        
        self.config = {
            "output_dir": output_dir,
            "auto_publish": auto_publish,
            "video_duration": video_duration,
            "video_dimensions": video_dimensions,
            "fps": fps
        }
        
        # ONE unified temporary file manager for the entire pipeline
        self.temp_manager = TempFileManager(
            base_temp_dir="temp",
            auto_cleanup=True,
            keep_on_error=True,  # Keep for debugging
            max_age_hours=24
        )

        # Database for tracking videos and performance
        self.db = VideoDatabase()

        # Git versioning for tracking code changes
        try:
            self.git = GitVersioning()
        except ValueError:
            self.git = None
            logger.warning("Git versioning disabled (not a git repository)")

        # Track current video ID for this run
        self._current_video_id: Optional[int] = None

        os.makedirs(self.config["output_dir"], exist_ok=True)
        logger.info("SimplePipeline initialized with unified temp management and database tracking")
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure the pipeline with specific parameters
        
        Args:
            config: Configuration parameters
            
        Returns:
            True if configuration succeeded, False otherwise
        """
        try:
            # Update internal config with provided parameters
            self.config.update(config)
            
            # Ensure output directory exists
            os.makedirs(self.config["output_dir"], exist_ok=True)
            
            logger.info(f"Pipeline configured: {self.config}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure pipeline: {e}")
            return False
    
    def execute(self) -> Optional[str]:
        """Execute pipeline with unified temporary file management"""
        try:
            timestamp = int(time.time())
            logger.info("Starting content pipeline...")
            
            # Initialize paths for each step (all using the same temp manager)
            trend_file = None
            video_file = None
            audio_file = None
            combined_file = None
            enhanced_file = None
            
            # ===== STEP 1: TREND ANALYSIS =====
            logger.info("1/5: Analyzing trends...")
            try:
                if not self.trend_analyzer:
                    logger.error("No trend analyzer configured")
                    return None
                
                trend_data = self.trend_analyzer.get_trend_analysis()
                if not trend_data:
                    logger.error("Trend analysis failed")
                    return None
                
                # Save trend data using unified temp manager
                trend_file = self.temp_manager.create_temp_file("trend_analysis", "trends", "json")
                trend_file.write_text(trend_data.to_json(), encoding='utf-8')
                logger.info(f"Trends saved: {trend_file}")
                
            except Exception as e:
                logger.error(f"Trend analysis error: {e}")
                self.temp_manager.mark_error()
                return None
            
            # ===== STEP 2: VIDEO GENERATION =====
            logger.info("2/5: Generating video...")
            try:
                if not self.video_generator:
                    logger.error("No video generator configured")
                    return None
                
                # Create video file path using unified temp manager
                video_file = self.temp_manager.create_video_file("video_generation", "mp4", "raw")
                
                # Configure and generate
                self.video_generator.set_output_path(str(video_file))
                self.video_generator.apply_trend_data(trend_data)
                
                result_video = self.video_generator.generate()
                
                # Check if video was created (even if generator returns None due to flush error)
                if result_video and os.path.exists(result_video):
                    video_file = result_video
                    logger.info(f"Video generated: {video_file}")
                elif os.path.exists(str(video_file)):
                    # Fallback: check if video was created at expected path
                    file_size = os.path.getsize(str(video_file)) / (1024*1024)
                    if file_size > 0.1:  # File has content
                        logger.info(f"Video generated successfully (despite error): {video_file} ({file_size:.1f} MB)")
                    else:
                        logger.error("Video file is empty")
                        self.temp_manager.mark_error()
                        return None
                else:
                    logger.error("Video generation failed or file not found")
                    self.temp_manager.mark_error()
                    return None
                
            except Exception as e:
                logger.error(f"Video generation error: {e}")
                self.temp_manager.mark_error()
                return None
            
            # ===== STEP 3: AUDIO GENERATION =====
            logger.info("3/5: Generating audio...")
            try:
                if self.audio_generator:
                    # Create audio file path using unified temp manager
                    audio_file = self.temp_manager.create_audio_file("audio_generation", "wav")
                    
                    self.audio_generator.set_output_path(str(audio_file))
                    self.audio_generator.set_duration(self.config["video_duration"])
                    self.audio_generator.apply_trend_data(trend_data)
                    
                    # Get audio events from video generator
                    if hasattr(self.video_generator, 'get_audio_events'):
                        events = self.video_generator.get_audio_events()
                        self.audio_generator.add_events(events)
                        logger.debug(f"Added {len(events)} audio events")
                    
                    audio_result = self.audio_generator.generate()
                    if audio_result and os.path.exists(audio_result):
                        audio_file = audio_result
                        logger.info(f"Audio generated: {audio_file}")
                    else:
                        logger.warning("Audio generation failed, continuing without audio")
                        audio_file = None
                else:
                    logger.info("No audio generator configured, skipping audio")
                    audio_file = None
                    
            except Exception as e:
                logger.error(f"Audio generation error: {e}")
                audio_file = None  # Continue without audio
            
            # Current video path (for next step)
            current_video = video_file
            
            # ===== STEP 4: MEDIA COMBINATION =====
            logger.info("4/5: Combining media...")
            try:
                if audio_file and self.media_combiner and os.path.exists(audio_file):
                    # Verify video file still exists
                    if not os.path.exists(current_video):
                        logger.error(f"Video file disappeared: {current_video}")
                        self.temp_manager.mark_error()
                        return None
                    
                    # Create combined file path using unified temp manager
                    combined_file = self.temp_manager.create_video_file("media_combination", "mp4", "combined")
                    
                    combined_result = self.media_combiner.combine(
                        current_video, audio_file, str(combined_file)
                    )
                    
                    if combined_result and os.path.exists(combined_result):
                        current_video = combined_result
                        logger.info(f"Media combined: {combined_result}")
                    else:
                        logger.warning("Media combination failed, using video only")
                        # Keep current_video as is
                else:
                    logger.info("Skipping media combination (no audio or combiner)")
                    
            except Exception as e:
                logger.error(f"Media combination error: {e}")
                # Continue with video only
            
            # ===== STEP 5: VIDEO ENHANCEMENT =====
            logger.info("5/5: Enhancing video...")
            try:
                if self.video_enhancer:
                    # Verify current video still exists
                    if not os.path.exists(current_video):
                        logger.error(f"Video file for enhancement not found: {current_video}")
                        self.temp_manager.mark_error()
                        return None
                    
                    # Create enhanced file path using unified temp manager
                    enhanced_file = self.temp_manager.create_video_file("video_enhancement", "mp4", "enhanced")
                    
                    # Prepare enhancement options
                    hashtags = trend_data.popular_hashtags[:8] if trend_data else ["fyp", "viral"]
                    options = {
                        "add_intro": True,
                        "add_hashtags": True,
                        "add_cta": True,
                        "intro_text": "Watch this!",
                        "hashtags": hashtags,
                        "cta_text": "Follow for more!"
                    }
                    
                    enhanced_result = self.video_enhancer.enhance(
                        current_video, str(enhanced_file), options
                    )
                    
                    if enhanced_result and os.path.exists(enhanced_result):
                        current_video = enhanced_result
                        logger.info(f"Video enhanced: {enhanced_result}")
                    else:
                        logger.warning("Video enhancement failed, using unenhanced video")
                        # Keep current_video as is
                else:
                    logger.info("No video enhancer configured, skipping enhancement")
                    
            except Exception as e:
                logger.error(f"Video enhancement error: {e}")
                # Continue with unenhanced video
            
            # ===== FINAL: COPY TO OUTPUT DIRECTORY =====
            try:
                # Verify final video exists
                if not os.path.exists(current_video):
                    logger.error(f"Final video file not found: {current_video}")
                    self.temp_manager.mark_error()
                    return None
                
                # Create final output path
                final_path = os.path.join(self.config["output_dir"], f"final_{timestamp}.mp4")
                
                # Copy to final destination
                import shutil
                shutil.copy2(current_video, final_path)
                
                # Verify final copy
                if not os.path.exists(final_path):
                    logger.error(f"Failed to copy to final destination: {final_path}")
                    return None
                
                file_size_mb = os.path.getsize(final_path) / (1024 * 1024)
                logger.info(f"Final video ready: {final_path} ({file_size_mb:.1f} MB)")

                # ===== SAVE TO DATABASE =====
                try:
                    # Get generator info
                    generator_name = "Unknown"
                    generator_params = {}
                    if hasattr(self.video_generator, 'get_selected_info'):
                        info = self.video_generator.get_selected_info()
                        generator_name = info.get('generator', 'Unknown')
                        generator_params = info.get('params', {})
                    elif hasattr(self.video_generator, '__class__'):
                        generator_name = self.video_generator.__class__.__name__

                    # Get audio info
                    audio_mode = "none"
                    audio_params = {}
                    midi_file = None
                    if self.audio_generator:
                        audio_mode = getattr(self.audio_generator, 'mode', 'unknown')
                        audio_params = {
                            'progressive_build': getattr(self.audio_generator, 'progressive_builder', None) is not None
                        }
                        midi_file = getattr(self.audio_generator, 'selected_midi_path', None)

                    # Get git commit
                    git_commit = self.git.get_current_commit() if self.git else None

                    # Save video record
                    video_record = VideoRecord(
                        generator_name=generator_name,
                        generator_params=generator_params,
                        audio_mode=audio_mode,
                        audio_params=audio_params,
                        video_path=final_path,
                        duration=self.config["video_duration"],
                        fps=self.config["fps"],
                        width=self.config["video_dimensions"][0],
                        height=self.config["video_dimensions"][1],
                        git_commit=git_commit,
                        midi_file=midi_file
                    )

                    self._current_video_id = self.db.save_video(video_record)
                    logger.info(f"Video saved to database with ID: {self._current_video_id}")

                except Exception as e:
                    logger.error(f"Failed to save video to database: {e}")
                    # Continue anyway - don't fail the pipeline for DB errors

                # ===== OPTIONAL: PUBLISHING =====
                if self.config.get("auto_publish", False) and self.publishers:
                    logger.info("Publishing to platforms...")
                    self._publish_video(final_path, trend_data)
                else:
                    logger.info("Auto-publish disabled or no publishers configured")
                
                # ===== SUCCESS STATISTICS =====
                stats = self.temp_manager.get_stats()
                logger.info(f"Pipeline completed successfully!")
                logger.info(f"Temporary files: {stats['total_files']} files, {stats['total_size_mb']:.1f} MB")
                logger.info(f"Final output: {final_path}")
                
                return final_path
                
            except Exception as e:
                logger.error(f"Final output error: {e}")
                self.temp_manager.mark_error()
                return None
            
        except Exception as e:
            logger.error(f"Pipeline execution error: {e}")
            self.temp_manager.mark_error()
            return None
        
        finally:
            # Cleanup is handled automatically by temp_manager
            pass
    
    def _publish_video(self, video_path: str, trend_data):
        """Publish video to configured platforms"""
        for platform, publisher in self.publishers.items():
            try:
                logger.info(f"Publishing to {platform}...")

                # Prepare metadata - use AI-generated caption if available
                if trend_data and trend_data.recommended_settings:
                    content_settings = trend_data.recommended_settings.get("content", {})
                    caption = content_settings.get("ai_caption", "Amazing physics simulation!")
                    hashtags = content_settings.get("ai_hashtags", trend_data.popular_hashtags[:10])
                else:
                    caption = "Amazing physics simulation!"
                    hashtags = ["physics", "simulation", "viral", "fyp"]

                result = publisher.publish(video_path, caption, hashtags)
                if result:
                    logger.info(f"Successfully published to {platform}")

                    # Update database with publication info
                    if self._current_video_id:
                        try:
                            # Extract video ID from result if available
                            platform_video_id = None
                            if isinstance(result, dict):
                                platform_video_id = result.get('video_id') or result.get('id')
                            elif isinstance(result, str):
                                platform_video_id = result

                            self.db.update_video_publication(
                                self._current_video_id,
                                platform,
                                platform_video_id or "unknown"
                            )
                            logger.info(f"Database updated with {platform} publication")
                        except Exception as db_err:
                            logger.error(f"Failed to update DB with publication: {db_err}")
                else:
                    logger.error(f"Failed to publish to {platform}")

            except Exception as e:
                logger.error(f"Publishing error for {platform}: {e}")
    
    def get_database(self) -> VideoDatabase:
        """Get the video database instance."""
        return self.db

    def get_current_video_id(self) -> Optional[int]:
        """Get the ID of the most recently generated video."""
        return self._current_video_id

    def get_context_for_ai(self) -> Dict[str, Any]:
        """Get context data for AI decision making."""
        return self.db.get_context_for_ai()

    def __del__(self):
        """Ensure cleanup on pipeline destruction"""
        if hasattr(self, 'temp_manager'):
            try:
                self.temp_manager.cleanup_all()
            except:
                pass


# ===== UTILITIES =====

def create_simple_pipeline(output_dir: str = "videos", 
                          auto_publish: bool = False,
                          video_duration: int = 60) -> SimplePipeline:
    """
    Create a SimplePipeline with default settings
    
    Args:
        output_dir: Output directory for final videos
        auto_publish: Enable automatic publishing
        video_duration: Video duration in seconds
        
    Returns:
        Configured SimplePipeline instance
    """
    return SimplePipeline(
        output_dir=output_dir,
        auto_publish=auto_publish,
        video_duration=video_duration,
        video_dimensions=[1080, 1920],
        fps=60
    )


if __name__ == "__main__":
    # Test pipeline
    print("Testing SimplePipeline with unified temp management...")
    
    # Setup logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and test pipeline
    pipeline = create_simple_pipeline()
    
    # This would need actual components to test
    print("Pipeline created successfully!")
    print("Temp manager stats:", pipeline.temp_manager.get_stats())