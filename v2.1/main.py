#!/usr/bin/env python
# main.py
"""
Script principal pour TikSimPro
Permet de générer et publier des vidéos TikTok virales
"""

import os
import sys
import time
import logging
import argparse
import json
from typing import Dict, Any, Optional
from pathlib import Path

from core.config import Config

# Initialiser le logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tiksimpro.log')
    ]
)
logger = logging.getLogger("TikSimPro")

# Import des composants
from core.interfaces import (
    IPipeline, ITrendAnalyzer, IVideoGenerator, IAudioGenerator, 
    IMediaCombiner, IVideoEnhancer, IContentPublisher,
    TrendData, AudioEvent
)
from pipeline.content_pipeline import ContentPipeline
from core.plugin_manager import PluginManager

def setup_components(config: Config) -> Optional[ContentPipeline]:
    """
    Configure et initialise tous les composants du pipeline
    
    Args:
        config: Configuration à utiliser
        
    Returns:
        Pipeline configuré, ou None en cas d'erreur
    """
    try:
        plugin_dirs = ["trend_analyzers", "video_generators", "audio_generators", "media_combiner", "video_enhancers", "publishers"]
        manager = PluginManager(plugin_dirs)

        # Créer le pipeline
        pipeline = ContentPipeline()
        
        # Créer et configurer l'analyseur de tendances
        trend_analyzer = manager.get_plugin(config.get("trend_analyzer").get("name"), ITrendAnalyzer)
        pipeline.set_trend_analyzer(trend_analyzer(**config["trend_analyzer"]["params"]))

        # Créer et configurer le générateur de vidéo
        video_generator = manager.get_plugin(config.get("video_generator").get("name"), IVideoGenerator)
        pipeline.set_video_generator(video_generator(**config["video_generator"]["params"]))
        
        # Créer et configurer le générateur audio
        audio_generator = manager.get_plugin(config.get("audio_generator").get("name"), IAudioGenerator)
        pipeline.set_audio_generator(audio_generator(**config["audio_generator"]["params"]))
        
        # Créer et configurer le combineur de médias
        media_combiner = manager.get_plugin(config.get("media_combiner").get("name"), IMediaCombiner)
        pipeline.set_media_combiner(media_combiner(**config["media_combiner"]["params"]))
        
        # Créer et configurer l'améliorateur de vidéo
        video_enhancer = manager.get_plugin(config.get("video_enhancer").get("name"), IVideoEnhancer)
        pipeline.set_video_enhancer(video_enhancer(**config["video_enhancer"]["params"]))
        
        # Ajouter les systèmes de publication
        for platform, publisher_config in config["publishers"].items():
            if publisher_config.get("enabled", False):
                publisher = manager.get_plugin(publisher_config.get("name"), IContentPublisher)(**publisher_config["params"])
                pipeline.add_publisher(platform, publisher)
        
        pip = config.get("pipeline")
        # Configurer le pipeline
        pipeline_config = {
            "output_dir": pip.get("output_dir", "videos"),
            "auto_publish": pip.get("auto_publish", False),
            "platforms": [p for p, cfg in config["publishers"].items() if cfg.get("enabled", False)],
            "video_duration": pip.get("duration") if pip.get("duration") else config["video_generator"]["params"].get("duration", 30),
            "video_dimensions": (
                pip.get("width")[0] if pip.get("width") else config["video_generator"]["params"].get("width", 1080),
                pip.get("height")[0] if pip.get("height") else config["video_generator"]["params"].get("height", 1920)
            ),
            "fps": pip.get("fps") if pip.get("fps") else config["video_generator"]["params"].get("fps", 60)
        }
        pipeline.configure(pipeline_config)
        
        return pipeline
        
    except Exception as e:
        logger.error(f"Erreur lors de la configuration des composants: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_pipeline(pipeline: ContentPipeline) -> Optional[str]:
    """
    Exécute le pipeline de contenu
    
    Args:
        pipeline: Pipeline à exécuter
        
    Returns:
        Chemin de la vidéo générée, ou None en cas d'erreur
    """
    try:
        logger.info("Démarrage du pipeline de contenu...")
        start_time = time.time()
        
        # Exécuter le pipeline
        result_path = pipeline.execute()
        
        if not result_path:
            logger.error("Échec de l'exécution du pipeline")
            return None
        
        # Calculer le temps d'exécution
        elapsed_time = time.time() - start_time
        logger.info(f"Pipeline exécuté en {elapsed_time:.2f} secondes")
        logger.info(f"Vidéo générée: {result_path}")
        
        return result_path
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du pipeline: {e}")
        return None

def main():
    """Fonction principale"""
    # Analyser les arguments de la ligne de commande
    parser = argparse.ArgumentParser(description="TikSimPro - Générateur de contenu TikTok viral")
    parser.add_argument("--config", "-c", type=str, default="config.json", help="Fichier de configuration")
    parser.add_argument("--output", "-o", type=str, help="Répertoire de sortie")
    parser.add_argument("--duration", "-d", type=int, help="Durée de la vidéo en secondes")
    parser.add_argument("--resolution", "-r", type=str, help="Résolution de la vidéo (largeur:hauteur)")
    parser.add_argument("--publish", "-p", action="store_true", help="Publier automatiquement")
    parser.add_argument("--init", "-i", action="store_true", help="Initialiser la configuration par défaut")
    args = parser.parse_args()
    
    # Afficher une bannière
    print("\n" + "="*80)
    print("          TikSimPro - Générateur de contenu TikTok viral")
    print("="*80 + "\n")

    # Initialiser la configuration par défaut si demandé
    if args.init:
        config = Config(args.config)
        config.save_config(config)
        print(f"Configuration par défaut créée dans {args.config}")
        return
    
    # Charger la configuration
    if not os.path.exists(args.config):
        print(f"Le fichier de configuration {args.config} n'existe pas.")
        print("Utilisez --init pour créer une configuration par défaut.")
        return
    print(args.config)
    config = Config(args.config).load_config()
    
    # Appliquer les arguments de ligne de commande
    if args.output:
        config["output_dir"] = args.output
    
    if args.duration:
        config["simulator"]["params"]["duration"] = args.duration
    
    if args.resolution:
        try:
            width, height = map(int, args.resolution.split(":"))
            config["simulator"]["params"]["width"] = width
            config["simulator"]["params"]["height"] = height
        except:
            logger.error(f"Format de résolution invalide: {args.resolution}")
    
    if args.publish:
        config["auto_publish"] = True
    
    # Configurer et exécuter le pipeline
    pipeline = setup_components(config)
    if pipeline:
        result_path = run_pipeline(pipeline)
        
        if result_path:
            print("\nTraitement terminé avec succès!")
            print(f"Vidéo générée: {result_path}")
            
            if config.get("auto_publish", False):
                print("La vidéo a été publiée sur les plateformes configurées.")
            else:
                print("La vidéo n'a pas été publiée (auto_publish=False).")
        else:
            print("\nÉchec du traitement. Consultez les logs pour plus d'informations.")
    else:
        print("\nImpossible de configurer le pipeline. Consultez les logs pour plus d'informations.")

if __name__ == "__main__":
    main()