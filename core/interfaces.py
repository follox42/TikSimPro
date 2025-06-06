# core/interfaces.py
"""
Interfaces de base pour le système TikSimPro
Définit les contrats pour tous les composants
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import json

@dataclass
class TrendData:
    """Données de tendances pour la création de contenu"""
    timestamp: float
    date: str
    popular_hashtags: List[str]
    popular_music: List[Dict[str, Any]]
    color_trends: Dict[str, Any]
    timing_trends: Dict[str, Any]
    recommended_settings: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrendData':
        """Crée une instance à partir d'un dictionnaire"""
        return cls(
            timestamp=data.get('timestamp', 0),
            date=data.get('date', ''),
            popular_hashtags=data.get('popular_hashtags', []),
            popular_music=data.get('popular_music', []),
            color_trends=data.get('color_trends', {}),
            timing_trends=data.get('timing_trends', {}),
            recommended_settings=data.get('recommended_settings', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'instance en dictionnaire"""
        return {
            'timestamp': self.timestamp,
            'date': self.date,
            'popular_hashtags': self.popular_hashtags,
            'popular_music': self.popular_music,
            'color_trends': self.color_trends,
            'timing_trends': self.timing_trends,
            'recommended_settings': self.recommended_settings
        }
    
    def to_json(self) -> str:
        """Convertit l'instance en JSON"""
        return json.dumps(self.to_dict())

@dataclass
class AudioEvent:
    """Événement sonore pour la génération audio"""
    event_type: str
    time: float
    position: Optional[Tuple[float, float]] = None
    params: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialise les valeurs par défaut"""
        if self.params is None:
            self.params = {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioEvent':
        """Crée une instance à partir d'un dictionnaire"""
        return cls(
            event_type=data.get('event_type', ''),
            time=data.get('time', 0.0),
            position=data.get('position'),
            params=data.get('params', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'instance en dictionnaire"""
        return {
            'event_type': self.event_type,
            'time': self.time,
            'position': self.position,
            'params': self.params
        }

@dataclass
class VideoMetadata:
    """Métadonnées pour les vidéos générées"""
    width: int
    height: int
    fps: float
    duration: float
    frame_count: int
    file_path: str
    creation_timestamp: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoMetadata':
        """Crée une instance à partir d'un dictionnaire"""
        return cls(
            width=data.get('width', 0),
            height=data.get('height', 0),
            fps=data.get('fps', 0.0),
            duration=data.get('duration', 0.0),
            frame_count=data.get('frame_count', 0),
            file_path=data.get('file_path', ''),
            creation_timestamp=data.get('creation_timestamp', 0.0)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'instance en dictionnaire"""
        return {
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'duration': self.duration,
            'frame_count': self.frame_count,
            'file_path': self.file_path,
            'creation_timestamp': self.creation_timestamp
        }

class ITrendAnalyzer(ABC):
    """Interface pour les analyseurs de tendances"""
    
    @abstractmethod
    def get_trending_hashtags(self, limit: int = 30) -> List[str]:
        """
        Récupère les hashtags tendance
        
        Args:
            limit: Nombre maximum de hashtags à récupérer
            
        Returns:
            Liste de hashtags tendance
        """
        pass
    
    @abstractmethod
    def get_popular_music(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Récupère les musiques populaires
        
        Args:
            limit: Nombre maximum de musiques à récupérer
            
        Returns:
            Liste de musiques populaires avec métadonnées
        """
        pass
    
    @abstractmethod
    def get_trend_analysis(self) -> TrendData:
        """
        Analyse les tendances actuelles
        
        Returns:
            Données de tendances complètes
        """
        pass

class IVideoGenerator(ABC):
    """Interface pour les générateurs de vidéo"""
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure le générateur avec des paramètres spécifiques
        
        Args:
            config: Paramètres de configuration
            
        Returns:
            True si la configuration a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def set_output_path(self, path: str) -> None:
        """
        Définit le chemin de sortie pour la vidéo
        
        Args:
            path: Chemin du fichier de sortie
        """
        pass
    
    @abstractmethod
    def apply_trend_data(self, trend_data: TrendData) -> None:
        """
        Applique les données de tendances au générateur
        
        Args:
            trend_data: Données de tendances à appliquer
        """
        pass
    
    @abstractmethod
    def generate(self) -> Optional[str]:
        """
        Génère la vidéo
        
        Returns:
            Chemin de la vidéo générée, ou None en cas d'échec
        """
        pass
    
    @abstractmethod
    def get_audio_events(self) -> List[AudioEvent]:
        """
        Récupère les événements audio générés pendant la simulation
        
        Returns:
            Liste des événements audio
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> VideoMetadata:
        """
        Récupère les métadonnées de la vidéo générée
        
        Returns:
            Métadonnées de la vidéo
        """
        pass

class IAudioGenerator(ABC):
    """Interface pour les générateurs audio"""
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure le générateur avec des paramètres spécifiques
        
        Args:
            config: Paramètres de configuration
            
        Returns:
            True si la configuration a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def set_output_path(self, path: str) -> None:
        """
        Définit le chemin de sortie pour l'audio
        
        Args:
            path: Chemin du fichier de sortie
        """
        pass
    
    @abstractmethod
    def set_duration(self, duration: float) -> None:
        """
        Définit la durée de l'audio
        
        Args:
            duration: Durée en secondes
        """
        pass
    
    @abstractmethod
    def apply_trend_data(self, trend_data: TrendData) -> None:
        """
        Applique les données de tendances au générateur
        
        Args:
            trend_data: Données de tendances à appliquer
        """
        pass
    
    @abstractmethod
    def add_events(self, events: List[AudioEvent]) -> None:
        """
        Ajoute des événements audio à la timeline
        
        Args:
            events: Liste d'événements audio
        """
        pass
    
    @abstractmethod
    def generate(self) -> Optional[str]:
        """
        Génère la piste audio
        
        Returns:
            Chemin de la piste audio générée, ou None en cas d'échec
        """
        pass

class IMediaCombiner(ABC):
    """Interface pour les combineurs de médias (audio + vidéo)"""
    
    @abstractmethod
    def combine(self, video_path: str, audio_path: str, output_path: str) -> Optional[str]:
        """
        Combine une vidéo et une piste audio
        
        Args:
            video_path: Chemin de la vidéo
            audio_path: Chemin de la piste audio
            output_path: Chemin du fichier de sortie
            
        Returns:
            Chemin du fichier combiné, ou None en cas d'échec
        """
        pass

class IVideoEnhancer(ABC):
    """Interface pour les améliorateurs de vidéo"""
    
    @abstractmethod
    def enhance(self, video_path: str, output_path: str, options: Dict[str, Any]) -> Optional[str]:
        """
        Améliore une vidéo avec des effets visuels et textuels
        
        Args:
            video_path: Chemin de la vidéo à améliorer
            output_path: Chemin du fichier de sortie
            options: Options d'amélioration
            
        Returns:
            Chemin de la vidéo améliorée, ou None en cas d'échec
        """
        pass

class IContentPublisher(ABC):
    """Interface pour les systèmes de publication"""
    @abstractmethod
    def publish(self, video_path: str, caption: str, hashtags: List[str], **kwargs) -> bool:
        """
        Publie une vidéo
        
        Args:
            video_path: Chemin de la vidéo à publier
            caption: Légende de la vidéo
            hashtags: Liste de hashtags à utiliser
            kwargs: Paramètres supplémentaires spécifiques à la plateforme
            
        Returns:
            True si la publication a réussi, False sinon
        """
        pass

class IPipeline(ABC):
    """Interface pour un pipeline de traitement complet"""
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure le pipeline avec des paramètres spécifiques
        
        Args:
            config: Paramètres de configuration
            
        Returns:
            True si la configuration a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def execute(self) -> Optional[str]:
        """
        Exécute le pipeline complet
        
        Returns:
            Chemin du résultat final, ou None en cas d'échec
        """
        pass