# trend_analyzers/tiktok_analyzer.py
"""
Analyseur de tendances TikTok avancé avec recherche en ligne
Récupère et analyse les tendances actuelles en combinant données web et simulations
"""

import os
import time
import json
import random
import logging
import requests
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import hashlib
import re
import threading
from queue import Queue
import sys

# Assure que le dossier parent est dans le path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import ITrendAnalyzer, TrendData

# Import pour Selenium et BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("BeautifulSoup non disponible, certaines fonctionnalités de parsing seront limitées")

logger = logging.getLogger("TikSimPro")

from connectors.tiktok_ads_connector import TikTokAdsConnector

class TikTokAnalyzer(ITrendAnalyzer):
    """
    Analyseur de tendances qui récupère et traite les données TikTok
    en utilisant une approche hybride: recherche web + simulation
    """
    
    def __init__(self, cache_dir: str = "trend_data", 
                 cache_duration: int = 86400,  # 24 heures par défaut
                 region: str = "global",
                 use_web_search: bool = True,
                 headless: bool = True,
                 description: Optional[str] = None,
                 hashtags: Optional[List[str]] = None,
                 music_title: Optional[str] = None,
                 music_artist: Optional[str] = None,
                 color_palette: Optional[List[str]] = None):
        """
        Initialise l'analyseur de tendances TikTok
        
        Args:
            cache_dir: Répertoire de cache pour les données
            cache_duration: Durée de validité du cache en secondes
            region: Région pour les tendances (global, us, eu, asia, etc.)
            use_web_search: Si True, utilise Selenium pour chercher des tendances en ligne
            headless: Exécuter le navigateur en mode headless
            description: Description ou thème de la vidéo souhaitée (optionnel)
            hashtags: Liste de hashtags spécifiques à utiliser (optionnel)
            music_title: Titre de la musique à utiliser (optionnel)
            music_artist: Artiste de la musique à utiliser (optionnel)
            color_palette: Palette de couleurs personnalisée (optionnel)
        """
        self.cache_dir = cache_dir
        self.cache_duration = cache_duration
        self.region = region
        self.use_web_search = use_web_search
        
        # Paramètres utilisateur
        self.user_description = description
        self.user_hashtags = hashtags
        self.user_music_title = music_title
        self.user_music_artist = music_artist
        self.user_color_palette = color_palette
        
        # Créer le répertoire de cache s'il n'existe pas
        os.makedirs(cache_dir, exist_ok=True)
        
        # Chemins des fichiers de cache
        self.trends_file = os.path.join(cache_dir, f"trends_{region}.json")
        self.songs_file = os.path.join(cache_dir, f"popular_songs_{region}.json")
        self.hashtags_file = os.path.join(cache_dir, f"trending_hashtags_{region}.json")
        self.colors_file = os.path.join(cache_dir, f"color_trends_{region}.json")
        
        # Données en cache
        self._hashtags_cache = None
        self._music_cache = None
        self._trends_cache = None
        self._colors_cache = None
        
        # Données saisonnières pour plus de réalisme
        self._month = datetime.now().month
        self._season = self._get_current_season()
        
        # Extraire des mots-clés à partir de la description si fournie
        self._extracted_keywords = self._extract_keywords_from_description() if description else []
        
        # Connecteur TikTok
        self.connector = TikTokAdsConnector(headless=headless) if use_web_search else None
        
        # Données extraites du web
        self._web_hashtags = None
        self._web_music = None
        self._web_colors = None
        
        # Base de données de hashtags par catégorie (fallback)
        self._hashtag_categories = {
            "general": ["fyp", "foryou", "viral", "trending", "tiktok", "meme", "viralvideo", "trending", "explore"],
            "dance": ["dance", "dancechallenge", "dancer", "dancing", "choreography", "moves"],
            "comedy": ["funny", "comedy", "humor", "joke", "comedyvideos", "laugh", "lol", "funnyvideos"],
            "beauty": ["beauty", "makeup", "skincare", "hair", "nails", "glam", "selfcare", "transformation"],
            "fitness": ["fitness", "workout", "gym", "exercise", "fit", "healthy", "weightloss", "bodybuilding"],
            "food": ["food", "recipe", "cooking", "tasty", "foodie", "chef", "homemade", "baking"],
            "fashion": ["fashion", "outfit", "style", "ootd", "clothes", "look", "aesthetic", "streetwear"],
            "travel": ["travel", "adventure", "traveling", "vacation", "explore", "wanderlust", "journey", "tourist"],
            "pet": ["pet", "dog", "cat", "puppy", "kitten", "animal", "cute", "adorable", "animals"],
            "diy": ["diy", "crafts", "homemade", "create", "art", "project", "handmade", "creative"],
            "gaming": ["gaming", "gamer", "videogames", "game", "ps5", "xbox", "nintendo", "streamer"],
            "music": ["music", "song", "singer", "musician", "artist", "rap", "pop", "singersoftiktok"],
            "tech": ["tech", "technology", "gadget", "coding", "programmer", "computer", "apple", "android"],
            "asmr": ["asmr", "satisfying", "oddlysatisfying", "relaxing", "calming", "tingles", "slime"],
            "education": ["learn", "education", "facts", "history", "science", "knowledge", "interesting", "educational"],
            "motivation": ["motivation", "success", "inspire", "hustle", "quote", "grind", "positivity", "mindset"],
            "business": ["business", "entrepreneur", "money", "finance", "investing", "success", "startup", "passive"],
            "seasonal": {
                "spring": ["spring", "flowers", "garden", "bloom", "springvibes", "allergies", "spring2025"],
                "summer": ["summer", "beach", "pool", "vacation", "summervibes", "tan", "bikini", "summertime"],
                "fall": ["fall", "autumn", "pumpkin", "halloween", "spooky", "cozy", "fallvibes", "leaves"],
                "winter": ["winter", "snow", "christmas", "cold", "wintervibes", "holiday", "newyear", "cozy"]
            },
            "holidays": {
                "1": ["newyear", "resolution", "january", "newyear2025", "winter", "freshstart"],
                "2": ["valentines", "love", "february", "valentinesday", "couple", "date", "romantic"],
                "3": ["stpatricks", "green", "march", "spring", "lucky", "shamrock", "irish"],
                "4": ["easter", "spring", "april", "bunny", "eggs", "pastel", "springbreak"],
                "5": ["cincodemayo", "mothersday", "may", "spring", "mom", "mother", "momlife"],
                "6": ["pride", "summer", "june", "pridemonth", "love", "equality", "rainbow"],
                "7": ["july4th", "independence", "july", "summer", "fireworks", "america", "patriotic"],
                "8": ["backtoschool", "summer", "august", "vacation", "school", "college", "student"],
                "9": ["laborday", "fall", "september", "autumn", "backtoschool", "work", "longweekend"],
                "10": ["halloween", "spooky", "october", "costume", "pumpkin", "scary", "trickortreat"],
                "11": ["thanksgiving", "grateful", "november", "turkey", "family", "thankful", "fall"],
                "12": ["christmas", "holiday", "december", "santa", "snow", "winter", "newyear"]
            }
        }
        
        # Base de données de musiques populaires (fallback)
        self._popular_artists = [
            "Drake", "Taylor Swift", "BTS", "Dua Lipa", "Bad Bunny", "The Weeknd", "Harry Styles", 
            "Billie Eilish", "Ariana Grande", "Ed Sheeran", "Justin Bieber", "Olivia Rodrigo", 
            "Doja Cat", "Post Malone", "Travis Scott", "Cardi B", "Megan Thee Stallion", "Lil Nas X"
        ]
        
        self._music_genres = [
            "Pop", "Hip-Hop", "Rap", "R&B", "EDM", "K-Pop", "Latin", "Rock", "Indie", 
            "Alternative", "Dance", "Electronic", "Country", "Jazz", "Classical"
        ]
        
        # Base de données de palettes de couleurs tendance (fallback)
        self._color_palettes = {
            "tiktok_default": ["#FF0050", "#00F2EA", "#FFFFFF", "#FE2C55", "#25F4EE"],
            "vibrant": ["#FF5733", "#33FFC7", "#3386FF", "#FF33E0", "#F3FF33"],
            "pastel": ["#F9CB9C", "#D5A6BD", "#B4A7D6", "#9FC5E8", "#A2C4C9"],
            "monochrome": ["#000000", "#333333", "#666666", "#999999", "#FFFFFF"],
            "retro": ["#FFDF6B", "#FF9E6B", "#FF6B6B", "#FF6BB5", "#6B95FF"],
            "earthy": ["#A0522D", "#6B8E23", "#BDB76B", "#F5DEB3", "#8B4513"],
            "neon": ["#FF00FF", "#00FFFF", "#FF0000", "#00FF00", "#0000FF"],
            "seasonal": {
                "spring": ["#76d275", "#a0ddff", "#ffde59", "#ffafcc", "#c1ff9b"],
                "summer": ["#ff7e67", "#ffcb8e", "#7fffd4", "#00bfff", "#ffeb3b"],
                "fall": ["#b34700", "#ff8c19", "#a35638", "#bf9270", "#dabb94"],
                "winter": ["#ecf0f1", "#34495e", "#9ac1d9", "#286fb4", "#0a2351"]
            },
            "trending2025": ["#222831", "#00ADB5", "#EEEEEE", "#FF2E63", "#252A34"]
        }
        
        # Lancer la recherche web en arrière-plan
        if self.use_web_search and self.connector:
            self._start_web_search()
        
        logger.info(f"TikTokAnalyzer initialisé: {cache_dir}, région: {region}, web search: {use_web_search}")
    
    def _extract_keywords_from_description(self) -> List[str]:
        """
        Extrait des mots-clés pertinents de la description fournie
        
        Returns:
            Liste de mots-clés extraits
        """
        if not self.user_description:
            return []
            
        # Liste de mots vides à ignorer
        stopwords = [
            "a", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", 
            "about", "from", "of", "is", "are", "was", "were", "be", "being", "been",
            "have", "has", "had", "do", "does", "did", "will", "would", "shall", "should",
            "can", "could", "may", "might", "must", "i", "you", "he", "she", "it", "we", "they"
        ]
        
        # Découper la description en mots
        words = self.user_description.lower().replace(".", " ").replace(",", " ").replace("!", " ").replace("?", " ").split()
        
        # Filtrer les mots vides et les mots trop courts
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        # Éliminer les doublons
        unique_keywords = list(set(keywords))
        
        # Limiter à 10 mots-clés maximum
        return unique_keywords[:10]
    
    def _start_web_search(self):
        """Lance les recherches web en arrière-plan"""
        def web_search_worker():
            """Fonction de travail pour le thread de recherche web"""
            try:
                # Configurer le navigateur si nécessaire
                if self.connector._setup_browser():
                    # Rechercher les hashtags
                    self._web_hashtags = self.connector.search_trending_hashtags()
                    
                    # Rechercher les musiques
                    self._web_music = self.connector.search_popular_music()
                    
                    # Extraire les couleurs
                    self._web_colors = self.connector.extract_color_trends()
                    
                    # Fermer le navigateur
                    self.connector.close()
                    
                    logger.info("Recherche web des tendances terminée")
            except Exception as e:
                logger.error(f"Erreur dans le thread de recherche web: {e}")
        
        # Démarrer le thread en arrière-plan
        thread = threading.Thread(target=web_search_worker, daemon=True)
        thread.start()
    
    def _get_current_season(self) -> str:
        """
        Détermine la saison actuelle en fonction du mois
        
        Returns:
            Saison actuelle (spring, summer, fall, winter)
        """
        month = self._month
        if 3 <= month <= 5:
            return "spring"
        elif 6 <= month <= 8:
            return "summer"
        elif 9 <= month <= 11:
            return "fall"
        else:
            return "winter"
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """
        Vérifie si un fichier de cache est valide
        
        Args:
            cache_file: Chemin du fichier de cache
            
        Returns:
            True si le cache est valide, False sinon
        """
        # Si des paramètres utilisateur sont fournis, ne pas utiliser le cache
        if (self.user_description or self.user_hashtags or 
            self.user_music_title or self.user_music_artist or 
            self.user_color_palette):
            return False
            
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
        # Ne pas sauvegarder les données personnalisées
        if (self.user_description or self.user_hashtags or 
            self.user_music_title or self.user_music_artist or 
            self.user_color_palette):
            return False
            
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du cache {cache_file}: {e}")
            return False
    
    def _generate_consistent_seed(self, base_value: str) -> int:
        """
        Génère une graine aléatoire cohérente basée sur une chaîne
        
        Args:
            base_value: Valeur de base pour la graine
            
        Returns:
            Graine entière
        """
        # Générer un hash de la chaîne pour avoir un nombre cohérent
        hash_value = hashlib.md5(base_value.encode()).hexdigest()
        # Convertir les 8 premiers caractères en entier
        return int(hash_value[:8], 16)
    
    def _get_trending_challenges(self) -> List[str]:
        """
        Génère des défis tendance
        
        Returns:
            Liste de défis tendance
        """
        base_challenges = [
            "dance", "lipsync", "transition", "duet", "pov", "outfit", "makeup", "comedy",
            "acting", "talent", "magic", "cooking", "transformation", "challenge"
        ]
        
        # Challenges spécifiques
        specific_challenges = [
            f"{random.choice(['viral', 'trending', 'new', 'famous'])}dance{random.randint(1, 100)}",
            f"the{random.choice(['box', 'cup', 'bottle', 'chair', 'flip', 'drop'])}challenge",
            f"{random.choice(['savage', 'renegade', 'woah', 'shuffle', 'moonwalk'])}2025",
            f"{random.choice(self._popular_artists).lower().replace(' ', '')}challenge"
        ]
        
        # Intégrer les mots-clés de la description si disponibles
        if self._extracted_keywords:
            for keyword in self._extracted_keywords[:3]:  # Limiter à 3 mots-clés
                specific_challenges.append(f"{keyword}challenge")
        
        # Combiner et mélanger
        trending_challenges = base_challenges + specific_challenges
        random.shuffle(trending_challenges)
        
        return trending_challenges
    
    def _fetch_trending_hashtags(self) -> List[str]:
        """
        Récupère les hashtags tendance depuis l'API TikTok ou par simulation
        
        Returns:
            Liste de hashtags tendance
        """
        # Si des hashtags ont été fournis par l'utilisateur, les utiliser comme base
        if self.user_hashtags:
            logger.info(f"Utilisation des hashtags fournis par l'utilisateur: {len(self.user_hashtags)}")
            base_hashtags = self.user_hashtags.copy()
            
            # Compléter avec les hashtags généraux toujours utiles
            general_tags = self._hashtag_categories["general"]
            for tag in general_tags:
                if tag.lower() not in [t.lower() for t in base_hashtags]:
                    base_hashtags.append(tag)
            
            # Ajouter quelques hashtags saisonniers
            season_tags = self._hashtag_categories["seasonal"][self._season]
            for tag in random.sample(season_tags, min(3, len(season_tags))):
                if tag.lower() not in [t.lower() for t in base_hashtags]:
                    base_hashtags.append(tag)
            
            # Mélanger les hashtags
            random.shuffle(base_hashtags)
            
            return base_hashtags
        
        # Si des hashtags ont été récupérés du web, les utiliser
        if self._web_hashtags:
            logger.info(f"Utilisation des hashtags récupérés du web: {len(self._web_hashtags)}")
            web_hashtags = self._web_hashtags.copy()
            
            # Ajouter quelques hashtags généraux et saisonniers
            general_tags = random.sample(self._hashtag_categories["general"], min(5, len(self._hashtag_categories["general"])))
            season_tags = random.sample(self._hashtag_categories["seasonal"][self._season], min(3, len(self._hashtag_categories["seasonal"][self._season])))
            
            # Combiner tous les hashtags
            all_hashtags = web_hashtags + general_tags + season_tags
            
            # Éliminer les doublons
            unique_hashtags = []
            seen = set()
            for tag in all_hashtags:
                if tag.lower() not in seen:
                    unique_hashtags.append(tag)
                    seen.add(tag.lower())
            
            # Mélanger les hashtags
            random.shuffle(unique_hashtags)
            
            return unique_hashtags
        
        # Sinon, générer des hashtags simulés
        logger.info("Génération des hashtags tendance par simulation")
        
        # Définir une graine pour avoir des résultats cohérents
        seed = self._generate_consistent_seed(f"hashtags_{self.region}_{datetime.now().strftime('%Y-%m-%d')}")
        random.seed(seed)
        
        # Liste de base par catégorie
        all_hashtags = []
        
        # Ajouter des hashtags généraux (toujours présents)
        all_hashtags.extend(random.sample(self._hashtag_categories["general"], k=min(10, len(self._hashtag_categories["general"]))))
        
        # Ajouter des hashtags saisonniers
        season_hashtags = self._hashtag_categories["seasonal"][self._season]
        all_hashtags.extend(random.sample(season_hashtags, k=min(5, len(season_hashtags))))
        
        # Ajouter des hashtags liés au mois actuel
        month_str = str(self._month)
        if month_str in self._hashtag_categories["holidays"]:
            holiday_hashtags = self._hashtag_categories["holidays"][month_str]
            all_hashtags.extend(random.sample(holiday_hashtags, k=min(5, len(holiday_hashtags))))
        
        # Ajouter des hashtags de diverses catégories
        categories = list(self._hashtag_categories.keys())
        categories = [c for c in categories if c not in ["general", "seasonal", "holidays"]]
        
        # Sélectionner des catégories aléatoires
        selected_categories = random.sample(categories, k=min(10, len(categories)))
        
        for category in selected_categories:
            hashtags = self._hashtag_categories[category]
            # Prendre 2-5 hashtags de chaque catégorie
            num_from_category = random.randint(2, 5)
            all_hashtags.extend(random.sample(hashtags, k=min(num_from_category, len(hashtags))))
        
        # Ajouter des défis tendance
        trending_challenges = self._get_trending_challenges()
        all_hashtags.extend(trending_challenges[:5])  # Prendre les 5 premiers défis
        
        # Ajouter des hashtags avec des nombres pour l'année et des variations
        current_year = datetime.now().year
        all_hashtags.extend([
            f"trend{current_year}",
            f"viral{current_year}",
            f"tiktok{current_year}",
            f"{self._season}{current_year}"
        ])
        
        # Mélanger tous les hashtags
        random.shuffle(all_hashtags)
        
        # Assurer l'unicité des hashtags (tout en minuscules pour éviter les doublons)
        unique_hashtags = []
        lowercase_set = set()
        
        for tag in all_hashtags:
            if tag.lower() not in lowercase_set:
                unique_hashtags.append(tag)
                lowercase_set.add(tag.lower())
        
        # Réinitialiser la graine aléatoire
        random.seed()
        
        logger.info(f"{len(unique_hashtags)} hashtags générés par simulation")
        return unique_hashtags
    
    def _generate_song_data(self, title: str, artist: str) -> Dict[str, Any]:
        """
        Génère des données complètes pour une chanson
        
        Args:
            title: Titre de la chanson
            artist: Artiste
            
        Returns:
            Dictionnaire de métadonnées
        """
        # Générer un BPM réaliste
        bpm = random.randint(70, 180)
        
        # Durée réaliste entre 2 et 4 minutes
        duration = round(random.uniform(2.0, 4.0), 2)
        
        # Déterminer la popularité (pondération pour favoriser certains artistes)
        popularity_boost = 0
        for popular_artist in self._popular_artists:
            if popular_artist.lower() in artist.lower():
                popularity_boost = 20
                break
        
        popularity = random.randint(60, 85) + popularity_boost
        popularity = min(100, popularity)  # Plafonner à 100
        
        # Genre musical
        genre = random.choice(self._music_genres)
        
        # ID unique basé sur le nom
        song_id = hashlib.md5(f"{title}_{artist}".encode()).hexdigest()[:16]
        
        # Simuler une URL d'échantillon
        sample_url = f"https://example.com/music/{song_id}.mp3"
        
        # Générer un lien de téléchargement fictif
        download_url = f"https://cdn.example.com/music/{song_id}_download.mp3"
        
        # Générer une URL d'image de couverture
        cover_url = f"https://example.com/covers/{song_id}.jpg"
        
        # Date de sortie (généralement récente pour les tendances)
        days_ago = random.randint(1, 180)  # Entre 1 jour et 6 mois
        release_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        # Simuler un nombre d'utilisations
        min_uses = 1000 if popularity < 80 else 10000
        max_uses = 100000 if popularity < 90 else 1000000
        uses_count = random.randint(min_uses, max_uses)
        
        # Crédits et informations supplémentaires
        record_label = random.choice([
            "Universal Music", "Sony Music", "Warner Music", 
            "Columbia Records", "Atlantic Records", "Interscope Records",
            "Capitol Records", "Republic Records", "Def Jam Recordings"
        ])
        
        # Métadonnées audio
        audio_features = {
            "energy": random.uniform(0.3, 1.0),
            "danceability": random.uniform(0.4, 1.0),
            "valence": random.uniform(0.1, 0.9),
            "acousticness": random.uniform(0.0, 0.8),
            "instrumentalness": random.uniform(0.0, 0.5),
            "liveness": random.uniform(0.0, 0.8),
            "speechiness": random.uniform(0.0, 0.6)
        }
        
        # Combiner toutes les informations
        return {
            "id": song_id,
            "title": title,
            "artist": artist,
            "genre": genre,
            "bpm": bpm,
            "duration": duration,
            "popularity": popularity,
            "release_date": release_date,
            "uses_count": uses_count,
            "sample_url": sample_url,
            "download_url": download_url,
            "cover_url": cover_url,
            "record_label": record_label,
            "audio_features": audio_features
        }
    
    def _enhance_web_music_data(self, web_music: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Améliore les données de musique récupérées du web avec des métadonnées supplémentaires
        
        Args:
            web_music: Liste de musiques récupérées du web
            
        Returns:
            Liste de musiques avec métadonnées complètes
        """
        enhanced_music = []
        
        for music in web_music:
            title = music.get("title", "Unknown")
            artist = music.get("artist", "Unknown Artist")
            
            # Générer des métadonnées complètes
            song_data = self._generate_song_data(title, artist)
            
            # Conserver l'URL originale si disponible
            if "url" in music:
                song_data["url"] = music["url"]
                
            # Conserver l'ID original si disponible
            if "id" in music:
                song_data["id"] = music["id"]
                
            enhanced_music.append(song_data)
        
        return enhanced_music
    
    def _fetch_popular_music(self) -> List[Dict[str, Any]]:
        """
        Récupère les musiques populaires depuis l'API TikTok ou par simulation
        
        Returns:
            Liste de musiques populaires
        """
        # Si une musique spécifique a été fournie
        if self.user_music_title or self.user_music_artist:
            logger.info("Utilisation de la musique spécifiée par l'utilisateur")
            
            title = self.user_music_title or "Unknown Title"
            artist = self.user_music_artist or "Unknown Artist"
            
            # Générer les métadonnées pour la musique spécifiée
            specified_song = self._generate_song_data(title, artist)
            
            # Créer une liste de musiques avec celle spécifiée en premier
            music_list = [specified_song]
            
            # Ajouter quelques musiques populaires pour compléter la liste
            # Définir une graine pour avoir des résultats cohérents
            seed = self._generate_consistent_seed(f"music_{self.region}_{datetime.now().strftime('%Y-%m-%d')}")
            random.seed(seed)
            
            # Chansons de base (mélanges populaires fictifs)
            base_songs = [
                {
                    "title": "Stay",
                    "artist": "The Kid LAROI & Justin Bieber"
                },
                {
                    "title": "Industry Baby",
                    "artist": "Lil Nas X & Jack Harlow"
                },
                {
                    "title": "Kiss Me More",
                    "artist": "Doja Cat ft. SZA"
                },
                {
                    "title": "Levitating",
                    "artist": "Dua Lipa ft. DaBaby"
                },
                {
                    "title": "Save Your Tears",
                    "artist": "The Weeknd & Ariana Grande"
                }
            ]
            
            # Ajouter des métadonnées aux chansons de base
            for song in base_songs:
                music_list.append(self._generate_song_data(song["title"], song["artist"]))
            
            # Réinitialiser la graine aléatoire
            random.seed()
            
            return music_list
            
        # Si des musiques ont été récupérées du web, les utiliser
        if self._web_music:
            logger.info(f"Utilisation des musiques récupérées du web: {len(self._web_music)}")
            
            # Améliorer les données web avec des métadonnées supplémentaires
            enhanced_web_music = self._enhance_web_music_data(self._web_music)
            
            return enhanced_web_music
        
        # Sinon, générer des musiques simulées
        logger.info("Simulation des musiques populaires TikTok")
        
        # Définir une graine pour avoir des résultats cohérents
        seed = self._generate_consistent_seed(f"music_{self.region}_{datetime.now().strftime('%Y-%m-%d')}")
        random.seed(seed)
        
        # Chansons de base (mélanges populaires fictifs)
        base_songs = [
            {
                "title": "Stay",
                "artist": "The Kid LAROI & Justin Bieber"
            },
            {
                "title": "Industry Baby",
                "artist": "Lil Nas X & Jack Harlow"
            },
            {
                "title": "Kiss Me More",
                "artist": "Doja Cat ft. SZA"
            },
            {
                "title": "Levitating",
                "artist": "Dua Lipa ft. DaBaby"
            },
            {
                "title": "Save Your Tears",
                "artist": "The Weeknd & Ariana Grande"
            }
        ]
        
        # Générer des chansons pour les artistes populaires
        artist_songs = []
        for artist in random.sample(self._popular_artists, k=10):
            # Générer un titre fictif
            words = ["love", "heart", "dance", "night", "star", "dream", "feeling", 
                    "forever", "together", "magic", "vibe", "beat", "rhythm", "soul", "life"]
            
            title = random.choice([
                f"{random.choice(words).title()} {random.choice(words).title()}",
                f"The {random.choice(words).title()}",
                f"{random.choice(words).title()} With You",
                f"{random.choice(words).title()} Me",
                f"My {random.choice(words).title()}"
            ])
            
            artist_songs.append({
                "title": title,
                "artist": artist
            })
        
        # Combiner les listes
        all_songs = base_songs + artist_songs
        
        # Générer des métadonnées complètes pour chaque chanson
        detailed_songs = [self._generate_song_data(song["title"], song["artist"]) for song in all_songs]
        
        # Trier par popularité
        detailed_songs.sort(key=lambda x: x["popularity"], reverse=True)
        
        # Réinitialiser la graine aléatoire
        random.seed()
        
        logger.info(f"{len(detailed_songs)} musiques générées")
        return detailed_songs
    
    def _fetch_color_trends(self) -> Dict[str, Any]:
        """
        Récupère les tendances de couleurs
        
        Returns:
            Dictionnaire de tendances de couleurs
        """
        # Si une palette de couleurs spécifique a été fournie
        if self.user_color_palette:
            logger.info("Utilisation de la palette de couleurs spécifiée par l'utilisateur")
            
            # S'assurer que la palette a au moins 5 couleurs
            palette = list(self.user_color_palette)
            while len(palette) < 5:
                # Compléter avec des couleurs de la palette TikTok par défaut
                palette.append(self._color_palettes["tiktok_default"][len(palette) % len(self._color_palettes["tiktok_default"])])
            
            # Créer des données de tendances de couleurs
            color_trends = {
                "dominant_palettes": {
                    "user_specified": palette,
                    "tiktok_official": self._color_palettes["tiktok_default"],
                    "seasonal": self._color_palettes["seasonal"][self._season]
                },
                "dominant_colors": palette[:3],  # Les 3 premières couleurs comme dominantes
                "color_metadata": {
                    "season": self._season,
                    "region": self.region,
                    "timestamp": time.time(),
                    "source": "user_specified"
                }
            }
            
            return color_trends
        
        # Si des couleurs ont été extraites du web, les utiliser
        if self._web_colors:
            logger.info(f"Utilisation des couleurs extraites du web: {len(self._web_colors)}")
            
            # S'assurer qu'il y a au moins 5 couleurs
            web_colors = list(self._web_colors)
            while len(web_colors) < 5:
                web_colors.append(self._color_palettes["tiktok_default"][len(web_colors) % len(self._color_palettes["tiktok_default"])])
            
            # Palette saisonnière pour compléter
            seasonal_palette = self._color_palettes["seasonal"][self._season]
            
            # Créer une palette personnalisée basée sur les couleurs web
            custom_palette = []
            for i in range(5):
                if i < 3:  # Favoriser les couleurs web
                    custom_palette.append(web_colors[i])
                else:  # Ajouter quelques touches saisonnières
                    custom_palette.append(seasonal_palette[i % len(seasonal_palette)])
            
            # Créer des données de tendances de couleurs
            color_trends = {
                "dominant_palettes": {
                    "web_extracted": web_colors[:5],
                    "tiktok_official": self._color_palettes["tiktok_default"],
                    "seasonal": seasonal_palette,
                    "custom": custom_palette
                },
                "dominant_colors": web_colors[:3],
                "color_metadata": {
                    "season": self._season,
                    "region": self.region,
                    "timestamp": time.time(),
                    "source": "web_extracted"
                }
            }
            
            return color_trends
        
        # Mode simulation standard
        logger.info("Simulation des tendances de couleurs")
        
        # Définir une graine pour avoir des résultats cohérents
        seed = self._generate_consistent_seed(f"colors_{self.region}_{datetime.now().strftime('%Y-%m-%d')}")
        random.seed(seed)
        
        # Palettes de base
        base_palettes = self._color_palettes
        
        # Sélectionner des palettes selon la saison
        seasonal_palette = base_palettes["seasonal"][self._season]
        
        # Palette "tendance" aléatoire
        trending_sources = [p for p in base_palettes.keys() if p not in ["seasonal"]]
        trending_palette_key = random.choice(trending_sources)
        trending_palette = base_palettes[trending_palette_key]
        
        # Créer une palette personnalisée basée sur la saison
        custom_palette = []
        for _ in range(5):
            # 70% de chance de prendre de la palette saisonnière, 30% de la palette tendance
            if random.random() < 0.7:
                custom_palette.append(random.choice(seasonal_palette))
            else:
                custom_palette.append(random.choice(trending_palette))
        
        # Générer des données de tendances de couleurs
        color_trends = {
            "dominant_palettes": {
                "tiktok_official": self._color_palettes["tiktok_default"],
                "seasonal": seasonal_palette,
                "trending": trending_palette,
                "custom": custom_palette
            },
            "dominant_colors": [
                trending_palette[0],
                seasonal_palette[0],
                self._color_palettes["tiktok_default"][0]
            ],
            "color_metadata": {
                "season": self._season,
                "region": self.region,
                "timestamp": time.time()
            }
        }
        
        # Réinitialiser la graine aléatoire
        random.seed()
        
        return color_trends
    
    def _generate_timing_trends(self) -> Dict[str, Any]:
        """
        Génère des tendances de timing pour les vidéos
        
        Returns:
            Dictionnaire de tendances de timing
        """
        # Définir une graine pour avoir des résultats cohérents
        seed = self._generate_consistent_seed(f"timing_{self.region}_{datetime.now().strftime('%Y-%m-%d')}")
        random.seed(seed)
        
        # Durées vidéo populaires (en secondes)
        video_durations = [15, 30, 60]
        
        # Sélectionner une durée tendance
        trending_duration = random.choice(video_durations)
        
        # BPM (beats per minute) tendance
        trending_bpm = random.randint(90, 150)
        
        # Calculer la durée d'un beat en secondes
        beat_duration = 60 / trending_bpm
        
        # Nombre de sections typiques dans les vidéos virales
        sections_count = random.randint(3, 6)
        
        # Durée moyenne des sections
        section_duration = trending_duration / sections_count
        
        # Types de transitions populaires
        transition_types = ["cut", "fade", "slide", "zoom", "wipe", "spin"]
        trending_transitions = random.sample(transition_types, k=3)
        
        # Type de rythme
        rhythm_types = ["steady", "build-up", "drop", "alternating", "progressive"]
        trending_rhythm = random.choice(rhythm_types)
        
        # Assembler les données
        timing_trends = {
            "duration_trend": {
                "popular_durations": video_durations,
                "trending_duration": trending_duration
            },
            "beat_trend": {
                "trending_bpm": trending_bpm,
                "beat_duration": round(beat_duration, 4),
                "trending_rhythm": trending_rhythm
            },
            "structure_trend": {
                "sections_count": sections_count,
                "section_duration": round(section_duration, 2),
                "trending_transitions": trending_transitions
            },
            "engagement_metrics": {
                "optimal_hook_duration": random.randint(3, 7),
                "attention_span": random.randint(5, 15),
                "optimal_loop_factor": random.choice([1, 2, 3, 4])
            }
        }
        
        # Réinitialiser la graine aléatoire
        random.seed()
        
        return timing_trends
    
    def _generate_trend_analysis(self) -> Dict[str, Any]:
        """
        Génère une analyse complète des tendances
        
        Returns:
            Dictionnaire d'analyse de tendances
        """
        logger.info("Génération de l'analyse des tendances TikTok")
        
        # Récupérer les différentes composantes
        hashtags = self.get_trending_hashtags()
        music = self.get_popular_music()
        colors = self._fetch_color_trends()
        timing = self._generate_timing_trends()
        
        # Source de données principale
        data_source = "hybrid"
        if self._web_hashtags or self._web_music or self._web_colors:
            data_source = "web_enhanced"
        elif self.user_hashtags or self.user_music_title or self.user_color_palette:
            data_source = "user_specified"
        
        # Construire les paramètres recommandés
        recommended_settings = {
            "video_duration": timing["duration_trend"]["trending_duration"],
            "beat_frequency": timing["beat_trend"]["beat_duration"],
            "sections_count": timing["structure_trend"]["sections_count"],
            "color_palette": colors["dominant_palettes"]["custom"],
            "recommended_hashtags": hashtags[:15],
            "recommended_music": [song["title"] + " - " + song["artist"] for song in music[:5]],
            "visual_elements": [
                "text_overlay",
                "transitions",
                "zoom_effects",
                "filters",
                "captions"
            ],
            "hook_duration": timing["engagement_metrics"]["optimal_hook_duration"],
            "optimal_posting_times": [
                {"day": "Monday", "times": ["18:00", "21:00"]},
                {"day": "Wednesday", "times": ["12:30", "19:00"]},
                {"day": "Friday", "times": ["15:00", "20:00"]},
                {"day": "Saturday", "times": ["11:00", "14:00", "21:00"]},
                {"day": "Sunday", "times": ["13:00", "18:00"]}
            ],
            "trending_effects": [
                "green_screen",
                "time_warp",
                "slow_motion",
                "beauty_filter",
                "voice_effects"
            ]
        }
        
        # Assemblage des composants spécifiques fournis par l'utilisateur
        user_components = {}
        if self.user_description:
            user_components["description"] = self.user_description
            user_components["keywords"] = self._extracted_keywords
        if self.user_hashtags:
            user_components["hashtags"] = self.user_hashtags
        if self.user_music_title or self.user_music_artist:
            user_components["music"] = {
                "title": self.user_music_title,
                "artist": self.user_music_artist
            }
        if self.user_color_palette:
            user_components["color_palette"] = self.user_color_palette
        
        # Assembler l'analyse complète
        analysis = {
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "region": self.region,
            "data_source": data_source,
            "popular_hashtags": hashtags[:30],
            "popular_music": music[:20],
            "color_trends": colors,
            "timing_trends": timing,
            "recommended_settings": recommended_settings,
            "trending_challenges": self._get_trending_challenges()[:10],
            "seasonal_data": {
                "season": self._season,
                "month": self._month,
                "seasonal_hashtags": [tag for tag in hashtags if self._season in tag.lower()]
            }
        }
        
        # Ajouter les composants utilisateur s'ils existent
        if user_components:
            analysis["user_components"] = user_components
        
        # Ajouter des sources de données web si disponibles
        if self._web_hashtags or self._web_music or self._web_colors:
            analysis["web_data_sources"] = {
                "hashtags_count": len(self._web_hashtags) if self._web_hashtags else 0,
                "music_count": len(self._web_music) if self._web_music else 0,
                "colors_count": len(self._web_colors) if self._web_colors else 0,
                "timestamp": time.time()
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
        if not self._hashtags_cache and not (self.user_hashtags or self._extracted_keywords):
            cached_hashtags = self._load_cache(self.hashtags_file)
            if cached_hashtags:
                self._hashtags_cache = cached_hashtags
                logger.info(f"Hashtags chargés depuis le cache: {len(cached_hashtags)}")
        
        # Si le cache est valide, l'utiliser
        if self._hashtags_cache:
            return self._hashtags_cache[:limit]
        
        # Sinon, récupérer de nouvelles données
        hashtags = self._fetch_trending_hashtags()
        
        # Sauvegarder dans le cache si aucun paramètre utilisateur n'est fourni
        if not (self.user_hashtags or self._extracted_keywords):
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
        if not self._music_cache and not (self.user_music_title or self.user_music_artist):
            cached_music = self._load_cache(self.songs_file)
            if cached_music:
                self._music_cache = cached_music
                logger.info(f"Musiques chargées depuis le cache: {len(cached_music)}")
        
        # Si le cache est valide, l'utiliser
        if self._music_cache:
            return self._music_cache[:limit]
        
        # Sinon, récupérer de nouvelles données
        music = self._fetch_popular_music()
        
        # Sauvegarder dans le cache si aucun paramètre utilisateur n'est fourni
        if not (self.user_music_title or self.user_music_artist):
            self._save_cache(self.songs_file, music)
        
        self._music_cache = music
        
        return music[:limit]
    
    def get_color_trends(self) -> Dict[str, Any]:
        """
        Récupère les tendances de couleurs
        
        Returns:
            Dictionnaire de tendances de couleurs
        """
        # Essayer de charger depuis le cache
        if not self._colors_cache and not self.user_color_palette:
            cached_colors = self._load_cache(self.colors_file)
            if cached_colors:
                self._colors_cache = cached_colors
                logger.info("Tendances de couleurs chargées depuis le cache")
        
        # Si le cache est valide, l'utiliser
        if self._colors_cache:
            return self._colors_cache
        
        # Sinon, récupérer de nouvelles données
        colors = self._fetch_color_trends()
        
        # Sauvegarder dans le cache si aucun paramètre utilisateur n'est fourni
        if not self.user_color_palette:
            self._save_cache(self.colors_file, colors)
        
        self._colors_cache = colors
        
        return colors
    
    def get_trend_analysis(self) -> TrendData:
        """
        Analyse les tendances actuelles
        
        Returns:
            Données de tendances complètes
        """
        # Essayer de charger depuis le cache si aucun paramètre utilisateur n'est fourni
        should_use_cache = not (self.user_description or self.user_hashtags or 
                             self.user_music_title or self.user_music_artist or 
                             self.user_color_palette)
        
        if not self._trends_cache and should_use_cache:
            cached_trends = self._load_cache(self.trends_file)
            if cached_trends:
                self._trends_cache = cached_trends
                logger.info("Analyse des tendances chargée depuis le cache")
        
        # Si le cache est valide, l'utiliser
        if self._trends_cache:
            return TrendData.from_dict(self._trends_cache)
        
        # Sinon, générer une nouvelle analyse
        analysis = self._generate_trend_analysis()
        
        # Sauvegarder dans le cache si possible
        if should_use_cache:
            self._save_cache(self.trends_file, analysis)
        
        self._trends_cache = analysis
        
        return TrendData.from_dict(analysis)

if __name__ == "__main__":
    analyzer = TikTokAnalyzer(
        use_web_search=True,  # Activer la recherche web
        headless=True,        # Mode sans interface (arrière-plan)
        cache_duration=3600   # Durée de validité du cache (1h)
    )

    # Récupérer les tendances
    trend_data = analyzer.get_trend_analysis()
    print(trend_data)