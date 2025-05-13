# enhancers/base_enhancer.py
from abc import ABC, abstractmethod

class BaseEnhancer(ABC):
    """Interface abstraite pour tous les enhancers de vidéo"""
    
    @abstractmethod
    def enhance_video(self, video_path, output_path, options):
        """Améliore une vidéo avec plusieurs effets"""
        pass