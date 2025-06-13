# src/trend_analyzers/base_trend_analyzer.py
"""
Base class interface for all trend analyzers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from src.core.data_pipeline import TrendData

class ITrendAnalyzer(ABC):
    """
    Abstract base class for all trend analyzers
    
    Defines the interface that all trend analysis implementations must follow.
    This ensures consistent data flow and compatibility across the pipeline.
    """
    
    @abstractmethod
    def get_trending_hashtags(self, limit: int = 30) -> List[str]:
        """
        Retrieve currently trending hashtags
        
        Args:
            limit: Maximum number of hashtags to retrieve
            
        Returns:
            List of trending hashtags (without # prefix)
            
        Example:
            ["fyp", "viral", "trending", "satisfying", "simulation"]
        """
        pass
    
    @abstractmethod
    def get_popular_music(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieve popular music tracks and audio
        
        Args:
            limit: Maximum number of music tracks to retrieve
            
        Returns:
            List of music data with metadata
            
        Example:
            [
                {
                    "title": "Levitating",
                    "artist": "Dua Lipa"
                }
            ]
        """
        pass
    
    @abstractmethod
    def get_trend_analysis(self) -> TrendData:
        """
        Perform comprehensive trend analysis
        
        This is the main method that combines all trend data into a single,
        actionable dataset for the content generation pipeline.
        
        Returns:
            Complete TrendData with all trending information
            
        Raises:
            TrendAnalysisError: If analysis fails or data is unavailable
        """
        pass
    
    # Optional methods that can be overridden for enhanced functionality
    
    def get_color_trends(self) -> Dict[str, Any]:
        """
        Get color trends and palettes (optional override)
        
        Returns:
            Dictionary containing color trend data
        """
        return {
            "primary_colors": ["#FF0050", "#00F2EA", "#FFFFFF", "#FE2C55", "#25F4EE"],
            "style": "vibrant",
            "trending_palettes": {}
        }
    
    def get_timing_trends(self) -> Dict[str, Any]:
        """
        Get optimal timing strategies (optional override)
        
        Returns:
            Dictionary containing timing recommendations
        """
        return {
            "optimal_duration": 30,
            "trending_duration": 15,
            "best_fps": 60,
            "peak_engagement_time": 3.5,
            "hook_duration": 2.0,
            "resolution": [1080, 1920]
        }
    
    def validate_trend_data(self, trend_data: TrendData) -> bool:
        """
        Validate trend data quality and completeness
        
        Args:
            trend_data: TrendData instance to validate
            
        Returns:
            True if data is valid and complete
        """
        required_fields = [
            trend_data.popular_hashtags,
            trend_data.popular_music,
            trend_data.color_trends
        ]
        
        # Check that all required fields have data
        return all(field for field in required_fields)
    
    def get_cache_key(self) -> str:
        """
        Generate cache key for trend data storage
        
        Returns:
            Unique cache key based on current date and analyzer type
        """
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        analyzer_name = self.__class__.__name__
        return f"trends_{analyzer_name}_{date_str}"