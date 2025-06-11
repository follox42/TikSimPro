import importlib
import inspect
import os
import logging

logger = logging.getLogger("TikSimPro")

class PluginManager:
    """Gestionnaire de plugins pour charger dynamiquement des modules"""
    
    def __init__(self, plugin_dirs=None):
        self.plugins = {}
        self.plugin_dirs = plugin_dirs or []
    
    def register_plugin_dir(self, dir_path):
        """Ajoute un répertoire de plugins à scanner"""
        if dir_path not in self.plugin_dirs:
            self.plugin_dirs.append(dir_path)
    
    def discover_plugins(self, base_class):
        """Découvre tous les plugins qui héritent de la classe de base"""
        discovered = {}
        
        # Parcourir les dossiers de plugins
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue
                
            for filename in os.listdir(plugin_dir):
                if filename.endswith('.py') and not filename.startswith('__'):
                    module_name = filename[:-3]  # Enlever l'extension .py
                    
                    try:
                        # Importer dynamiquement le module
                        module_path = f"{os.path.basename(plugin_dir)}.{module_name}"
                        module = importlib.import_module(module_path)
                        
                        # Chercher les classes qui héritent de base_class
                        for name, obj in inspect.getmembers(module):
                            if (inspect.isclass(obj) and 
                                issubclass(obj, base_class) and 
                                obj != base_class):
                                discovered[name] = obj
                                logger.info(f"Plugin découvert: {name}")
                    
                    except Exception as e:
                        logger.error(f"Erreur lors du chargement du plugin {module_name}: {e}")
        
        return discovered
    
    def get_plugin(self, name, base_class):
        """Récupère un plugin spécifique par son nom"""
        if not self.plugins.get(base_class.__name__):
            self.plugins[base_class.__name__] = self.discover_plugins(base_class)
            
        return self.plugins[base_class.__name__].get(name)