# src/pipelines/simple_pipeline.py
import os
import time
import logging
from typing import Dict, Any, Optional

from .base_pipeline import IPipeline
from src.utils.temp_file_manager import TempFileManager, temp_pipeline_step

logger = logging.getLogger("TikSimPro")

class SimplePipeline(IPipeline):
    """Simple pipeline with temporary file management"""
    
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
        
        # Temporary file manager
        self.temp_manager = TempFileManager(
            base_temp_dir="temp",
            auto_cleanup=True,
            keep_on_error=True,  # Keep for debugging
            max_age_hours=24
        )
        
        os.makedirs(self.config["output_dir"], exist_ok=True)
    
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
        """Execute pipeline with temporary file management"""
        try:
            timestamp = int(time.time())
            
            # 1. TREND ANALYSIS
            logger.info("1/5: Analyzing trends...")
            with temp_pipeline_step("trend_analysis") as (temp_mgr, step_dir):
                if not self.trend_analyzer:
                    logger.error("No trend analyzer")
                    return None
                
                trend_data = self.trend_analyzer.get_trend_analysis()
                if not trend_data:
                    logger.error("Trend analysis failed")
                    return None
                
                # Save trend data
                trend_file = temp_mgr.create_temp_file("trend_analysis", "trends", "json")
                trend_file.write_text(trend_data.to_json())
                logger.debug(f"Trends saved: {trend_file}")
            
            # 2. VIDEO GENERATION
            logger.info("2/5: Generating video...")
            with temp_pipeline_step("video_generation") as (temp_mgr, step_dir):
                if not self.video_generator:
                    logger.error("No video generator")
                    return None
                
                # Temporary video file
                video_temp = temp_mgr.create_video_file("video_generation", "mp4", "raw")
                
                # Configuration and generation
                self.video_generator.set_output_path(str(video_temp))
                self.video_generator.apply_trend_data(trend_data)
                
                result_video = self.video_generator.generate()
                if not result_video:
                    logger.error("Video generation failed")
                    self.temp_manager.mark_error()
                    return None
                
                logger.info(f"Raw video generated: {result_video}")
            
            current_video = result_video
            
            # 3. AUDIO GENERATION
            logger.info("3/5: Generating audio...")
            audio_result = None
            if self.audio_generator:
                with temp_pipeline_step("audio_generation") as (temp_mgr, step_dir):
                    # Temporary audio file
                    audio_temp = temp_mgr.create_audio_file("audio_generation", "wav")
                    
                    self.audio_generator.set_output_path(str(audio_temp))
                    self.audio_generator.set_duration(self.config["video_duration"])
                    self.audio_generator.apply_trend_data(trend_data)
                    self.audio_generator.add_events(self.video_generator.get_audio_events())
                    
                    audio_result = self.audio_generator.generate()
                    if audio_result:
                        logger.info(f"Audio generated: {audio_result}")
            
            # 4. MEDIA COMBINATION
            if audio_result and self.media_combiner:
                logger.info("4/5: Combining media...")
                with temp_pipeline_step("media_combination") as (temp_mgr, step_dir):
                    # Temporary combined file
                    combined_temp = temp_mgr.create_video_file("media_combination", "mp4", "combined")
                    
                    combined_result = self.media_combiner.combine(
                        current_video, audio_result, str(combined_temp)
                    )
                    if combined_result:
                        current_video = combined_result
                        logger.info(f"Media combined: {combined_result}")
            else:
                logger.info("4/5: Skipping media combination")
            
            # 5. VIDEO ENHANCEMENT
            if self.video_enhancer:
                logger.info("5/5: Enhancing video...")
                with temp_pipeline_step("video_enhancement") as (temp_mgr, step_dir):
                    # Temporary final file
                    enhanced_temp = temp_mgr.create_video_file("video_enhancement", "mp4", "enhanced")
                    
                    hashtags = trend_data.popular_hashtags[:8] if trend_data else ["fyp", "viral"]
                    
                    options = {
                        "add_intro": True,
                        "add_hashtags": True,
                        "add_cta": True,
                        "intro_text": "Watch this! 👀",
                        "hashtags": hashtags,
                        "cta_text": "Follow for more! 👆"
                    }
                    
                    enhanced_result = self.video_enhancer.enhance(
                        current_video, str(enhanced_temp), options
                    )
                    if enhanced_result:
                        current_video = enhanced_result
                        logger.info(f"Video enhanced: {enhanced_result}")
            else:
                logger.info("5/5: Skipping video enhancement")
            
            # COPY TO FINAL DESTINATION
            final_path = os.path.join(self.config["output_dir"], f"final_{timestamp}.mp4")
            if current_video != final_path:
                import shutil
                shutil.copy2(current_video, final_path)
                logger.info(f"Final video: {final_path}")
            
            # PUBLISHING (optional)
            if self.config.get("auto_publish", False) and self.publishers:
                logger.info("Publishing...")
                self._simple_publish(final_path, trend_data)
            
            # FINAL STATISTICS
            stats = self.temp_manager.get_stats()
            logger.info(f" Temporary files: {stats['total_files']} files, {stats['total_size_mb']:.1f} MB")
            
            logger.info(f" Pipeline completed: {final_path}")
            return final_path
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            self.temp_manager.mark_error()
            return None
        finally:
            # Automatic cleanup managed by TempFileManager
            pass
    
    def _simple_publish(self, video_path: str, trend_data):
        """Simple publishing logic"""
        for platform, publisher in self.publishers.items():
            try:
                logger.info(f"Publishing to {platform}...")
                
                # Prepare metadata
                metadata = {
                    "title": "Amazing Physics Simulation! 🤯",
                    "description": f"Check out this viral physics simulation! #{' #'.join(trend_data.popular_hashtags[:5]) if trend_data else 'physics #viral #fyp'}",
                    "tags": trend_data.popular_hashtags[:10] if trend_data else ["physics", "simulation", "viral", "fyp"]
                }
                
                result = publisher.publish(video_path, metadata)
                if result:
                    logger.info(f"✅ Published to {platform}: {result}")
                else:
                    logger.error(f" Failed to publish to {platform}")
                    
            except Exception as e:
                logger.error(f" Publishing error for {platform}: {e}")
    
    def __del__(self):
        """Final cleanup"""
        if hasattr(self, 'temp_manager'):
            self.temp_manager.cleanup_all()