from abc import ABC, abstractmethod

class BaseSimulator(ABC):
    """Interface abstraite que tous les simulateurs doivent implémenter"""
    
    @abstractmethod
    def setup(self, config):
        """Configure le simulateur avec les paramètres spécifiés"""
        pass
    
    @abstractmethod
    def run_simulation(self):
        """Exécute la simulation et retourne True en cas de succès"""
        pass
    
    @abstractmethod
    def generate_video(self):
        """Génère une vidéo à partir des frames et des sons"""
        pass
    
    @abstractmethod
    def get_output_path(self):
        """Retourne le chemin de la vidéo générée"""
        pass
    