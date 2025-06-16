# src/core/plugin_manager.py
import importlib
import inspect
import os
import logging
from pathlib import Path
from typing import List, Type, Dict, Optional

logger = logging.getLogger("TikSimPro")

class PluginManager:
    """
    Manager for plugins.
    Provide a manager to dynamically load and manage all plugins.
    Automatically organizes plugins by their base classes when no base is specified.
    """
    
    def __init__(self, base_dir=None, plugin_dirs=None):
        """
        Init the plugin manager.

        Args:
            base_dir: Base directory for all plugins
            plugin_dirs: List of all plugin directories
        """
        self.plugins = {}  # Structure: {base_class_name: {plugin_name: plugin_class}}
        self.all_plugins = {}  # Cache for all discovered plugins
        self.base_dir = base_dir or "src"

        self.plugin_dirs: List[Path] = [
            Path(p) if Path(p).is_absolute() else Path(self.base_dir) / p
            for p in (plugin_dirs or [])
        ]
        
        for plugin in self.plugin_dirs:
            logger.info(f"Plugin directory to discover: {plugin}")
    
    def register_plugin_dir(self, dir_path: str):
        """
        Add a directory to the plugin_dirs list.
        
        Args:
            dir_path: The new directory
        """
        path = Path(dir_path) if Path(dir_path).is_absolute() else Path(self.base_dir) / dir_path
        if path not in self.plugin_dirs:
            self.plugin_dirs.append(path)
            logger.info(f"Registered new plugin directory: {path}")
    
    def discover_plugins(self, base_class: Optional[Type] = None) -> Dict[str, Type]:
        """
        Discover plugins. If base_class is provided, filter by it.
        If not, discover all and organize by their detected base classes.

        Args:
            base_class: The base class to filter by (optional)
        
        Returns: 
            Dictionary of discovered plugins {plugin_name: plugin_class}
        """
        discovered: Dict[str, Type] = {}
        
        # Going through all directories
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                logger.debug(f"Plugin directory not found: {plugin_dir}")
                continue
                
            try:
                for filename in os.listdir(plugin_dir):
                    if (filename.endswith('.py') and 
                        not filename.startswith('__') and 
                        not filename.startswith('base_')):
                        
                        module_name = filename[:-3]  # Remove .py
                        
                        try:
                            # Import dynamically the module
                            module_path = f"{self._package_name(plugin_dir)}.{module_name}"
                            module = importlib.import_module(module_path)
                            
                            # Search for classes defined in this module
                            for name, obj in inspect.getmembers(module, inspect.isclass):
                                # Skip if the class is defined in another module
                                if obj.__module__ != module_path:
                                    continue
                                
                                # If base_class is specified, filter by it
                                if base_class is not None:
                                    if issubclass(obj, base_class) and obj != base_class:
                                        discovered[name] = obj
                                        logger.info(f"Plugin discovered (filtered by {base_class.__name__}): {name}")
                                else:
                                    # No filter, add all classes and organize by base later
                                    discovered[name] = obj
                                    logger.info(f"Plugin discovered: {name}")
                        
                        except Exception as e:
                            logger.error(f"Error loading plugin module {module_path}: {e}")
                            
            except Exception as e:
                logger.error(f"Error scanning directory {plugin_dir}: {e}")
        
        return discovered
    
    def _organize_by_base_classes(self, plugins: Dict[str, Type]):
        """
        Organize plugins by their base classes automatically.
        
        Args:
            plugins: Dictionary of {plugin_name: plugin_class}
        """
        # Clear existing organization
        self.plugins.clear()
        
        for plugin_name, plugin_class in plugins.items():
            # Find meaningful base classes (skip object and generic bases)
            meaningful_bases = []
            
            for base in plugin_class.__bases__:
                # Skip basic Python classes
                if base.__name__ in ['object', 'ABC']:
                    continue
                    
                # Look for interfaces (classes starting with 'I') or meaningful bases
                if (base.__name__.startswith('I') or 
                    'base' in base.__name__.lower() or
                    'interface' in base.__name__.lower() or
                    hasattr(base, '__abstractmethods__')):
                    meaningful_bases.append(base)
            
            # If no meaningful base found, use the direct parent
            if not meaningful_bases and plugin_class.__bases__:
                meaningful_bases = [plugin_class.__bases__[0]]
            
            # Organize by each meaningful base
            for base in meaningful_bases:
                base_name = base.__name__
                
                if base_name not in self.plugins:
                    self.plugins[base_name] = {}
                
                self.plugins[base_name][plugin_name] = plugin_class
                logger.debug(f"Organized {plugin_name} under base {base_name}")
    
    def _package_name(self, plugin_dir: Path) -> str:
        """
        Convert path to package name.
        Example: /absolute/path/to/src/pipelines → src.pipelines
        """
        parts = plugin_dir.parts
        
        # Find 'src' in the path and use everything from there
        try:
            src_index = parts.index('src')
            return ".".join(parts[src_index:])
        except ValueError:
            # If 'src' not found, use the full path as dots
            return ".".join(parts)

    def get_plugin(self, name: str, base_class: Optional[Type] = None) -> Optional[Type]:
        """
        Get a plugin by name. If base_class is provided, look in that category.
        If not, discover and organize automatically, then search.

        Args:
            name: The name of the plugin class
            base_class: The base class to look under (optional)

        Returns:
            The plugin class or None if not found
        """
        try:
            if base_class is not None:
                # Specific base class requested
                base_name = base_class.__name__
                
                # Check if we have plugins for this base class
                if base_name not in self.plugins:
                    logger.debug(f"Discovering plugins for base class: {base_name}")
                    discovered = self.discover_plugins(base_class)
                    self.plugins[base_name] = discovered
                
                plugin = self.plugins[base_name].get(name)
                if plugin:
                    logger.debug(f"Plugin found in {base_name}: {name}")
                    return plugin
                else:
                    logger.warning(f"Plugin {name} not found in base class {base_name}")
                    available = list(self.plugins[base_name].keys())
                    logger.debug(f"Available in {base_name}: {available}")
                    return None
            
            else:
                # No base class specified - discover all and organize
                if not self.all_plugins:
                    logger.debug("Discovering all plugins and organizing by base classes")
                    self.all_plugins = self.discover_plugins(None)
                    self._organize_by_base_classes(self.all_plugins)
                
                # Search in all organized categories
                for base_name, plugins in self.plugins.items():
                    if name in plugins:
                        logger.debug(f"Plugin found in auto-detected base {base_name}: {name}")
                        return plugins[name]
                
                # If not found in organized categories, check the raw cache
                if name in self.all_plugins:
                    logger.debug(f"Plugin found in raw cache: {name}")
                    return self.all_plugins[name]
                
                logger.warning(f"Plugin {name} not found anywhere")
                self._debug_available_plugins()
                return None
                
        except Exception as e:
            logger.error(f"Error getting plugin {name}: {e}")
            return None
    
    def _debug_available_plugins(self):
        """Debug helper to show available plugins"""
        logger.debug("=== Available Plugins Debug ===")
        for base_name, plugins in self.plugins.items():
            plugin_names = list(plugins.keys())
            logger.debug(f"  {base_name}: {plugin_names}")
        
        if self.all_plugins:
            all_names = list(self.all_plugins.keys())
            logger.debug(f"  Raw cache: {all_names}")
    
    def list_plugins(self, base_class: Optional[Type] = None) -> List[str]:
        """
        List all available plugin names.
        
        Args:
            base_class: Filter by base class (optional)
            
        Returns:
            List of plugin names
        """
        if base_class is not None:
            base_name = base_class.__name__
            if base_name not in self.plugins:
                discovered = self.discover_plugins(base_class)
                self.plugins[base_name] = discovered
            return list(self.plugins[base_name].keys())
        else:
            # Return all plugins from all categories
            if not self.all_plugins:
                self.all_plugins = self.discover_plugins(None)
                self._organize_by_base_classes(self.all_plugins)
            return list(self.all_plugins.keys())
    
    def list_categories(self) -> List[str]:
        """
        List all discovered base class categories.
        
        Returns:
            List of base class names
        """
        if not self.all_plugins:
            self.all_plugins = self.discover_plugins(None)
            self._organize_by_base_classes(self.all_plugins)
        
        return list(self.plugins.keys())
    
    def get_plugins_by_category(self, category: str) -> Dict[str, Type]:
        """
        Get all plugins in a specific category.
        
        Args:
            category: Base class name (category)
            
        Returns:
            Dictionary of plugins in that category
        """
        if not self.all_plugins:
            self.all_plugins = self.discover_plugins(None)
            self._organize_by_base_classes(self.all_plugins)
        
        return self.plugins.get(category, {})
    
    def reload_plugins(self):
        """
        Force reload of all plugins (clears all caches).
        """
        self.plugins.clear()
        self.all_plugins.clear()
        logger.info("Reloaded all plugins")
    
    def get_plugin_info(self, name: str, base_class: Optional[Type] = None) -> Dict:
        """
        Get detailed information about a plugin.
        
        Args:
            name: Plugin name
            base_class: Base class filter (optional)
            
        Returns:
            Dictionary with plugin information
        """
        plugin = self.get_plugin(name, base_class)
        
        if not plugin:
            return {}
        
        # Find which category this plugin belongs to
        category = "unknown"
        for base_name, plugins in self.plugins.items():
            if name in plugins:
                category = base_name
                break
        
        info = {
            "name": name,
            "class": plugin,
            "module": plugin.__module__,
            "category": category,
            "doc": plugin.__doc__,
            "base_classes": [cls.__name__ for cls in plugin.__bases__],
            "methods": [method for method in dir(plugin) if not method.startswith('_')]
        }
        
        return info


# ===== UTILITIES =====

def create_plugin_manager(base_dir: str = "src", 
                         plugin_dirs: List[str] = None) -> PluginManager:
    """
    Create a plugin manager with default settings.
    
    Args:
        base_dir: Base directory
        plugin_dirs: List of plugin directories
        
    Returns:
        Configured PluginManager instance
    """
    default_dirs = [
        "pipelines", "trend_analyzers", "video_generators", 
        "audio_generators", "media_combiners", "video_enhancers", "publishers"
    ]
    
    dirs = plugin_dirs or default_dirs
    return PluginManager(base_dir, dirs)


if __name__ == "__main__":
    # Test du plugin manager
    print("🔌 Test Smart PluginManager")
    
    # Create manager
    manager = create_plugin_manager()
    
    # Test auto-discovery and organization
    print("\n📋 Auto-discovering all plugins...")
    all_plugins = manager.list_plugins()
    print(f"Total plugins found: {len(all_plugins)}")
    
    # Show categories
    categories = manager.list_categories()
    print(f"\n📂 Categories discovered: {categories}")
    
    for category in categories:
        plugins_in_cat = manager.get_plugins_by_category(category)
        print(f"  {category}: {list(plugins_in_cat.keys())}")
    
    # Test getting plugins without specifying base class
    print(f"\n🔍 Testing plugin retrieval without base class...")
    
    # Try to get some common plugins
    test_plugins = ["SimplePipeline", "SimpleTrendAnalyzer", "TrendAudioGenerator"]
    for plugin_name in test_plugins:
        plugin = manager.get_plugin(plugin_name)
        if plugin:
            info = manager.get_plugin_info(plugin_name)
            print(f"  ✅ {plugin_name} found in category: {info['category']}")
        else:
            print(f"  ❌ {plugin_name} not found")