# pipeline/content_pipeline.py
"""
Pipeline central pour le système TikSimPro
Coordonne tous les composants pour générer et publier du contenu viral
"""

import os
import time
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
import random
from pathlib import Path

from core.interfaces import (
    IPipeline, ITrendAnalyzer, IVideoGenerator, IAudioGenerator, 
    IMediaCombiner, IVideoEnhancer, IContentPublisher,
    TrendData, AudioEvent, VideoMetadata
)

logger = logging.getLogger("TikSimPro")

class ContentPipeline(IPipeline):
    """
    Pipeline complet pour la génération et publication de contenu viral
    """
    
    def __init__(self):
        """Initialise le pipeline de contenu"""
        # Configuration par défaut
        self.config = {
            "output_dir": "output",
            "temp_dir": "temp",
            "auto_publish": False,
            "platforms": ["tiktok"],
            "video_duration": 30,
            "video_dimensions": (1080, 1920),  # Format portrait pour TikTok
            "fps": 60
        }
        
        # Composants du pipeline
        self.trend_analyzer = None
        self.video_generator = None
        self.audio_generator = None
        self.media_combiner = None
        self.video_enhancer = None
        self.publishers = {}
        
        # Chemins des fichiers générés
        self.video_path = None
        self.audio_path = None
        self.combined_path = None
        self.enhanced_path = None
        
        # Métadonnées et événements
        self.trend_data = None
        self.audio_events = []
        
        # Créer les répertoires nécessaires
        self._create_directories()
        
        logger.info("ContentPipeline initialisé")
    
    def _create_directories(self) -> None:
        """Crée les répertoires nécessaires"""
        os.makedirs(self.config["output_dir"], exist_ok=True)
        os.makedirs(self.config["temp_dir"], exist_ok=True)
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure le pipeline avec des paramètres spécifiques
        
        Args:
            config: Paramètres de configuration
            
        Returns:
            True si la configuration a réussi, False sinon
        """
        try:
            # Mettre à jour la configuration
            for key, value in config.items():
                if key in self.config:
                    self.config[key] = value
            
            # Créer les répertoires nécessaires
            self._create_directories()
            
            # Configurer les composants si fournis
            if "trend_analyzer" in config:
                self.set_trend_analyzer(config["trend_analyzer"])
            
            if "video_generator" in config:
                self.set_video_generator(config["video_generator"])
            
            if "audio_generator" in config:
                self.set_audio_generator(config["audio_generator"])
            
            if "media_combiner" in config:
                self.set_media_combiner(config["media_combiner"])
            
            if "video_enhancer" in config:
                self.set_video_enhancer(config["video_enhancer"])
            
            if "publishers" in config:
                for platform, publisher in config["publishers"].items():
                    self.add_publisher(platform, publisher)
            
            logger.info("Pipeline configuré avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du pipeline: {e}")
            return False
    
    def set_trend_analyzer(self, analyzer: ITrendAnalyzer) -> None:
        """
        Définit l'analyseur de tendances
        
        Args:
            analyzer: Instance de ITrendAnalyzer
        """
        self.trend_analyzer = analyzer
        logger.info(f"Analyseur de tendances défini: {analyzer.__class__.__name__}")
    
    def set_video_generator(self, generator: IVideoGenerator) -> None:
        """
        Définit le générateur de vidéo
        
        Args:
            generator: Instance de IVideoGenerator
        """
        self.video_generator = generator
        logger.info(f"Générateur de vidéo défini: {generator.__class__.__name__}")
    
    def set_audio_generator(self, generator: IAudioGenerator) -> None:
        """
        Définit le générateur audio
        
        Args:
            generator: Instance de IAudioGenerator
        """
        self.audio_generator = generator
        logger.info(f"Générateur audio défini: {generator.__class__.__name__}")
    
    def set_media_combiner(self, combiner: IMediaCombiner) -> None:
        """
        Définit le combineur de médias
        
        Args:
            combiner: Instance de IMediaCombiner
        """
        self.media_combiner = combiner
        logger.info(f"Combineur de médias défini: {combiner.__class__.__name__}")
    
    def set_video_enhancer(self, enhancer: IVideoEnhancer) -> None:
        """
        Définit l'améliorateur de vidéo
        
        Args:
            enhancer: Instance de IVideoEnhancer
        """
        self.video_enhancer = enhancer
        logger.info(f"Améliorateur de vidéo défini: {enhancer.__class__.__name__}")
    
    def add_publisher(self, platform: str, publisher: IContentPublisher) -> None:
        """
        Ajoute un système de publication pour une plateforme
        
        Args:
            platform: Nom de la plateforme
            publisher: Instance de IContentPublisher
        """
        self.publishers[platform] = publisher
        logger.info(f"Système de publication ajouté pour {platform}: {publisher.__class__.__name__}")
    
    def _generate_filenames(self) -> None:
        """Génère des noms de fichiers uniques pour les différentes étapes"""
        timestamp = int(time.time())
        
        # Répertoire temporaire pour les fichiers intermédiaires
        temp_dir = self.config["temp_dir"]
        
        # Répertoire de sortie pour les fichiers finaux
        output_dir = self.config["output_dir"]
        
        # Chemins des fichiers
        self.video_path = os.path.join(temp_dir, f"video_{timestamp}.mp4")
        self.audio_path = os.path.join(temp_dir, f"audio_{timestamp}.wav")
        self.combined_path = os.path.join(temp_dir, f"combined_{timestamp}.mp4")
        self.enhanced_path = os.path.join(output_dir, f"final_{timestamp}.mp4")
        
        logger.info(f"Fichiers générés: {self.enhanced_path}")
    
    def _analyze_trends(self) -> Optional[TrendData]:
        """
        Analyse les tendances actuelles
        
        Returns:
            Données de tendances, ou None en cas d'erreur
        """
        if not self.trend_analyzer:
            logger.error("Aucun analyseur de tendances défini")
            return None
        
        try:
            logger.info("Analyse des tendances en cours...")
            trend_data = self.trend_analyzer.get_trend_analysis()
            logger.info("Analyse des tendances terminée")
            return trend_data
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des tendances: {e}")
            return None
    
    def _generate_video(self) -> Optional[str]:
        """
        Génère la vidéo de base
        
        Returns:
            Chemin de la vidéo générée, ou None en cas d'erreur
        """
        if not self.video_generator:
            logger.error("Aucun générateur de vidéo défini")
            return None
        
        if not self.trend_data:
            logger.error("Aucune donnée de tendance disponible")
            return None
        
        try:
            # Configurer le générateur
            logger.info("Configuration du générateur de vidéo...")
            width, height = self.config["video_dimensions"]
            self.video_generator.configure({
                "width": width,
                "height": height,
                "fps": self.config["fps"],
                "duration": self.config["video_duration"]
            })
            
            # Définir le chemin de sortie
            self.video_generator.set_output_path(self.video_path)
            
            # Appliquer les données de tendances
            self.video_generator.apply_trend_data(self.trend_data)
            
            # Générer la vidéo
            logger.info("Génération de la vidéo en cours...")
            video_path = self.video_generator.generate()
            
            if not video_path:
                logger.error("Échec de la génération vidéo")
                return None
            
            # Récupérer les événements audio
            self.audio_events = self.video_generator.get_audio_events()
            logger.info(f"{len(self.audio_events)} événements audio collectés")
            
            return video_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la vidéo: {e}")
            return None
    
    def _generate_audio(self) -> Optional[str]:
        """
        Génère la piste audio
        
        Returns:
            Chemin de la piste audio générée, ou None en cas d'erreur
        """
        if not self.audio_generator:
            logger.error("Aucun générateur audio défini")
            return None
        
        if not self.trend_data:
            logger.error("Aucune donnée de tendance disponible")
            return None
        
        try:
            # Configurer le générateur
            logger.info("Configuration du générateur audio...")
            self.audio_generator.configure({
                "sample_rate": 44100,
                "duration": self.config["video_duration"]
            })
            
            # Définir le chemin de sortie
            self.audio_generator.set_output_path(self.audio_path)
            
            # Définir la durée
            self.audio_generator.set_duration(self.config["video_duration"])
            
            # Appliquer les données de tendances
            self.audio_generator.apply_trend_data(self.trend_data)
            
            # Ajouter les événements audio
            if self.audio_events:
                self.audio_generator.add_events(self.audio_events)
            
            # Générer la piste audio
            logger.info("Génération de la piste audio en cours...")
            audio_path = self.audio_generator.generate()
            
            if not audio_path:
                logger.error("Échec de la génération audio")
                return None
            
            return audio_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la piste audio: {e}")
            return None
    
    def _combine_media(self) -> Optional[str]:
        """
        Combine la vidéo et la piste audio
        
        Returns:
            Chemin de la vidéo combinée, ou None en cas d'erreur
        """
        if not self.media_combiner:
            logger.error("Aucun combineur de médias défini")
            return None
        
        if not self.video_path or not os.path.exists(self.video_path):
            logger.error(f"Fichier vidéo non trouvé: {self.video_path}")
            return None
        
        if not self.audio_path or not os.path.exists(self.audio_path):
            logger.error(f"Fichier audio non trouvé: {self.audio_path}")
            return None
        
        try:
            # Combiner la vidéo et l'audio
            logger.info("Combinaison de la vidéo et de l'audio en cours...")
            combined_path = self.media_combiner.combine(
                self.video_path,
                self.audio_path,
                self.combined_path
            )
            
            if not combined_path:
                logger.error("Échec de la combinaison des médias")
                return None
            
            return combined_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la combinaison des médias: {e}")
            return None
    
    def _enhance_video(self) -> Optional[str]:
        """
        Améliore la vidéo avec des effets visuels et textuels
        
        Returns:
            Chemin de la vidéo améliorée, ou None en cas d'erreur
        """
        if not self.video_enhancer:
            logger.error("Aucun améliorateur de vidéo défini")
            return None
        
        if not self.combined_path or not os.path.exists(self.combined_path):
            logger.error(f"Fichier vidéo combiné non trouvé: {self.combined_path}")
            return None
        
        try:
            # Préparer les options d'amélioration
            hashtags = self.trend_data.popular_hashtags if self.trend_data else ["fyp", "viral", "foryou"]
            
            enhance_options = {
                "add_intro": True,
                "add_hashtags": True,
                "add_cta": True,
                "intro_text": "Watch this to the end! 👀",
                "hashtags": hashtags[:8],  # Limiter à 8 hashtags
                "cta_text": "Follow for more! 👆"
            }
            
            # Améliorer la vidéo
            logger.info("Amélioration de la vidéo en cours...")
            enhanced_path = self.video_enhancer.enhance(
                self.combined_path,
                self.enhanced_path,
                enhance_options
            )
            
            if not enhanced_path:
                logger.error("Échec de l'amélioration de la vidéo")
                return None
            
            return enhanced_path
            
        except Exception as e:
            logger.error(f"Erreur lors de l'amélioration de la vidéo: {e}")
            return None
    
    def _publish_content(self, video_path: str) -> Dict[str, bool]:
        """
        Publie la vidéo sur les plateformes configurées
        
        Args:
            video_path: Chemin de la vidéo à publier
            
        Returns:
            Dictionnaire {plateforme: succès}
        """
        if not self.publishers:
            logger.error("Aucun système de publication défini")
            return {}
        
        if not video_path or not os.path.exists(video_path):
            logger.error(f"Fichier vidéo non trouvé: {video_path}")
            return {}
        
        # Plateformes à utiliser
        platforms = self.config.get("platforms", list(self.publishers.keys()))
        print(platforms)
        # Résultats de publication
        results = {}
        
        # Préparer la légende et les hashtags
        captions = [
            "This simulation is so satisfying!",
            "Watch till the end for a surprise!",
            "I could watch this all day!",
            "The physics in this are incredible!",
            "Turn on the sound!"
        ]
        caption = random.choice(captions)
        
        hashtags = self.trend_data.popular_hashtags[:10] if self.trend_data else ["fyp", "viral", "foryou", "trending"]
        
        # Publier sur chaque plateforme
        for platform in platforms:
            if platform not in self.publishers:
                logger.warning(f"Aucun système de publication disponible pour {platform}")
                results[platform] = False
                continue
            
            publisher = self.publishers[platform]
            
            try:
                # Authentifier si nécessaire
                if not publisher.authenticate():
                    logger.error(f"Échec de l'authentification sur {platform}")
                    results[platform] = False
                    continue
                
                # Publier la vidéo
                logger.info(f"Publication sur {platform} en cours...")
                
                # Paramètres spécifiques à la plateforme
                kwargs = {}
                if platform == "youtube":
                    kwargs["title"] = f"Satisfying Physics Simulation - {time.strftime('%Y-%m-%d')}"
                
                success = publisher.publish(
                    video_path=video_path,
                    caption=caption,
                    hashtags=hashtags,
                    **kwargs
                )
                
                results[platform] = success
                logger.info(f"Publication sur {platform}: {'réussie' if success else 'échouée'}")
                
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur {platform}: {e}")
                results[platform] = False
        
        return results
    
    def execute(self) -> Optional[str]:
        """
        Exécute le pipeline complet
        
        Returns:
            Chemin du résultat final, ou None en cas d'échec
        """
        logger.info("Démarrage du pipeline de contenu...")
        
        # 1. Générer des noms de fichiers uniques
        self._generate_filenames()
        
        # 2. Analyser les tendances
        logger.info("Étape 1/6: Analyse des tendances...")
        self.trend_data = self._analyze_trends()
        if not self.trend_data:
            logger.error("Échec de l'analyse des tendances")
            return None
        
        # 3. Générer la vidéo
        logger.info("Étape 2/6: Génération de la vidéo...")
        video_path = self._generate_video()
        if not video_path:
            logger.error("Échec de la génération vidéo")
            return None
        
        # 4. Générer la piste audio
        logger.info("Étape 3/6: Génération de la piste audio...")
        audio_path = self._generate_audio()
        if not audio_path:
            logger.error("Échec de la génération audio")
            # Continuer avec la vidéo sans son
            self.combined_path = self.video_path
        else:
            # 5. Combiner la vidéo et l'audio
            logger.info("Étape 4/6: Combinaison des médias...")
            combined_path = self._combine_media()
            if not combined_path:
                logger.error("Échec de la combinaison des médias")
                # Continuer avec la vidéo sans son
                self.combined_path = self.video_path
        
        # 6. Améliorer la vidéo
        logger.info("Étape 5/6: Amélioration de la vidéo...")
        enhanced_path = self._enhance_video()
        if not enhanced_path:
            logger.error("Échec de l'amélioration de la vidéo")
            # Utiliser la vidéo combinée non améliorée
            enhanced_path = self.combined_path
        
        # 7. Publier le contenu si demandé
        if self.config.get("auto_publish", False):
            logger.info("Étape 6/6: Publication du contenu...")
            results = self._publish_content(enhanced_path)
            
            # Afficher le résumé
            logger.info("Résumé de la publication:")
            for platform, success in results.items():
                status = "réussie" if success else "échouée"
                logger.info(f"- {platform}: {status}")
        else:
            logger.info("Publication automatique désactivée")
        
        logger.info(f"Pipeline terminé avec succès: {enhanced_path}")
        return enhanced_path