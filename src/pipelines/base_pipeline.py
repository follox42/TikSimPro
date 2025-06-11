# src/pipelines/base_pipeline.py
"""
Base class interface for a pipeline.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IPipeline(ABC):
    """Interface for a complete processing pipeline"""
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure the pipeline with specific parameters
        
        Args:
            config: Configuration parameters
            
        Returns:
            True if configuration succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self) -> Optional[str]:
        """
        Execute the complete pipeline
        
        Returns:
            Path to the final result, or None if failed
        """
        pass