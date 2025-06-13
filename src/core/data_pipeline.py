# src/core/data_pipeline.py
"""
Interfaces de base pour le système TikSimPro
Définit les contrats pour tous les composants
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import json
import time

@dataclass
class TrendData:
    """
    Comprehensive trend data for viral content creation
    
    Contains all trending information needed to create viral TikTok videos:
    - Popular hashtags currently trending
    - Trending music and audio tracks
    - Color palettes that are performing well
    - Optimal timing strategies for engagement
    - AI-recommended settings for maximum viral potential
    """
    
    # Metadata
    timestamp: float                        # Unix timestamp when analysis was performed
    date: str                              # Human-readable date (YYYY-MM-DD)
    
    # Content trends
    popular_hashtags: List[str]            # Trending hashtags: ["fyp", "viral", "trending", ...]
    popular_music: List[Dict[str, Any]]    # Music data: [{"title": "Song", "artist": "Artist", "bpm": 120, ...}, ...]
    
    # Visual trends
    color_trends: Dict[str, Any]           # Color data: {"primary_colors": ["#FF0050", ...], "palettes": {...}}

    # AI recommendations
    recommended_settings: Dict[str, Any]   # Complete optimized settings for all generators
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrendData':
        """
        Create TrendData instance from dictionary
        
        Args:
            data: Dictionary containing trend data
            
        Returns:
            TrendData instance with validated data
        """
        return cls(
            timestamp=data.get('timestamp', time.time()),
            date=data.get('date', ''),
            popular_hashtags=data.get('popular_hashtags', []),
            popular_music=data.get('popular_music', []),
            color_trends=data.get('color_trends', {}),
            recommended_settings=data.get('recommended_settings', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert instance to dictionary for storage/transmission
        
        Returns:
            Dictionary representation of trend data
        """
        return {
            'timestamp': self.timestamp,
            'date': self.date,
            'popular_hashtags': self.popular_hashtags,
            'popular_music': self.popular_music,
            'color_trends': self.color_trends,
            'recommended_settings': self.recommended_settings
        }
    
    def to_json(self) -> str:
        """
        Convert instance to JSON string
        
        Returns:
            JSON string representation of trend data
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def is_fresh(self, max_age_hours: int = 24) -> bool:
        """
        Check if trend data is still fresh/valid
        
        Args:
            max_age_hours: Maximum age in hours before data is considered stale
            
        Returns:
            True if data is fresh, False if stale
        """
        current_time = time.time()
        age_seconds = current_time - self.timestamp
        age_hours = age_seconds / 3600
        return age_hours <= max_age_hours
    
    def get_top_hashtags(self, count: int = 10) -> List[str]:
        """
        Get top N hashtags from trend data
        
        Args:
            count: Number of hashtags to return
            
        Returns:
            List of top hashtags (most trending first)
        """
        return self.popular_hashtags[:count]
    
    def get_recommended_colors(self) -> List[str]:
        """
        Get recommended color palette for video generation
        
        Returns:
            List of hex color codes
        """
        if 'primary_colors' in self.color_trends:
            return self.color_trends['primary_colors']
        elif 'recommended_palette' in self.color_trends:
            return self.color_trends['recommended_palette']
        else:
            # Fallback to TikTok default colors
            return ["#FF0050", "#00F2EA", "#FFFFFF", "#FE2C55", "#25F4EE"]
        
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