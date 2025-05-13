import json
import os
import logging

logger = logging.getLogger("TikSimPro")

class Config:
    """Gestionnaire de configuration central"""
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erreur lors du chargement de la configuration: {e}")
        
        # Configuration par défaut
        return {
            "simulator": {
                "type": "AdvancedPhysicsSimulation",
                "params": {
                    "width": 1080,
                    "height": 1920,
                    "fps": 60,
                    "duration": 61
                }
            },
            "enhancer": {
                "type": "VideoEnhancer",
                "params": {
                    "add_intro": False,
                    "add_hashtags": False,
                    "add_music": True
                }
            },
            "publisher": {
                "type": "TikTokPublisher",
                "params": {
                    "auto_close": True
                }
            },
            "data_provider": {
                "type": "TikTokScraper",
                "params": {
                    "cache_dir": "tiktok_data"
                }
            },
            "output_dir": "videos",
            "auto_publish": False
        }
    
    def save_config(self):
        """Sauvegarde la configuration dans le fichier"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration sauvegardée dans {self.config_file}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
    
    def get(self, key, default=None):
        """Récupère une valeur de configuration"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set(self, key, value):
        """Définit une valeur de configuration"""
        keys = key.split('.')
        config = self.config
        
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        logger.info(f"Configuration mise à jour: {key} = {value}")