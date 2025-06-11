# src/video_enhancers/base_video_enhancer.py
"""
Base class interface for a video enhancer.

// TODO implement real usage and maybe data format
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IVideoEnhancer(ABC):
    """Interface for video enhancers"""
    
    @abstractmethod
    def enhance(self, video_path: str, output_path: str, options: Dict[str, Any]) -> Optional[str]:
        """
        Enhance a video with visual and textual effects
        
        Args:
            video_path: Path to the video to enhance
            output_path: Path to the output file
            options: Enhancement options
            
        Returns:
            Path to the enhanced video, or None if failed
        """
        pass