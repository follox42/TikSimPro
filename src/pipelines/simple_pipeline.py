# src/pipelines/simple_pipeline.py
"""
Simple pipeline for TikSimPro
Minimalist version without complexity
"""

import os
import time
import logging
from typing import Dict, Any, Optional
import random

from .base_pipeline import IPipeline

logger = logging.getLogger("TikSimPro")

class SimplePipeline(IPipeline):
    """Simple and direct pipeline"""
    
    def __init__(self):
        # Default config
        self.config = {
            "output_dir": "output",
            "auto_publish": False,
            "video_duration": 30,
            "video_dimensions": [1080, 1920],
            "fps": 60
        }
        
        # Components
        self.trend_analyzer = None
        self.video_generator = None
        self.audio_generator = None
        self.media_combiner = None
        self.video_enhancer = None
        self.publishers = {}
        
        # Create output directory
        os.makedirs(self.config["output_dir"], exist_ok=True)
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the pipeline"""
        self.config.update(config)
        os.makedirs(self.config["output_dir"], exist_ok=True)
        return True
    
    def set_trend_analyzer(self, analyzer):
        self.trend_analyzer = analyzer
    
    def set_video_generator(self, generator):
        self.video_generator = generator
    
    def set_audio_generator(self, generator):
        self.audio_generator = generator
    
    def set_media_combiner(self, combiner):
        self.media_combiner = combiner
    
    def set_video_enhancer(self, enhancer):
        self.video_enhancer = enhancer
    
    def add_publisher(self, platform: str, publisher):
        self.publishers[platform] = publisher
    
    def execute(self) -> Optional[str]:
        """Execute the simple pipeline"""
        try:
            timestamp = int(time.time())
            
            # 1. Analyze trends
            logger.info("1/5: Analyzing trends...")
            if not self.trend_analyzer:
                logger.error("No trend analyzer")
                return None
            
            trend_data = self.trend_analyzer.get_trend_analysis()
            if not trend_data:
                logger.error("Trend analysis failed")
                return None
            
            # 2. Generate video
            logger.info("2/5: Generating video...")
            if not self.video_generator:
                logger.error("No video generator")
                return None
            
            video_path = os.path.join(self.config["output_dir"], f"video_{timestamp}.mp4")
            
            # Configure and generate
            self.video_generator.set_output_path(video_path)
            self.video_generator.apply_trend_data(trend_data)
            
            result_video = self.video_generator.generate()
            if not result_video:
                logger.error("Video generation failed")
                return None
            
            # 3. Audio (optional)
            current_video = result_video
            if self.audio_generator:
                logger.info("3/5: Generating audio...")
                audio_path = os.path.join(self.config["output_dir"], f"audio_{timestamp}.wav")
                
                self.audio_generator.set_output_path(audio_path)
                self.audio_generator.set_duration(self.config["video_duration"])
                self.audio_generator.apply_trend_data(trend_data)
                self.audio_generator.add_events(self.video_generator.get_audio_events())
                
                audio_result = self.audio_generator.generate()
                
                # 4. Combine (if audio generated)
                if audio_result and self.media_combiner:
                    logger.info("4/5: Combining media...")
                    combined_path = os.path.join(self.config["output_dir"], f"combined_{timestamp}.mp4")
                    
                    combined_result = self.media_combiner.combine(result_video, audio_result, combined_path)
                    if combined_result:
                        current_video = combined_result
            else:
                logger.info("3/5: Audio disabled, skipping to next step")
                logger.info("4/5: Media combination not needed")
            
            # 5. Enhancement (optional)
            if self.video_enhancer:
                logger.info("5/5: Enhancing video...")
                final_path = os.path.join(self.config["output_dir"], f"final_{timestamp}.mp4")
                
                hashtags = trend_data.popular_hashtags[:8] if trend_data else ["fyp", "viral"]
                
                options = {
                    "add_intro": True,
                    "add_hashtags": True,
                    "add_cta": True,
                    "intro_text": "Watch this! 👀",
                    "hashtags": hashtags,
                    "cta_text": "Follow for more! 👆"
                }
                
                enhanced_result = self.video_enhancer.enhance(current_video, final_path, options)
                if enhanced_result:
                    current_video = enhanced_result
            else:
                logger.info("5/5: Enhancement disabled")
            
            # Publishing (optional)
            if self.config.get("auto_publish", False) and self.publishers:
                logger.info("Publishing...")
                self._simple_publish(current_video, trend_data)
            
            logger.info(f"✅ Pipeline completed: {current_video}")
            return current_video
            
        except Exception as e:
            logger.error(f"❌ Pipeline error: {e}")
            return None
    
    def _simple_publish(self, video_path: str, trend_data):
        """Simple publishing"""
        captions = [
            "This is so satisfying!",
            "Watch till the end!",
            "Amazing simulation!",
            "Turn on the sound!"
        ]
        
        caption = random.choice(captions)
        hashtags = trend_data.popular_hashtags[:10] if trend_data else ["fyp", "viral", "satisfying"]
        
        for platform, publisher in self.publishers.items():
            try:
                logger.info(f"Publishing to {platform}...")
                success = publisher.publish(video_path, caption, hashtags)
                logger.info(f"{platform}: {'✅' if success else '❌'}")
            except Exception as e:
                logger.error(f"Error publishing to {platform}: {e}")