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
            "trend_analyzer": {
            "name": "TikTokAnalyzer",
            "params": {
                "cache_dir": "tiktok_data"
            }
            },
            "video_generator": {
            "name": "CircleSimulator",
            "params": {
                "width": 1080,
                "height": 1920,
                "fps": 60,
                "duration": 30.0,
                "output_path": "output/circle_video.mp4",
                "temp_dir": "temp",
                "frames_dir": "frames",
        
                "min_radius": 100,
                "gap_radius": 0,
                "nb_rings": 50,
                "thickness": 15,
                "gap_angle": 60,
                "rotation_speed": 60,
                
                "color_palette": [
                    "#FF0050",
                    "#00F2EA", 
                    "#FFFFFF", 
                    "#FE2C55",
                    "#25F4EE"
                ]
            }
            },
            "audio_generator": {
            "name": "TrendAudioGenerator",
            "params": {
                "add_effects": False
            }
            },
            "media_combiner": {
            "name": "FFmpegMediaCombiner"
            },
            "video_enhancer": {
            "name": "VideoEnhancer",
            "params": {
                "add_intro": True,
                "add_hashtags": True,
                "add_music": True
            }
            },
            "publishers": {
            "tiktok": {
                "name": "TikTokPublisher",
                "params": {
                "auto_close": True
                },
                "enabled": True
            },
            "youtube": {
                "name": "YouTubePublisher",
                "params": {
                "auto_close": True
                },
                "enabled": False
            },
            "instagram": {
                "name": "InstagramPublisher",
                "params": {
                "auto_close": True,
                "mobile_emulation": True
                },
                "enabled": False
            }
            },
            "pipeline": {
            "output_dir": "videos",
            "auto_publish": False,
            "video_duration": 30,
            "video_dimensions": [1080, 1920],
            "fps": 60
            }
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