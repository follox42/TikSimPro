# src/docker/docker_config.py
"""
Extension Docker pour TikSimPro
Gère la configuration basée sur les variables d'environnement Docker
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("TikSimPro.Docker")

class DockerConfigManager:
    """Gestionnaire de configuration pour l'environnement Docker"""
    
    def __init__(self):
        self.account_id = os.getenv('ACCOUNT_ID', 'viral_account_1')
        self.publisher = os.getenv('PUBLISHER', 'tiktok')
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.auto_publish = os.getenv('AUTO_PUBLISH', 'true').lower() == 'true'
        
        # Configuration vidéo
        self.video_duration = int(os.getenv('VIDEO_DURATION', '30'))
        self.video_width = int(os.getenv('VIDEO_WIDTH', '1080'))
        self.video_height = int(os.getenv('VIDEO_HEIGHT', '1920'))
        self.fps = int(os.getenv('FPS', '60'))
        
        # Paths
        self.output_dir = os.getenv('OUTPUT_DIR', '/app/output')
        self.temp_dir = os.getenv('TEMP_DIR', '/app/temp')
        self.config_dir = os.getenv('CONFIG_DIR', '/app/config')
        
        # API Cookies
        self.cookie_api_url = os.getenv('COOKIE_API_URL', 'http://cookie-api:5000')
        
        # Logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Mode Docker
        self.docker_mode = os.getenv('DOCKER_MODE', 'false').lower() == 'true'
        
    def get_account_config_path(self) -> str:
        """Retourne le chemin vers la config du compte"""
        return f"{self.config_dir}/accounts/{self.account_id}/config.json"
    
    def get_publisher_config_path(self) -> str:
        """Retourne le chemin vers la config du publisher"""
        return f"{self.config_dir}/accounts/{self.account_id}/{self.publisher}.json"
    
    def load_base_config(self) -> Dict[str, Any]:
        """Charge la configuration de base"""
        base_config_path = f"{self.config_dir}/base/config.json"
        
        if os.path.exists(base_config_path):
            with open(base_config_path, 'r') as f:
                return json.load(f)
        
        # Configuration par défaut si pas de fichier
        return self.get_default_config()
    
    def load_account_config(self) -> Dict[str, Any]:
        """Charge la configuration spécifique au compte"""
        account_config_path = self.get_account_config_path()
        
        if os.path.exists(account_config_path):
            with open(account_config_path, 'r') as f:
                return json.load(f)
        
        return {}
    
    def load_publisher_config(self) -> Dict[str, Any]:
        """Charge la configuration spécifique au publisher"""
        publisher_config_path = self.get_publisher_config_path()
        
        if os.path.exists(publisher_config_path):
            with open(publisher_config_path, 'r') as f:
                return json.load(f)
        
        return {}
    
    def get_merged_config(self) -> Dict[str, Any]:
        """Fusionne toutes les configurations avec priorité aux variables d'environnement"""
        base_config = self.load_base_config()
        account_config = self.load_account_config()
        publisher_config = self.load_publisher_config()
        
        # Fusion des configs (ordre de priorité : env > account > publisher > base)
        config = {**base_config, **publisher_config, **account_config}
        
        # Override avec les variables d'environnement
        if 'video_generator' in config:
            if 'params' not in config['video_generator']:
                config['video_generator']['params'] = {}
            
            config['video_generator']['params'].update({
                'duration': self.video_duration,
                'width': self.video_width,
                'height': self.video_height,
                'fps': self.fps
            })
        
        if 'pipeline' in config:
            if 'params' not in config['pipeline']:
                config['pipeline']['params'] = {}
                
            config['pipeline']['params'].update({
                'output_dir': self.output_dir,
                'auto_publish': self.auto_publish
            })
        
        # Configuration publisher
        if 'publishers' not in config:
            config['publishers'] = {}
        
        if self.publisher not in config['publishers']:
            config['publishers'][self.publisher] = {
                'name': f'{self.publisher.title()}Publisher',
                'params': {},
                'enabled': True
            }
        
        return config
    
    def get_default_config(self) -> Dict[str, Any]:
        """Configuration par défaut pour Docker"""
        return {
            "pipeline": {
                "name": "SimplePipeline",
                "params": {
                    "output_dir": self.output_dir,
                    "auto_publish": self.auto_publish,
                    "video_duration": self.video_duration,
                    "video_dimensions": [self.video_width, self.video_height],
                    "fps": self.fps
                }
            },
            "video_generator": {
                "name": "CircleSimulator",
                "params": {
                    "width": self.video_width,
                    "height": self.video_height,
                    "fps": self.fps,
                    "duration": self.video_duration,
                    "balls": 1,
                    "gravity": 500,
                    "style": "satisfying"
                }
            },
            "audio_generator": {
                "name": "CustomMidiAudioGenerator",
                "params": {
                    "sample_rate": 44100,
                    "preset_name": "satisfying_bounce"
                }
            },
            "media_combiner": {
                "name": "FFmpegCombiner",
                "params": {
                    "video_codec": "libx264",
                    "audio_codec": "aac"
                }
            },
            "publishers": {
                self.publisher: {
                    "name": f"{self.publisher.title()}Publisher",
                    "params": {
                        "auto_close": True,
                        "headless": True,
                        "cookie_api_url": self.cookie_api_url
                    },
                    "enabled": True
                }
            }
        }
    
    def setup_logging(self):
        """Configure le logging selon les variables d'environnement"""
        level = getattr(logging, self.log_level.upper(), logging.INFO)
        
        # Format des logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(account_id)s/%(publisher)s] - %(message)s'
        )
        
        # Handler pour stdout
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Handler pour fichier (dans Docker)
        log_file = f"{self.output_dir}/tiksimpro_{self.account_id}_{self.publisher}.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # Configurer le root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # Ajouter le contexte au logger
        class ContextAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs):
                return msg, {**kwargs, 'extra': {
                    'account_id': self.extra['account_id'],
                    'publisher': self.extra['publisher']
                }}
        
        # Adapter le logger principal
        logger_adapter = ContextAdapter(
            logging.getLogger("TikSimPro"),
            {'account_id': self.account_id, 'publisher': self.publisher}
        )
        
        return logger_adapter
    
    def validate_environment(self) -> bool:
        """Valide que l'environnement Docker est correctement configuré"""
        required_dirs = [self.output_dir, self.temp_dir]
        
        for dir_path in required_dirs:
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                logger.error(f"Impossible de créer le dossier {dir_path}: {e}")
                return False
        
        # Vérifier FFmpeg
        if os.system("ffmpeg -version > /dev/null 2>&1") != 0:
            logger.error("FFmpeg n'est pas installé ou accessible")
            return False
        
        logger.info(f"✅ Environnement Docker validé pour {self.account_id}/{self.publisher}")
        return True
    
    def debug_environment(self):
        """Affiche les variables d'environnement pour debug"""
        if not self.debug:
            return
            
        print("\n🔍 === DEBUG ENVIRONNEMENT DOCKER ===")
        print(f"Account ID: {self.account_id}")
        print(f"Publisher: {self.publisher}")
        print(f"Auto Publish: {self.auto_publish}")
        print(f"Video: {self.video_width}x{self.video_height} @ {self.fps}fps, {self.video_duration}s")
        print(f"Output Dir: {self.output_dir}")
        print(f"Cookie API: {self.cookie_api_url}")
        print("=" * 40 + "\n")


# Extension du main.py pour Docker
def docker_main():
    """Point d'entrée principal pour le mode Docker"""
    
    # Configuration Docker
    docker_config = DockerConfigManager()
    
    # Setup logging
    logger = docker_config.setup_logging()
    
    # Debug si nécessaire
    docker_config.debug_environment()
    
    # Validation environnement
    if not docker_config.validate_environment():
        logger.error("❌ Validation de l'environnement échouée")
        exit(1)
    
    # Banner Docker
    logger.info("🐳 === TikSimPro Mode Docker ===")
    logger.info(f"📱 Compte: {docker_config.account_id}")
    logger.info(f"🎬 Publisher: {docker_config.publisher}")
    logger.info(f"⚙️ Auto-publish: {docker_config.auto_publish}")
    
    try:
        # Charger la configuration fusionnée
        config_dict = docker_config.get_merged_config()
        
        # Importer votre code existant
        from src.core.config import Config
        from src.core.plugin_manager import PluginManager
        
        # Créer la config object
        config = Config()
        config.config = config_dict
        
        # Setup des composants comme dans votre main.py existant
        pipeline = setup_components_docker(config, docker_config)
        if pipeline:
            result_path = run_pipeline_docker(pipeline, logger)
            
            if result_path:
                logger.info(f"✅ Vidéo générée avec succès: {result_path}")
                
                if docker_config.auto_publish:
                    logger.info("🚀 Publication automatique activée")
                else:
                    logger.info("💾 Vidéo sauvegardée (publication désactivée)")
            else:
                logger.error("❌ Échec de génération de la vidéo")
                exit(1)
        else:
            logger.error("❌ Échec de configuration du pipeline")
            exit(1)
            
    except Exception as e:
        logger.error(f"💥 Erreur fatale: {e}")
        if docker_config.debug:
            import traceback
            traceback.print_exc()
        exit(1)


def setup_components_docker(config, docker_config):
    """Version Docker du setup des composants"""
    try:
        plugin_dirs = ["pipelines", "trend_analyzers", "video_generators", 
                      "audio_generators", "media_combiners", "video_enhancers", "publishers"]
        manager = PluginManager("src", plugin_dirs)

        # Créer le pipeline
        pipeline_config = config.get("pipeline", {})
        pipeline = manager.get_plugin(pipeline_config.get("name", "SimplePipeline"))(**{
            k: v for k, v in pipeline_config.get("params", {}).items() 
            if not k.startswith("_comment")
        })

        # Configurer tous les composants
        components = [
            ("trend_analyzer", "set_trend_analyzer"),
            ("video_generator", "set_video_generator"),
            ("audio_generator", "set_audio_generator"),
            ("media_combiner", "set_media_combiner"),
            ("video_enhancer", "set_video_enhancer")
        ]
        
        for comp_name, setter_name in components:
            comp_config = config.get(comp_name)
            if comp_config:
                comp_class = manager.get_plugin(comp_config.get("name"))
                if comp_class:
                    component = comp_class(**{
                        k: v for k, v in comp_config.get("params", {}).items() 
                        if not k.startswith("_comment")
                    })
                    getattr(pipeline, setter_name)(component)

        # Ajouter les publishers
        publishers_config = config.get("publishers", {})
        for pub_name, pub_config in publishers_config.items():
            if pub_config.get("enabled", False):
                pub_class = manager.get_plugin(pub_config.get("name"))
                if pub_class:
                    publisher = pub_class(**{
                        k: v for k, v in pub_config.get("params", {}).items() 
                        if not k.startswith("_comment")
                    })
                    pipeline.add_publisher(publisher)

        return pipeline
        
    except Exception as e:
        logger.error(f"Erreur setup composants: {e}")
        return None


def run_pipeline_docker(pipeline, logger):
    """Version Docker de l'exécution du pipeline"""
    try:
        start_time = time.time()
        
        logger.info("🎬 Démarrage de la génération vidéo...")
        result_path = pipeline.execute()
        
        if not result_path:
            logger.error("Pipeline execution failed")
            return None
        
        elapsed_time = time.time() - start_time
        logger.info(f"⏱️ Pipeline exécuté en {elapsed_time:.2f} secondes")
        
        return result_path
        
    except Exception as e:
        logger.error(f"Erreur exécution pipeline: {e}")
        return None


if __name__ == "__main__":
    import sys
    import time
    
    # Vérifier si on est en mode Docker
    if "--docker-mode" in sys.argv or os.getenv('DOCKER_MODE', 'false').lower() == 'true':
        docker_main()
    else:
        # Importer et exécuter le main original
        from main import main
        main()