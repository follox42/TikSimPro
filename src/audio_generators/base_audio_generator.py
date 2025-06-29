# src/audio_generators/base_audio_generator.py
"""
Base class interface for all audio generators.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import os

from src.core.data_pipeline import TrendData, AudioEvent

class IAudioGenerator(ABC):
    """Interface for audio generators"""
    
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
        Set the output path for the audio
        
        Args:
            path: Output file path
        """
        pass
    
    @abstractmethod
    def set_duration(self, duration: float) -> None:
        """
        Set the audio duration
        
        Args:
            duration: Duration in seconds
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
    def add_events(self, events: List[AudioEvent]) -> None:
        """
        Add audio events to the timeline
        
        Args:
            events: List of audio events
        """
        pass
    
    @abstractmethod
    def generate(self) -> Optional[str]:
        """
        Generate the audio track
        
        Returns:
            Path to the generated audio track, or None if failed
        """
        pass

    def set_output_path(self, path: str) -> None:
        self.output_path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
    
    def set_duration(self, duration: float) -> None:
        self.duration = duration