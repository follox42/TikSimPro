# data_providers/base_provider.py
from abc import ABC, abstractmethod

class BaseDataProvider(ABC):
    """Interface abstraite pour tous les fournisseurs de données"""
    
    @abstractmethod
    def get_trending_hashtags(self, limit=30, refresh=False):
        """Récupère les hashtags tendance"""
        pass
    
    @abstractmethod
    def get_popular_music(self, limit=20, refresh=False):
        """Récupère les musiques populaires"""
        pass
    
    @abstractmethod
    def get_trend_analysis(self, refresh=False):
        """Analyse les tendances actuelles"""
        pass