# publishers/base_publisher.py
from abc import ABC, abstractmethod

class BasePublisher(ABC):
    """Interface abstraite pour tous les systèmes de publication"""
    
    @abstractmethod
    def authenticate(self):
        """Authentifie le publisher avec la plateforme"""
        pass
    
    @abstractmethod
    def upload_video(self, video_path, caption, hashtags):
        """Publie une vidéo avec une description et des hashtags"""
        pass