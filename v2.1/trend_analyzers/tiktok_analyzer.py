# trend_analyzers/tiktok_analyzer.py
"""
Analyseur de tendances TikTok
Récupère et analyse les tendances actuelles sur TikTok
"""

import os
import time
import json
import random
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

from core.interfaces import ITrendAnalyzer, TrendData

logger = logging.getLogger("TikSimPro")

class TikTokAnalyzer(ITrendAnalyzer):
    """
    Analyseur de tendances qui récupère et traite les données TikTok
    """
    
    def __init__(self, cache_dir: str = "trend_data"):
        """
        Initialise l'analyseur de tendances TikTok
        
        Args:
            cache_dir: Répertoire de cache pour les données
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Chemins des fichiers de cache
        self.trends_file = os.path.join(cache_dir, "trends.json")
        self.songs_file = os.path.join(cache_dir, "popular_songs.json")
        self.hashtags_file = os.path.join(cache_dir, "trending_hashtags.json")
        
        # Données en cache
        self._hashtags_cache = None
        self._music_cache = None
        self._trends_cache = None
        
        # Durée de validité du cache (24h)
        self.cache_duration = 86400
        
        logger.info(f"TikTokAnalyzer initialisé: {cache_dir}")
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """
        Vérifie si un fichier de cache est valide
        
        Args:
            cache_file: Chemin du fichier de cache
            
        Returns:
            True si le cache est valide, False sinon
        """
        if not os.path.exists(cache_file):
            return False
        
        # Vérifier l'âge du fichier
        file_age = time.time() - os.path.getmtime(cache_file)
        return file_age < self.cache_duration
    
    def _load_cache(self, cache_file: str) -> Optional[Any]:
        """
        Charge les données depuis un fichier de cache
        
        Args:
            cache_file: Chemin du fichier de cache
            
        Returns:
            Données chargées, ou None si le cache est invalide
        """
        if not self._is_cache_valid(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement du cache {cache_file}: {e}")
            return None
    
    def _save_cache(self, cache_file: str, data: Any) -> bool:
        """
        Sauvegarde des données dans un fichier de cache
        
        Args:
            cache_file: Chemin du fichier de cache
            data: Données à sauvegarder
            
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du cache {cache_file}: {e}")
            return False
    
    def _fetch_trending_hashtags(self) -> List[str]:
        """
        Récupère les hashtags tendance depuis l'API TikTok
        
        Returns:
            Liste de hashtags tendance
        """
        # Note: Dans une implémentation réelle, on appellerait l'API TikTok
        # Pour ce prototype, on simule des hashtags tendance
        
        logger.info("Récupération des hashtags tendance TikTok (simulation)")
        
        # Liste de hashtags populaires (fictifs pour la simulation)
        base_hashtags = [
            "fyp", "foryou", "viral", "trending", "tiktok",
            "dance", "funny", "comedy", "music", "art",
            "food", "fashion", "beauty", "fitness", "travel",
            "nature", "animals", "pets", "diy", "challenge",
            "satisfying", "asmr", "relaxing", "mindfulness", "positivity",
            "animation", "technology", "science", "education", "motivation"
        ]
        
        # Ajouter quelques hashtags aléatoires pour simuler les tendances changeantes
        current_trends = [
            f"trend{random.randint(1, 100)}",
            f"challenge{random.randint(1, 50)}",
            f"viral{random.randint(1, 30)}",
            f"new{random.randint(1, 20)}",
            f"popular{random.randint(1, 10)}"
        ]
        
        # Combiner et mélanger
        all_hashtags = base_hashtags + current_trends
        random.shuffle(all_hashtags)
        
        logger.info(f"{len(all_hashtags)} hashtags récupérés")
        return all_hashtags
    
    def _fetch_popular_music(self) -> List[Dict[str, Any]]:
        """
        Récupère les musiques populaires depuis l'API TikTok
        
        Returns:
            Liste de musiques populaires
        """
        # Note: Dans une implémentation réelle, on appellerait l'API TikTok
        # Pour ce prototype, on simule des musiques populaires
        
        logger.info("Récupération des musiques populaires TikTok (simulation)")
        
        # Liste de musiques populaires (fictives pour la simulation)
        popular_songs = [
            {
                "title": "STAY",
                "artist": "The Kid LAROI & Justin Bieber",
                "url": "https://example.com/stay.mp3"
            },
            {
                "title": "Industry Baby",
                "artist": "Lil Nas X & Jack Harlow",
                "url": "https://example.com/industry_baby.mp3"
            },
            {
                "title": "Fancy Like",
                "artist": "Walker Hayes",
                "url": "https://example.com/fancy_like.mp3"
            },
            {
                "title": "Bad Habits",
                "artist": "Ed Sheeran",
                "url": "https://example.com/bad_habits.mp3"
            },
            {
                "title": "good 4 u",
                "artist": "Olivia Rodrigo",
                "url": "https://example.com/good_4_u.mp3"
            },
            {
                "title": "Levitating",
                "artist": "Dua Lipa ft. DaBaby",
                "url": "https://example.com/levitating.mp3"
            },
            {
                "title": "MONTERO (Call Me By Your Name)",
                "artist": "Lil Nas X",
                "url": "https://example.com/montero.mp3"
            },
            {
                "title": "Save Your Tears",
                "artist": "The Weeknd & Ariana Grande",
                "url": "https://example.com/save_your_tears.mp3"
            },
            {
                "title": "Kiss Me More",
                "artist": "Doja Cat ft. SZA",
                "url": "https://example.com/kiss_me_more.mp3"
            },
            {
                "title": "Peaches",
                "artist": "Justin Bieber ft. Daniel Caesar & Giveon",
                "url": "https://example.com/peaches.mp3"
            }
        ]
        
        # Ajouter quelques informations aléatoires
        for song in popular_songs:
            song["popularity"] = random.randint(70, 100)
            song["duration"] = random.uniform(2.5, 4.0)
            song["bpm"] = random.randint(90, 150)
        
        logger.info(f"{len(popular_songs)} musiques récupérées")
        return popular_songs
    
    def _generate_trend_analysis(self) -> Dict[str, Any]:
        """
        Génère une analyse complète des tendances
        
        Returns:
            Dictionnaire d'analyse de tendances
        """
        logger.info("Génération de l'analyse des tendances TikTok")
        
        # Récupérer les hashtags et musiques
        hashtags = self.get_trending_hashtags()
        songs = self.get_popular_music()
        
        # Tendances de couleurs (palettes populaires sur TikTok)
        color_palettes = [
            ["#FF0050", "#00F2EA", "#FFFFFF", "#FE2C55"],  # Palette TikTok classique
            ["#25F4EE", "#FE2C55", "#FFFFFF", "#000000"],  # Palette TikTok alternative
            ["#F9CB9C", "#D5A6BD", "#B4A7D6", "#9FC5E8"],  # Palette pastel
            ["#FF5733", "#33FFC7", "#3386FF", "#FF33E0"],  # Palette vive
            ["#000000", "#FFFFFF", "#FF0050", "#00F2EA"]   # Palette contrastée
        ]
        
        # Fréquences de beat populaires
        beat_frequencies = [0.5, 0.6, 0.75, 1.0, 1.25]  # en secondes par beat
        
        # Durées de vidéo tendance
        durations = ["short", "medium", "long"]
        
        # Générer l'analyse
        analysis = {
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "popular_hashtags": hashtags[:10],
            "popular_music": [s["title"] for s in songs[:5]],
            "color_trends": {
                "dominant_palette": random.choice(color_palettes)
            },
            "timing_trends": {
                "duration_trend": random.choice(durations),
                "beat_frequency": random.choice(beat_frequencies)
            },
            "recommended_settings": {
                "video_duration": random.choice([30, 45, 60]),
                "beat_frequency": random.choice(beat_frequencies),
                "color_palette": random.choice(color_palettes),
                "recommended_hashtags": hashtags[:10],
                "visual_elements": ["text_overlay", "sound_effects", "transitions"]
            }
        }
        
        logger.info("Analyse des tendances générée")
        return analysis
    
    def get_trending_hashtags(self, limit: int = 30) -> List[str]:
        """
        Récupère les hashtags tendance
        
        Args:
            limit: Nombre maximum de hashtags à récupérer
            
        Returns:
            Liste de hashtags tendance
        """
        # Essayer de charger depuis le cache
        if not self._hashtags_cache:
            cached_hashtags = self._load_cache(self.hashtags_file)
            if cached_hashtags:
                self._hashtags_cache = cached_hashtags
                logger.info(f"Hashtags chargés depuis le cache: {len(cached_hashtags)}")
        
        # Si le cache est valide, l'utiliser
        if self._hashtags_cache:
            return self._hashtags_cache[:limit]
        
        # Sinon, récupérer de nouvelles données
        hashtags = self._fetch_trending_hashtags()
        
        # Sauvegarder dans le cache
        self._save_cache(self.hashtags_file, hashtags)
        self._hashtags_cache = hashtags
        
        return hashtags[:limit]
    
    def get_popular_music(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Récupère les musiques populaires
        
        Args:
            limit: Nombre maximum de musiques à récupérer
            
        Returns:
            Liste de musiques populaires avec métadonnées
        """
        # Essayer de charger depuis le cache
        if not self._music_cache:
            cached_music = self._load_cache(self.songs_file)
            if cached_music:
                self._music_cache = cached_music
                logger.info(f"Musiques chargées depuis le cache: {len(cached_music)}")
        
        # Si le cache est valide, l'utiliser
        if self._music_cache:
            return self._music_cache[:limit]
        
        # Sinon, récupérer de nouvelles données
        music = self._fetch_popular_music()
        
        # Sauvegarder dans le cache
        self._save_cache(self.songs_file, music)
        self._music_cache = music
        
        return music[:limit]
    
    def get_trend_analysis(self) -> TrendData:
        """
        Analyse les tendances actuelles
        
        Returns:
            Données de tendances complètes
        """
        # Essayer de charger depuis le cache
        if not self._trends_cache:
            cached_trends = self._load_cache(self.trends_file)
            if cached_trends:
                self._trends_cache = cached_trends
                logger.info("Analyse des tendances chargée depuis le cache")
        
        # Si le cache est valide, l'utiliser
        if self._trends_cache:
            return TrendData.from_dict(self._trends_cache)
        
        # Sinon, générer une nouvelle analyse
        analysis = self._generate_trend_analysis()
        
        # Sauvegarder dans le cache
        self._save_cache(self.trends_file, analysis)
        self._trends_cache = analysis
        
        return TrendData.from_dict(analysis)