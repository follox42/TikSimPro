#!/usr/bin/env python3
"""
TikSimPro - Système modulaire de création et publication de contenu viral
=========================================================================

Architecture plugin-based permettant de changer facilement:
- Les simulateurs de contenu
- Les enhancers vidéo
- Les plateformes de publication
- Les sources de données tendances
"""

import os
import sys
import time
import json
import logging
import argparse
import threading
import importlib
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import schedule

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tiksim.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("TikSimPro")

class ModuleRegistry:
    """
    Registre central pour tous les modules chargés dynamiquement.
    Gère le chargement, l'instanciation et l'accès aux modules.
    """
    
    def __init__(self):
        self.module_types = {
            "simulator": "simulators.base_simulator.BaseSimulator",
            "enhancer": "enhancers.base_enhancer.BaseEnhancer",
            "publisher": "publishers.base_publisher.BasePublisher",
            "data_provider": "data_providers.base_provider.BaseDataProvider"
        }
        
        # Format: {type: {name: class}}
        self.available_modules = {}
        
        # Format: {type: {name: instance}}
        self.active_instances = {k: {} for k in self.module_types}
        
        # Charger tous les modules disponibles
        self._discover_modules()
    
    def _discover_modules(self) -> None:
        """
        Découvre tous les modules disponibles en parcourant les répertoires
        et en recherchant les classes qui héritent des interfaces de base.
        """
        for module_type, base_class_path in self.module_types.items():
            # Initialiser le dictionnaire pour ce type de module
            self.available_modules[module_type] = {}
            
            # Importer la classe de base
            try:
                base_module_path, base_class_name = base_class_path.rsplit(".", 1)
                base_module = importlib.import_module(base_module_path)
                base_class = getattr(base_module, base_class_name)
            except (ImportError, AttributeError) as e:
                logger.error(f"Erreur chargement classe base {base_class_path}: {e}")
                continue
            
            # Obtenir le répertoire où se trouvent les modules
            module_dir = base_module_path.split(".")[0]
            module_path = Path(os.path.dirname(__file__)) / module_dir
            
            # Parcourir tous les fichiers Python dans ce répertoire
            for file_path in module_path.glob("*.py"):
                # Ignorer les fichiers spéciaux
                if file_path.name.startswith("__") or file_path.name == f"base_{module_type}.py":
                    continue
                
                module_name = file_path.stem
                full_module_path = f"{module_dir}.{module_name}"
                
                try:
                    # Importer le module
                    module = importlib.import_module(full_module_path)
                    
                    # Rechercher toutes les classes qui héritent de la classe de base
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        if (isinstance(attr, type) and 
                            issubclass(attr, base_class) and 
                            attr != base_class):
                            
                            # Enregistrer la classe
                            self.available_modules[module_type][attr_name] = attr
                            logger.debug(f"Module découvert: {module_type}.{attr_name}")
                
                except Exception as e:
                    logger.error(f"Erreur chargement module {full_module_path}: {e}")
                    continue
            
            # Afficher les modules découverts
            modules_str = ', '.join(self.available_modules[module_type].keys())
            logger.info(f"Modules {module_type} disponibles: {modules_str}")
    
    def get_module_class(self, module_type: str, module_name: str) -> Optional[type]:
        """
        Récupère une classe de module par son nom et son type.
        
        Args:
            module_type: Type de module (simulator, enhancer, publisher, etc.)
            module_name: Nom de la classe du module
            
        Returns:
            La classe du module, ou None si non trouvée
        """
        return self.available_modules.get(module_type, {}).get(module_name)
    
    def create_instance(self, module_type: str, module_name: str, 
                        params: Dict[str, Any] = None, instance_name: str = None) -> Any:
        """
        Crée et enregistre une instance d'un module avec les paramètres donnés.
        
        Args:
            module_type: Type de module (simulator, enhancer, publisher, etc.)
            module_name: Nom de la classe du module
            params: Paramètres d'initialisation pour le module
            instance_name: Nom optionnel pour l'instance (utilise module_name par défaut)
            
        Returns:
            L'instance créée, ou None en cas d'erreur
        """
        module_class = self.get_module_class(module_type, module_name)
        if not module_class:
            logger.error(f"Module {module_type}.{module_name} non trouvé")
            return None
        
        # Utiliser le nom du module comme nom d'instance par défaut
        instance_name = instance_name or module_name
        
        try:
            # Créer l'instance avec les paramètres fournis
            params = params or {}
            instance = module_class(**params)
            
            # Enregistrer l'instance
            self.active_instances[module_type][instance_name] = instance
            logger.info(f"Instance créée: {module_type}.{instance_name}")
            
            return instance
            
        except Exception as e:
            logger.error(f"Erreur création instance {module_type}.{module_name}: {e}")
            traceback.print_exc()
            return None
    
    def get_instance(self, module_type: str, instance_name: str) -> Any:
        """
        Récupère une instance active par son type et son nom.
        
        Args:
            module_type: Type de module
            instance_name: Nom de l'instance
            
        Returns:
            L'instance, ou None si non trouvée
        """
        return self.active_instances.get(module_type, {}).get(instance_name)
    
    def get_all_instances(self, module_type: str) -> Dict[str, Any]:
        """
        Récupère toutes les instances actives d'un type de module.
        
        Args:
            module_type: Type de module
            
        Returns:
            Dictionnaire {nom: instance}
        """
        return self.active_instances.get(module_type, {}).copy()
    
    def list_available_modules(self, module_type: str = None) -> Dict[str, List[str]]:
        """
        Liste tous les modules disponibles, éventuellement filtrés par type.
        
        Args:
            module_type: Type de module (optionnel)
            
        Returns:
            Dictionnaire {type: [noms]}
        """
        result = {}
        
        if module_type:
            if module_type in self.available_modules:
                result[module_type] = list(self.available_modules[module_type].keys())
        else:
            for m_type, modules in self.available_modules.items():
                result[m_type] = list(modules.keys())
                
        return result


class ConfigManager:
    """
    Gestionnaire de configuration pour TikSimPro.
    Gère le chargement, la sauvegarde et l'accès aux paramètres de configuration.
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialise le gestionnaire de configuration.
        
        Args:
            config_file: Chemin vers le fichier de configuration
        """
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Charge la configuration depuis le fichier.
        Si le fichier n'existe pas, retourne la configuration par défaut.
        
        Returns:
            Dictionnaire de configuration
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"Configuration chargée: {self.config_file}")
                return config
            except Exception as e:
                logger.error(f"Erreur chargement configuration: {e}")
        
        logger.warning(f"Fichier de configuration {self.config_file} non trouvé, utilisation des valeurs par défaut")
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Retourne la configuration par défaut.
        
        Returns:
            Dictionnaire de configuration par défaut
        """
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
            "publishers": {
                "tiktok": {
                    "type": "TikTokPublisher",
                    "params": {
                        "auto_close": True
                    },
                    "enabled": True
                },
                "youtube": {
                    "type": "YouTubePublisher",
                    "params": {
                        "client_secrets_file": "client_secret.json",
                        "token_file": "youtube_token.pickle",
                        "auto_close": True
                    },
                    "enabled": True
                }
            },
            "data_provider": {
                "type": "TikTokScraper",
                "params": {
                    "cache_dir": "tiktok_data"
                }
            },
            "output_dir": "videos",
            "auto_publish": False,
            "publishing": {
                "cross_platform": True,
                "default_platform": "tiktok"
            }
        }
    
    def save_config(self) -> bool:
        """
        Sauvegarde la configuration dans le fichier.
        
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration sauvegardée: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration par sa clé.
        Les clés peuvent être hiérarchiques, séparées par des points.
        
        Args:
            key: Clé de configuration (ex: "simulator.params.width")
            default: Valeur par défaut si la clé n'existe pas
            
        Returns:
            La valeur de configuration, ou la valeur par défaut
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Définit une valeur de configuration.
        Les clés peuvent être hiérarchiques, séparées par des points.
        
        Args:
            key: Clé de configuration (ex: "simulator.params.width")
            value: Valeur à définir
        """
        keys = key.split('.')
        config = self.config
        
        # Naviguer jusqu'au dernier niveau
        for i, k in enumerate(keys[:-1]):
            # Créer le dictionnaire s'il n'existe pas
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        # Définir la valeur
        config[keys[-1]] = value
        logger.debug(f"Configuration mise à jour: {key} = {value}")
    
    def get_all(self) -> Dict[str, Any]:
        """
        Récupère toute la configuration.
        
        Returns:
            Dictionnaire complet de configuration
        """
        return self.config.copy()


class TikSimPro:
    """
    Classe principale du système TikSimPro.
    Coordonne tous les modules et gère le workflow complet.
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialise le système TikSimPro.
        
        Args:
            config_file: Chemin vers le fichier de configuration
        """
        # Initialiser le gestionnaire de configuration
        self.config_manager = ConfigManager(config_file)
        
        # Initialiser le registre de modules
        self.module_registry = ModuleRegistry()
        
        # Répertoire de sortie pour les vidéos
        self.output_dir = self.config_manager.get('output_dir', 'videos')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialiser le provider de données
        self._init_data_provider()
        
        # État interne
        self.current_operation = None
        self.operation_status = {}
        
        logger.info("TikSimPro initialisé")
    
    def _init_data_provider(self) -> None:
        """Initialise le provider de données configuré"""
        provider_config = self.config_manager.get('data_provider', {})
        provider_type = provider_config.get('type', 'TikTokScraper')
        params = provider_config.get('params', {})
        
        self.module_registry.create_instance(
            'data_provider', provider_type, params, 'default')
    
    def get_data_provider(self) -> Any:
        """
        Récupère l'instance du provider de données.
        
        Returns:
            L'instance du provider de données
        """
        return self.module_registry.get_instance('data_provider', 'default')
    
    def create_simulator(self, simulator_type: str = None, params: Dict[str, Any] = None) -> Any:
        """
        Crée une instance de simulateur selon la configuration.
        
        Args:
            simulator_type: Type de simulateur (optionnel, utilise la config par défaut)
            params: Paramètres supplémentaires pour le simulateur
            
        Returns:
            L'instance du simulateur créée
        """
        # Utiliser les paramètres de la configuration
        sim_config = self.config_manager.get('simulator', {})
        sim_type = simulator_type or sim_config.get('type', 'AdvancedPhysicsSimulation')
        sim_params = sim_config.get('params', {}).copy()
        
        # Fusionner avec les paramètres fournis
        if params:
            sim_params.update(params)
        
        return self.module_registry.create_instance(
            'simulator', sim_type, sim_params, 'current')
    
    def get_simulator(self) -> Any:
        """
        Récupère l'instance courante du simulateur.
        
        Returns:
            L'instance du simulateur
        """
        return self.module_registry.get_instance('simulator', 'current')
    
    def create_enhancer(self, enhancer_type: str = None, params: Dict[str, Any] = None) -> Any:
        """
        Crée une instance d'enhancer selon la configuration.
        
        Args:
            enhancer_type: Type d'enhancer (optionnel, utilise la config par défaut)
            params: Paramètres supplémentaires pour l'enhancer
            
        Returns:
            L'instance de l'enhancer créée
        """
        # Utiliser les paramètres de la configuration
        enh_config = self.config_manager.get('enhancer', {})
        enh_type = enhancer_type or enh_config.get('type', 'VideoEnhancer')
        enh_params = enh_config.get('params', {}).copy()
        
        # Fusionner avec les paramètres fournis
        if params:
            enh_params.update(params)
        
        return self.module_registry.create_instance(
            'enhancer', enh_type, enh_params, 'current')
    
    def get_enhancer(self) -> Any:
        """
        Récupère l'instance courante de l'enhancer.
        
        Returns:
            L'instance de l'enhancer
        """
        return self.module_registry.get_instance('enhancer', 'current')
    
    def initialize_publishers(self) -> Dict[str, Any]:
        """
        Initialise tous les publishers configurés.
        
        Returns:
            Dictionnaire {plateforme: instance}
        """
        publishers_config = self.config_manager.get('publishers', {})
        initialized = {}
        
        for platform, config in publishers_config.items():
            if config.get('enabled', True):
                pub_type = config.get('type')
                params = config.get('params', {})
                
                instance = self.module_registry.create_instance(
                    'publisher', pub_type, params, platform)
                
                if instance:
                    initialized[platform] = instance
        
        return initialized
    
    def get_publisher(self, platform: str = None) -> Any:
        """
        Récupère une instance de publisher par sa plateforme.
        
        Args:
            platform: Nom de la plateforme (ex: 'tiktok', 'youtube')
            
        Returns:
            L'instance du publisher, ou None si non trouvée
        """
        if not platform:
            # Utiliser la plateforme par défaut
            platform = self.config_manager.get('publishing.default_platform', 'tiktok')
        
        return self.module_registry.get_instance('publisher', platform)
    
    def get_all_publishers(self) -> Dict[str, Any]:
        """
        Récupère toutes les instances de publishers actives.
        
        Returns:
            Dictionnaire {plateforme: instance}
        """
        return self.module_registry.get_all_instances('publisher')
    
    def generate_video(self, options: Dict[str, Any] = None) -> Optional[str]:
        """
        Génère une vidéo virale en utilisant le simulateur et l'enhancer configurés.
        
        Args:
            options: Options spécifiques pour la génération
            
        Returns:
            Le chemin de la vidéo générée, ou None en cas d'erreur
        """
        self.current_operation = "generate_video"
        self.operation_status = {"phase": "init", "progress": 0}
        
        try:
            # Fusionner les options avec la configuration
            options = options or {}
            
            # 1. Préparation et analyse des tendances
            self.operation_status = {"phase": "analyze_trends", "progress": 10}
            data_provider = self.get_data_provider()
            if not data_provider:
                logger.error("Provider de données non initialisé")
                return None
            
            trend_analysis = data_provider.get_trend_analysis()
            
            # 2. Créer un nom de fichier basé sur le timestamp
            timestamp = int(time.time())
            video_name = f"tiktok_viral_{timestamp}.mp4"
            video_path = os.path.join(self.output_dir, video_name)
            
            # 3. Initialiser le simulateur
            self.operation_status = {"phase": "init_simulator", "progress": 20}
            simulator = self.create_simulator()
            if not simulator:
                logger.error("Échec de l'initialisation du simulateur")
                return None
            
            # Configurer le simulateur
            sim_options = {
                'output_path': video_path,
            }
            # Ajouter d'autres options spécifiques si nécessaire
            if 'simulator' in options:
                sim_options.update(options['simulator'])
            
            simulator.setup(sim_options)
            
            # Appliquer les paramètres depuis l'analyse des tendances
            settings = trend_analysis.get("recommended_settings", {})
            if hasattr(simulator, 'set_color_palette') and 'color_palette' in settings:
                simulator.set_color_palette(settings['color_palette'])
                
            if hasattr(simulator, 'set_beat_frequency') and 'beat_frequency' in settings:
                simulator.set_beat_frequency(settings['beat_frequency'])
            
            # 4. Exécuter la simulation
            self.operation_status = {"phase": "run_simulation", "progress": 30}
            simulation_success = simulator.run_simulation()
            if not simulation_success:
                logger.error("Échec de l'exécution de la simulation")
                return None

            # 5. Générer la piste audio à partir des événements de la simulation
            audio_path = simulator.render_audio_from_events()
            if audio_path:
                logger.info(f"Piste audio générée: {audio_path}")
                simulator.output_audio_file = audio_path
            else:
                logger.warning("Échec de la génération audio")
            
            # 6. Générer la vidéo brute
            self.operation_status = {"phase": "generate_video", "progress": 70}
            video_result = simulator.generate_video()
            if not video_result:
                logger.error("Échec de la génération de la vidéo")
                return None
            
            # 7. Créer l'enhancer et améliorer la vidéo
            self.operation_status = {"phase": "enhance_video", "progress": 80}
            enhancer = self.create_enhancer()
            if not enhancer:
                logger.warning("Enhancer non disponible, utilisation de la vidéo brute")
                return video_result
            
            # Préparer les options d'amélioration
            enhanced_path = os.path.join(self.output_dir, f"tiktok_viral_{timestamp}_enhanced.mp4")
            enhance_options = self.config_manager.get('enhancer.params', {}).copy()
            
            # Ajouter les paramètres depuis l'analyse des tendances
            enhance_options.update({
                "intro_text": "Watch this all the way through! 👀",
                "hashtags": settings.get("recommended_hashtags", []),
                "music_file": getattr(simulator, 'output_audio_file', None)
            })
            
            # Ajouter d'autres options spécifiques si nécessaire
            if 'enhancer' in options:
                enhance_options.update(options['enhancer'])
            
            # Appliquer les améliorations
            enhanced_result = enhancer.enhance_video(
                video_result,
                enhanced_path,
                enhance_options
            )
            
            self.operation_status = {"phase": "complete", "progress": 100}
            logger.info(f"Vidéo générée avec succès: {enhanced_result or video_result}")
            
            # 7. Retourner le chemin de la vidéo améliorée, ou de la vidéo brute si l'amélioration a échoué
            return enhanced_result or video_result
            
        except Exception as e:
            logger.exception(f"Erreur lors de la génération de la vidéo: {e}")
            self.operation_status = {"phase": "error", "error": str(e)}
            return None
        finally:
            # Réinitialiser l'opération
            self.current_operation = None
    
    def publish_video(self, video_path: str = None, platforms: List[str] = None) -> Dict[str, bool]:
        """
        Publie une vidéo sur les plateformes spécifiées.
        
        Args:
            video_path: Chemin de la vidéo à publier
            platforms: Liste des plateformes où publier 
                       (None = utiliser toutes les plateformes activées)
            
        Returns:
            Dictionnaire {plateforme: succès}
        """
        self.current_operation = "publish_video"
        self.operation_status = {"phase": "init", "progress": 0}
        
        try:
            # 1. Rechercher la vidéo la plus récente si aucun chemin n'est spécifié
            if not video_path:
                video_files = [f for f in os.listdir(self.output_dir) if f.endswith('.mp4')]
                if not video_files:
                    logger.error("Aucune vidéo trouvée à publier")
                    return {}
                
                # Trier par date de modification (la plus récente en premier)
                video_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.output_dir, f)), 
                                reverse=True)
                video_path = os.path.join(self.output_dir, video_files[0])
            
            # 2. Vérifier que le fichier existe
            if not os.path.exists(video_path):
                logger.error(f"Fichier vidéo introuvable: {video_path}")
                return {}
            
            # 3. Obtenir des hashtags tendance
            self.operation_status = {"phase": "get_metadata", "progress": 10}
            data_provider = self.get_data_provider()
            if not data_provider:
                logger.warning("Provider de données non disponible, utilisation des hashtags par défaut")
                hashtags = ["fyp", "foryou", "viral", "satisfying"]
            else:
                hashtags = data_provider.get_trending_hashtags()[:8]
            
            # Ajouter toujours les hashtags essentiels
            essential_hashtags = ["fyp", "foryou", "viral"]
            for tag in essential_hashtags:
                if tag not in hashtags:
                    hashtags.insert(0, tag)
            
            # 4. Générer une description captivante
            captions = [
                "This simulation is so satisfying!",
                "Watch till the end for a surprise!",
                "I could watch this all day!",
                "The physics in this are incredible!",
                "Turn on the sound!"
            ]
            import random
            caption = random.choice(captions)
            
            # 5. Initialiser les publishers si nécessaire
            self.operation_status = {"phase": "init_publishers", "progress": 20}
            if not self.get_all_publishers():
                self.initialize_publishers()
            
            # 6. Déterminer les plateformes à utiliser
            if not platforms:
                # Si cross_platform est activé, publier sur toutes les plateformes
                if self.config_manager.get('publishing.cross_platform', False):
                    platforms = list(self.get_all_publishers().keys())
                else:
                    # Sinon, utiliser uniquement la plateforme par défaut
                    default_platform = self.config_manager.get('publishing.default_platform', 'tiktok')
                    platforms = [default_platform]
            
            # 7. Publier sur chaque plateforme
            results = {}
            total_platforms = len(platforms)
            
            for i, platform in enumerate(platforms):
                progress = 20 + int(80 * (i / total_platforms))
                self.operation_status = {
                    "phase": f"publish_{platform}", 
                    "progress": progress,
                    "platform": platform
                }
                
                publisher = self.get_publisher(platform)
                if not publisher:
                    logger.warning(f"Publisher {platform} non disponible")
                    results[platform] = False
                    continue
                
                logger.info(f"Publication sur {platform}...")
                print(f"Publication de la vidéo sur {platform}...")
                
                try:
                    # Différentes configurations selon la plateforme
                    if platform == 'youtube':
                        # Pour YouTube, utiliser un titre plus descriptif
                        title = f"Satisfying Physics Simulation - {time.strftime('%Y-%m-%d')}"
                        result = publisher.upload_video(
                            video_path=video_path,
                            caption=caption,
                            hashtags=hashtags,
                            title=title
                        )
                    else:
                        # Pour TikTok et autres plateformes
                        result = publisher.upload_video(
                            video_path=video_path,
                            caption=caption,
                            hashtags=hashtags
                        )
                        
                    results[platform] = result
                    
                except Exception as e:
                    logger.error(f"Erreur publication sur {platform}: {e}")
                    results[platform] = False
            
            self.operation_status = {"phase": "complete", "progress": 100, "results": results}
            
            # Afficher le résumé
            for platform, success in results.items():
                status = "réussie" if success else "échouée"
                print(f"Publication sur {platform}: {status}")
            
            return results
            
        except Exception as e:
            logger.exception(f"Erreur lors de la publication: {e}")
            self.operation_status = {"phase": "error", "error": str(e)}
            return {}
        finally:
            self.current_operation = None
    
    def generate_and_publish(self, options: Dict[str, Any] = None, 
                            platforms: List[str] = None) -> Tuple[Optional[str], Dict[str, bool]]:
        """
        Génère et publie une vidéo en une seule opération.
        
        Args:
            options: Options spécifiques pour la génération
            platforms: Liste des plateformes où publier
            
        Returns:
            Tuple (chemin de la vidéo, résultats de publication)
        """
        # Générer la vidéo
        video_path = self.generate_video(options)
        
        if not video_path:
            logger.error("Échec de la génération de la vidéo")
            return None, {}
        
        # Publier la vidéo
        publish_results = self.publish_video(video_path, platforms)
        
        return video_path, publish_results
    
    def schedule_publication(self, video_path: str, schedule_time: datetime, 
                           platforms: List[str] = None) -> str:
        """
        Planifie la publication d'une vidéo.
        
        Args:
            video_path: Chemin de la vidéo à publier
            schedule_time: Heure de publication (format datetime)
            platforms: Liste des plateformes où publier
            
        Returns:
            ID de la tâche planifiée
        """
        # Vérifier que le fichier existe
        if not os.path.exists(video_path):
            logger.error(f"Fichier vidéo introuvable: {video_path}")
            return None
        
        # Définir la fonction de publication
        def publish_task():
            logger.info(f"Publication programmée démarrée pour: {video_path}")
            self.publish_video(video_path, platforms)
        
        # Calculer le délai
        now = datetime.now()
        if schedule_time < now:
            logger.error("L'heure de publication est dans le passé")
            return None
        
        # Programmer la tâche
        delay = (schedule_time - now).total_seconds()
        
        # Utiliser schedule pour la planification
        job = schedule.every(delay).seconds.do(publish_task)
        job_id = f"publish_{int(time.time())}"
        
        logger.info(f"Publication programmée pour: {schedule_time}")
        return job_id
    
    def run_daily_schedule(self, times: List[str] = None, 
                          options: Dict[str, Any] = None) -> None:
        """
        Configure une planification quotidienne pour générer et publier des vidéos.
        
        Args:
            times: Liste d'heures de publication (format HH:MM)
            options: Options spécifiques pour la génération
        """
        if not times:
            # Heures optimales pour TikTok
            times = ["09:00", "12:30", "18:00", "21:00"]
        
        logger.info(f"Configuration de la planification quotidienne: {times}")
        
        # Configurer les tâches planifiées
        for time_str in times:
            # Créer une fonction de rappel pour chaque heure
            def task_wrapper(time_str=time_str):
                logger.info(f"Exécution de la tâche planifiée à {time_str}")
                self.generate_and_publish(options)
            
            schedule.every().day.at(time_str).do(task_wrapper)
        
        print(f"Planification quotidienne configurée: {', '.join(times)}")
        print("Appuyez sur Ctrl+C pour arrêter...")
        
        # Exécuter les tâches planifiées
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nPlanification arrêtée par l'utilisateur.")
    
    def get_operation_status(self) -> Dict[str, Any]:
        """
        Récupère le statut de l'opération en cours.
        
        Returns:
            Dictionnaire de statut de l'opération
        """
        return {
            "operation": self.current_operation,
            "status": self.operation_status
        }
    
    def stop_current_operation(self) -> bool:
        """
        Arrête l'opération en cours.
        
        Returns:
            True si une opération a été arrêtée, False sinon
        """
        if not self.current_operation:
            return False
        
        logger.info(f"Arrêt de l'opération: {self.current_operation}")
        
        # Arrêter le simulateur si en cours d'exécution
        simulator = self.get_simulator()
        if simulator and hasattr(simulator, 'simulation_running'):
            simulator.simulation_running = False
        
        self.current_operation = None
        self.operation_status = {"phase": "stopped", "progress": 0}
        
        return True


def print_banner():
    """Affiche la bannière TikSimPro"""
    banner = """
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   ████████╗██╗██╗  ██╗███████╗██╗███╗   ███╗               ║
║   ╚══██╔══╝██║██║ ██╔╝██╔════╝██║████╗ ████║               ║
║      ██║   ██║█████╔╝ ███████╗██║██╔████╔██║               ║
║      ██║   ██║██╔═██╗ ╚════██║██║██║╚██╔╝██║               ║
║      ██║   ██║██║  ██╗███████║██║██║ ╚═╝ ██║               ║
║      ╚═╝   ╚═╝╚═╝  ╚═╝╚══════╝╚═╝╚═╝     ╚═╝               ║
║                                                            ║
║   Génération Automatisée de Contenu Viral Multi-Plateforme ║
║                      Version 2.0                           ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
"""
    print(banner)


def show_interactive_menu(tiksim: TikSimPro):
    """
    Affiche un menu interactif pour l'utilisateur.
    
    Args:
        tiksim: Instance de TikSimPro
    """
    print_banner()
    
    while True:
        print("\nMenu Principal:")
        print("=" * 40)
        print("1. Générer une vidéo")
        print("2. Publier la dernière vidéo")
        print("3. Générer et publier")
        print("4. Configurer une planification quotidienne")
        print("5. Gérer les modules")
        print("6. Configurer les paramètres")
        print("7. Quitter")
        
        choice = input("\nChoisissez une option (1-7): ")
        
        if choice == "1":
            # Paramètres avancés
            print("\nOptions de génération:")
            print("1. Utiliser les paramètres par défaut")
            print("2. Personnaliser les paramètres")
            
            sub_choice = input("Choix (1-2): ")
            options = None
            
            if sub_choice == "2":
                # Options personnalisées
                options = {}
                
                # Paramètres du simulateur
                options["simulator"] = {}
                width = input("Largeur de la vidéo [1080]: ")
                if width.strip():
                    options["simulator"]["width"] = int(width)
                
                height = input("Hauteur de la vidéo [1920]: ")
                if height.strip():
                    options["simulator"]["height"] = int(height)
                
                fps = input("FPS [60]: ")
                if fps.strip():
                    options["simulator"]["fps"] = int(fps)
                
                duration = input("Durée en secondes [61]: ")
                if duration.strip():
                    options["simulator"]["duration"] = int(duration)
                
                # Paramètres de l'enhancer
                options["enhancer"] = {}
                add_intro = input("Ajouter une introduction? (o/n) [n]: ")
                options["enhancer"]["add_intro"] = add_intro.lower() in ["o", "oui", "y", "yes"]
                
                add_hashtags = input("Ajouter des hashtags? (o/n) [n]: ")
                options["enhancer"]["add_hashtags"] = add_hashtags.lower() in ["o", "oui", "y", "yes"]
            
            print("\nGénération de la vidéo en cours...")
            video_path = tiksim.generate_video(options)
            
            if video_path:
                print(f"\nVidéo générée avec succès: {video_path}")
            else:
                print("\nErreur lors de la génération de la vidéo")
            
        elif choice == "2":
            # Choix des plateformes
            print("\nPlateformes disponibles:")
            publishers = tiksim.get_all_publishers()
            if not publishers:
                tiksim.initialize_publishers()
                publishers = tiksim.get_all_publishers()
            
            if not publishers:
                print("Aucune plateforme de publication configurée")
                continue
            
            platforms = list(publishers.keys())
            
            for i, platform in enumerate(platforms):
                print(f"{i+1}. {platform}")
            print(f"{len(platforms)+1}. Toutes les plateformes")
            
            sub_choice = input(f"Choix (1-{len(platforms)+1}): ")
            try:
                idx = int(sub_choice) - 1
                if idx == len(platforms):
                    selected_platforms = platforms
                else:
                    selected_platforms = [platforms[idx]]
            except (ValueError, IndexError):
                print("Choix invalide, utilisation de toutes les plateformes")
                selected_platforms = platforms
            
            print("\nPublication de la vidéo en cours...")
            results = tiksim.publish_video(platforms=selected_platforms)
            
            if results:
                print("\nRésumé de la publication:")
                for platform, success in results.items():
                    status = "réussie" if success else "échouée"
                    print(f"- {platform}: {status}")
            else:
                print("\nAucun résultat de publication")
            
        elif choice == "3":
            # Générer et publier
            print("\nGénération et publication en cours...")
            video_path, results = tiksim.generate_and_publish()
            
            if video_path:
                print(f"\nVidéo générée avec succès: {video_path}")
                
                if results:
                    print("\nRésumé de la publication:")
                    for platform, success in results.items():
                        status = "réussie" if success else "échouée"
                        print(f"- {platform}: {status}")
                else:
                    print("\nAucun résultat de publication")
            else:
                print("\nErreur lors de la génération de la vidéo")
            
        elif choice == "4":
            # Planification quotidienne
            print("\nConfiguration de la planification quotidienne")
            times_input = input("Entrez les heures de publication (format HH:MM, séparées par des espaces)\n[09:00 12:30 18:00 21:00]: ")
            
            if times_input.strip():
                times = times_input.split()
            else:
                times = ["09:00", "12:30", "18:00", "21:00"]
            
            print(f"\nDémarrage de la planification quotidienne: {times}")
            print("Appuyez sur Ctrl+C pour arrêter")
            
            tiksim.run_daily_schedule(times)
            
        elif choice == "5":
            # Gérer les modules
            print("\nGestion des Modules:")
            print("1. Afficher les modules disponibles")
            print("2. Afficher les modules actifs")
            print("3. Revenir au menu principal")
            
            sub_choice = input("Choix (1-3): ")
            
            if sub_choice == "1":
                modules = tiksim.module_registry.list_available_modules()
                print("\nModules disponibles:")
                
                for module_type, module_names in modules.items():
                    print(f"\n{module_type.capitalize()}:")
                    for i, name in enumerate(module_names):
                        print(f"  {i+1}. {name}")
            
            elif sub_choice == "2":
                print("\nModules actifs:")
                
                # Data provider
                data_provider = tiksim.get_data_provider()
                if data_provider:
                    print(f"\nData Provider: {data_provider.__class__.__name__}")
                
                # Simulator
                simulator = tiksim.get_simulator()
                if simulator:
                    print(f"\nSimulator: {simulator.__class__.__name__}")
                
                # Enhancer
                enhancer = tiksim.get_enhancer()
                if enhancer:
                    print(f"\nEnhancer: {enhancer.__class__.__name__}")
                
                # Publishers
                publishers = tiksim.get_all_publishers()
                if publishers:
                    print("\nPublishers:")
                    for platform, publisher in publishers.items():
                        print(f"  - {platform}: {publisher.__class__.__name__}")
            
        elif choice == "6":
            # Configurer les paramètres
            print("\nConfiguration des Paramètres:")
            print("1. Afficher la configuration actuelle")
            print("2. Modifier les paramètres du simulateur")
            print("3. Modifier les paramètres de l'enhancer")
            print("4. Gérer les plateformes de publication")
            print("5. Revenir au menu principal")
            
            sub_choice = input("Choix (1-5): ")
            
            if sub_choice == "1":
                # Afficher la configuration
                config = tiksim.config_manager.get_all()
                print("\nConfiguration actuelle:")
                print(json.dumps(config, indent=2))
                
            elif sub_choice == "2":
                # Paramètres du simulateur
                print("\nParamètres du simulateur:")
                sim_config = tiksim.config_manager.get('simulator.params', {})
                
                width = input(f"Largeur de la vidéo [{sim_config.get('width', 1080)}]: ")
                if width.strip():
                    tiksim.config_manager.set('simulator.params.width', int(width))
                
                height = input(f"Hauteur de la vidéo [{sim_config.get('height', 1920)}]: ")
                if height.strip():
                    tiksim.config_manager.set('simulator.params.height', int(height))
                
                fps = input(f"FPS [{sim_config.get('fps', 60)}]: ")
                if fps.strip():
                    tiksim.config_manager.set('simulator.params.fps', int(fps))
                
                duration = input(f"Durée en secondes [{sim_config.get('duration', 61)}]: ")
                if duration.strip():
                    tiksim.config_manager.set('simulator.params.duration', int(duration))
                
                # Sauvegarder
                tiksim.config_manager.save_config()
                print("Configuration sauvegardée")
                
            elif sub_choice == "3":
                # Paramètres de l'enhancer
                print("\nParamètres de l'enhancer:")
                enh_config = tiksim.config_manager.get('enhancer.params', {})
                
                add_intro = input(f"Ajouter une introduction? (o/n) [{enh_config.get('add_intro', False) and 'o' or 'n'}]: ")
                if add_intro.strip():
                    tiksim.config_manager.set('enhancer.params.add_intro', 
                                            add_intro.lower() in ["o", "oui", "y", "yes"])
                
                add_hashtags = input(f"Ajouter des hashtags? (o/n) [{enh_config.get('add_hashtags', False) and 'o' or 'n'}]: ")
                if add_hashtags.strip():
                    tiksim.config_manager.set('enhancer.params.add_hashtags', 
                                           add_hashtags.lower() in ["o", "oui", "y", "yes"])
                
                add_music = input(f"Ajouter de la musique? (o/n) [{enh_config.get('add_music', True) and 'o' or 'n'}]: ")
                if add_music.strip():
                    tiksim.config_manager.set('enhancer.params.add_music', 
                                           add_music.lower() in ["o", "oui", "y", "yes"])
                
                # Sauvegarder
                tiksim.config_manager.save_config()
                print("Configuration sauvegardée")
                
            elif sub_choice == "4":
                # Gérer les plateformes
                print("\nPlateformes de publication:")
                publishers_config = tiksim.config_manager.get('publishers', {})
                
                i = 1
                platforms = []
                for platform, config in publishers_config.items():
                    enabled = config.get('enabled', True)
                    status = "activé" if enabled else "désactivé"
                    print(f"{i}. {platform} ({status})")
                    platforms.append(platform)
                    i += 1
                
                print(f"{i}. Ajouter une nouvelle plateforme")
                print(f"{i+1}. Revenir")
                
                plat_choice = input(f"Choix (1-{i+1}): ")
                
                try:
                    idx = int(plat_choice) - 1
                    if idx < len(platforms):
                        # Modifier une plateforme existante
                        platform = platforms[idx]
                        print(f"\nConfiguration de {platform}:")
                        
                        enabled = input(f"Activer cette plateforme? (o/n) [{publishers_config[platform].get('enabled', True) and 'o' or 'n'}]: ")
                        if enabled.strip():
                            tiksim.config_manager.set(f'publishers.{platform}.enabled', 
                                                   enabled.lower() in ["o", "oui", "y", "yes"])
                        
                        # Sauvegarder
                        tiksim.config_manager.save_config()
                        print("Configuration sauvegardée")
                        
                    elif idx == len(platforms):
                        # Ajouter une nouvelle plateforme
                        platform = input("Nom de la plateforme: ")
                        if platform.strip():
                            # Récupérer les types de publishers disponibles
                            publishers = tiksim.module_registry.list_available_modules('publisher')
                            if not publishers.get('publisher'):
                                print("Aucun type de publisher disponible")
                                continue
                            
                            print("\nTypes de publishers disponibles:")
                            publisher_types = list(publishers.get('publisher', []))
                            for i, pub_type in enumerate(publisher_types):
                                print(f"{i+1}. {pub_type}")
                            
                            type_choice = input(f"Choix (1-{len(publisher_types)}): ")
                            try:
                                type_idx = int(type_choice) - 1
                                if 0 <= type_idx < len(publisher_types):
                                    pub_type = publisher_types[type_idx]
                                    
                                    # Ajouter la nouvelle plateforme
                                    tiksim.config_manager.set(f'publishers.{platform}', {
                                        "type": pub_type,
                                        "params": {},
                                        "enabled": True
                                    })
                                    
                                    # Sauvegarder
                                    tiksim.config_manager.save_config()
                                    print(f"Plateforme {platform} ajoutée")
                            except (ValueError, IndexError):
                                print("Choix invalide")
                
                except (ValueError, IndexError):
                    print("Choix invalide")
        
        elif choice == "7":
            # Quitter
            print("\nAu revoir!")
            break
        
        else:
            print("\nOption invalide, veuillez réessayer")
        
        # Pause avant de revenir au menu
        input("\nAppuyez sur Entrée pour continuer...")


def main():
    """Point d'entrée principal"""
    # Configurer les arguments en ligne de commande
    parser = argparse.ArgumentParser(
        description="TikSimPro - Générateur Automatique de Contenu Viral Multi-Plateforme"
    )
    
    # Arguments généraux
    parser.add_argument("--config", type=str, default="config.json", 
                        help="Fichier de configuration")
    parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="INFO", help="Niveau de log")
    
    # Commandes principales
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Commande generate
    generate_parser = subparsers.add_parser("generate", help="Générer une vidéo")
    generate_parser.add_argument("--duration", type=int, help="Durée de la vidéo en secondes")
    generate_parser.add_argument("--width", type=int, help="Largeur de la vidéo")
    generate_parser.add_argument("--height", type=int, help="Hauteur de la vidéo")
    generate_parser.add_argument("--fps", type=int, help="Images par seconde")
    generate_parser.add_argument("--output", type=str, help="Chemin de sortie pour la vidéo")
    
    # Commande publish
    publish_parser = subparsers.add_parser("publish", help="Publier une vidéo")
    publish_parser.add_argument("--video", type=str, help="Chemin de la vidéo à publier")
    publish_parser.add_argument("--platforms", nargs="+", help="Plateformes de publication")
    
    # Commande generate-and-publish
    gp_parser = subparsers.add_parser("generate-and-publish", help="Générer et publier une vidéo")
    gp_parser.add_argument("--duration", type=int, help="Durée de la vidéo en secondes")
    gp_parser.add_argument("--platforms", nargs="+", help="Plateformes de publication")
    
    # Commande schedule
    schedule_parser = subparsers.add_parser("schedule", help="Planifier des publications")
    schedule_parser.add_argument("--times", nargs="+", help="Heures de publication (format HH:MM)")
    
    # Commande interactive
    subparsers.add_parser("interactive", help="Mode interactif (interface console)")
    
    # Commande list-modules
    list_parser = subparsers.add_parser("list-modules", help="Lister les modules disponibles")
    list_parser.add_argument("--type", type=str, help="Type de module (simulator, enhancer, publisher, data_provider)")
    
    # Analyser les arguments
    args = parser.parse_args()
    
    # Configurer le niveau de log
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Initialiser TikSimPro
    tiksim = TikSimPro(args.config)
    
    # Exécuter la commande demandée
    if args.command == "generate":
        # Préparer les options
        options = {"simulator": {}}
        
        if args.duration:
            options["simulator"]["duration"] = args.duration
        if args.width:
            options["simulator"]["width"] = args.width
        if args.height:
            options["simulator"]["height"] = args.height
        if args.fps:
            options["simulator"]["fps"] = args.fps
        if args.output:
            options["simulator"]["output_path"] = args.output
        
        # Générer la vidéo
        video_path = tiksim.generate_video(options)
        if video_path:
            print(f"Vidéo générée: {video_path}")
        else:
            print("Erreur lors de la génération de la vidéo")
        
    elif args.command == "publish":
        # Publier la vidéo
        results = tiksim.publish_video(args.video, args.platforms)
        
        # Afficher les résultats
        for platform, success in results.items():
            status = "réussie" if success else "échouée"
            print(f"Publication sur {platform}: {status}")
        
    elif args.command == "generate-and-publish":
        # Préparer les options
        options = {}
        if args.duration:
            options["simulator"] = {"duration": args.duration}
        
        # Générer et publier
        video_path, results = tiksim.generate_and_publish(options, args.platforms)
        
        if video_path:
            print(f"Vidéo générée: {video_path}")
            
            # Afficher les résultats
            for platform, success in results.items():
                status = "réussie" if success else "échouée"
                print(f"Publication sur {platform}: {status}")
        else:
            print("Erreur lors de la génération de la vidéo")
        
    elif args.command == "schedule":
        # Planifier des publications
        tiksim.run_daily_schedule(args.times)
        
    elif args.command == "list-modules":
        # Lister les modules
        modules = tiksim.module_registry.list_available_modules(args.type)
        
        print("Modules disponibles:")
        for module_type, module_names in modules.items():
            print(f"\n{module_type.capitalize()}:")
            for name in module_names:
                print(f"  - {name}")
        
    elif args.command == "interactive" or not args.command:
        # Mode interactif
        show_interactive_menu(tiksim)
        
    else:
        print(f"Commande inconnue: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOpération annulée par l'utilisateur.")
    except Exception as e:
        logger.error(f"Erreur non gérée: {e}", exc_info=True)
        print(f"\nErreur: {e}")
        traceback.print_exc()