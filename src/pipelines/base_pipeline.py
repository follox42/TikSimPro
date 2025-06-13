# src/pipelines/base_pipeline.py
"""
Base class interface for a pipeline.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IPipeline(ABC):
    """Interface for a complete processing pipeline"""
    
    def __init__(self):
        # Components
        self.trend_analyzer = None
        self.video_generator = None
        self.audio_generator = None
        self.media_combiner = None
        self.video_enhancer = None
        self.publishers = {}

    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure the pipeline with specific parameters
        
        Args:
            config: Configuration parameters
            
        Returns:
            True if configuration succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self) -> Optional[str]:
        """
        Execute the complete pipeline
        
        Returns:
            Path to the final result, or None if failed
        """
        pass

    # -------------------------
    # Basic setters for compatibilities
    # -------------------------
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