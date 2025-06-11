# src/video_generators/base_video_generator.py
"""
Base class interface for all video generators.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.core.format_data import TrendData, AudioEvent, VideoMetadata

class IVideoGenerator(ABC):
    """Interface for video generators"""
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure the generator with specific parameters
        
        Args:
            config: Configuration parameters
            
        Returns:
            True if configuration succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def set_output_path(self, path: str) -> None:
        """
        Set the output path for the video
        
        Args:
            path: Output file path
        """
        pass
    
    @abstractmethod
    def apply_trend_data(self, trend_data: TrendData) -> None:
        """
        Apply trend data to the generator
        
        Args:
            trend_data: Trend data to apply
        """
        pass
    
    @abstractmethod
    def generate(self) -> Optional[str]:
        """
        Generate the video
        
        Returns:
            Path to the generated video, or None if failed
        """
        pass
    
    @abstractmethod
    def get_audio_events(self) -> List[AudioEvent]:
        """
        Retrieve audio events generated during simulation
        
        Returns:
            List of audio events
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> VideoMetadata:
        """
        Retrieve metadata of the generated video
        
        Returns:
            Video metadata
        """
        pass