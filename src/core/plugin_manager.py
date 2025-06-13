import importlib
import inspect
import os
import logging
from pathlib import Path
from typing import List, Type, Dict

logger = logging.getLogger("TikSimPro")

class PluginManager:
    """
    Manager for plugins.
    Provide a manger to dynamicaly load and manage all plugins.
    """
    
    def __init__(self, base_dir=None, plugin_dirs=None):
        """
        Init the plugin manager.

        Args:
            base_dir: Base file for all plugin
            plugin_dirs: List for all plugins dirs
        """
        self.plugins = {}
        self.base_dir = base_dir

        self.plugin_dirs: List[Path] = [
            # If the path is already absolute, keep it; otherwise prepend base_dir
            Path(p) if Path(p).is_absolute() else Path(self.base_dir) / p
            for p in (plugin_dirs or [])
        ]
        for plugin in self.plugin_dirs:
            logger.info(f"File to discover: {plugin}")
    
    def register_plugin_dir(self, dir_path: str):
        """
        Add a directory to the plugin_dirs list.
        
        Args:
            dir_path: The new directory

        Returns:
            Empty
        """
        if dir_path not in self.plugin_dirs:
            self.plugin_dirs.append(dir_path)
    
    def discover_plugins(self, base_class: Type):
        """
        Discover all the classes taht inherit from a base_class.

        Args:
            base_class: The base class
        
        Retruns: 
            All the classes that inherit from the base class
        """
        discovered: Dict[str, Type] = {}
        
        # Going through all directories
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue
                
            for filename in os.listdir(plugin_dir):
                if filename.endswith('.py') and not filename.startswith('__') and not filename.startswith('base_'):
                    module_name = filename[:-3]  # Remove .py
                    
                    try:
                        # Importer dynamiquement le module
                        module_path =  f"{self._package_name(plugin_dir)}.{module_name}"
                        module = importlib.import_module(module_path)
                        
                        # Chercher les classes qui héritent de base_class
                        for name, obj in inspect.getmembers(module):
                            if (inspect.isclass(obj) and 
                                issubclass(obj, base_class) and 
                                obj != base_class):
                                discovered[name] = obj
                                logger.info(f"Plugin discover: {module_path}")
                    
                    except Exception as e:
                        logger.error(f"Error loading plugin {module_path}: {e}")
        
        return discovered
    
    def _package_name(self, plugin_dir: Path) -> str:
        """
        Convert ``/absolute/path/to/src/pipelines`` → ``src.pipelines``.
        """
        parts = plugin_dir.parts

        return ".".join(parts)

    def get_plugin(self, name, base_class):
        """
        Get a plugin with his name.

        Args:
            name: The name of the class
            base_class: The class of the plugin

        Returns:
            The plugin
        """
        if not self.plugins.get(base_class.__name__):
            self.plugins[base_class.__name__] = self.discover_plugins(base_class)
            
        return self.plugins[base_class.__name__].get(name)