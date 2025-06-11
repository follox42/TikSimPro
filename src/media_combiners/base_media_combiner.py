# src/media_combiner/base_media_combiner.py
"""
Base class interface for a combiner.
"""

from abc import ABC, abstractmethod
from typing import Optional


class IMediaCombiner(ABC):
    """Interface for media combiners (audio + video)"""
    
    @abstractmethod
    def combine(self, video_path: str, audio_path: str, output_path: str) -> Optional[str]:
        """
        Combine a video and an audio track
        
        Args:
            video_path: Path to the video file
            audio_path: Path to the audio track
            output_path: Path to the output file
            
        Returns:
            Path to the combined file, or None if failed
        """
        pass