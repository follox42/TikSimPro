# src/publishers/base_publisher.py
"""
Base class interface for all publisher.
"""

from abc import ABC, abstractmethod
from typing import List


class IPublisher(ABC):
    """Interface for publishing systems"""
    
    @abstractmethod
    def publish(self, video_path: str, caption: str, hashtags: List[str], **kwargs) -> bool:
        """
        Publish a video
        
        Args:
            video_path: Path to the video to publish
            caption: Video caption
            hashtags: List of hashtags to use
            kwargs: Additional platform-specific parameters
            
        Returns:
            True if publication succeeded, False otherwise
        """
        pass