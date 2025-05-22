# audio_generators/trend_audio_generator.py
"""
Générateur audio basé sur les tendances musicales
Génère une piste audio à partir de tendances et d'événements
Version améliorée avec téléchargement automatique de musiques MIDI
"""

import os
import time
import logging
import numpy as np
import librosa
import soundfile as sf
from scipy.io import wavfile
from typing import Dict, List, Any, Optional, Tuple, Union
import random
import requests
from pathlib import Path
import json
import re
from urllib.parse import urljoin, urlparse, quote
import mido  # Pour les fichiers MIDI
from bs4 import BeautifulSoup  # Pour scraper MuseScore

from core.interfaces import IAudioGenerator, TrendData, AudioEvent

logger = logging.getLogger("TikSimPro")

class TrendAudioGenerator(IAudioGenerator):
    """
    Générateur de pistes audio basées sur les tendances et les événements
    Avec téléchargement automatique de musiques MIDI populaires
    """
    
    def __init__(self, note_volume = 1.0, explosion_volume = 1.0, activation_volume = 1.0, passage_volume = 1.0):
        """Initialise le générateur audio"""
        # Paramètres par défaut
        self.sample_rate = 44100
        self.duration = 30.0
        self.output_path = "output/audio.wav"
        self.sounds_dir = "temp/sounds"
        self.midi_dir = "temp/midi"
        
        # Volume
        self.note_volume = note_volume
        self.explosion_volume = explosion_volume
        self.activation_volume = activation_volume
        self.passage_volume = passage_volume

        # Créer les répertoires nécessaires
        os.makedirs(self.sounds_dir, exist_ok=True)
        os.makedirs(self.midi_dir, exist_ok=True)
        
        # Événements audio
        self.events = []
        
        # Données de tendances
        self.trend_data = None
        
        # Sons de base
        self.notes = []  # (note_idx, octave, path)
        self.effect_sounds = {}  # {type_effect: {param: path}}
        self.background_music = None
        
        # Palette sonore
        self.current_melody = [0, 2, 4, 5, 4, 2, 0, 2]  # Do majeur par défaut
        self.beat_frequency = 1.0  # 1 beat par seconde (60 BPM)
        
        # Base de données de musiques populaires
        self.popular_songs_db = self._load_popular_songs_db()
        
        # Cache des téléchargements
        self.download_cache = {}

        logger.info("TrendAudioGenerator initialisé avec téléchargement MIDI automatique")
    
    def _load_popular_songs_db(self) -> Dict[str, List]:
        """
        Charge dynamiquement la base de données des musiques populaires depuis internet
        
        Returns:
            Dictionnaire avec les informations des musiques populaires récupérées en temps réel
        """
        try:
            # Vérifier le cache (valide pendant 24h)
            cache_file = os.path.join(self.sounds_dir, "songs_cache.json")
            if os.path.exists(cache_file):
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < 86400:  # 24 heures
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cached_data = json.load(f)
                        logger.info("Base de données de musiques populaires chargée depuis le cache")
                        return cached_data
                    except:
                        pass
            
            logger.info("Récupération dynamique des musiques populaires depuis internet...")
            
            songs_db = {
                "trending": [],
                "classical": [],
                "gaming": [],
                "viral_tiktok": []
            }
            
            # 1. Récupérer les tendances depuis plusieurs sources
            trending_songs = []
            trending_songs.extend(self._fetch_spotify_trending())
            trending_songs.extend(self._fetch_billboard_hot100())
            trending_songs.extend(self._fetch_lastfm_trending())
            trending_songs.extend(self._fetch_tiktok_trending())
            
            # 2. Récupérer les classiques populaires
            classical_songs = self._fetch_classical_popular()
            
            # 3. Récupérer les musiques de jeux populaires
            gaming_songs = self._fetch_gaming_popular()
            
            # 4. Nettoyer et formater les résultats
            songs_db["trending"] = self._clean_and_format_songs(trending_songs, "pop")[:20]
            songs_db["classical"] = self._clean_and_format_songs(classical_songs, "classical")[:10]
            songs_db["gaming"] = self._clean_and_format_songs(gaming_songs, "game")[:10]
            songs_db["viral_tiktok"] = self._extract_viral_tiktok(trending_songs)[:15]
            
            # 5. Sauvegarder en cache
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(songs_db, f, ensure_ascii=False, indent=2)
                logger.info("Base de données de musiques sauvegardée en cache")
            except Exception as e:
                logger.warning(f"Impossible de sauvegarder le cache: {e}")
            
            total_songs = sum(len(songs) for songs in songs_db.values())
            logger.info(f"Base de données dynamique chargée: {total_songs} musiques récupérées")
            
            return songs_db
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement dynamique des musiques: {e}")
            # Fallback vers une base de données statique minimale
            return self._get_fallback_songs_db()
    
    def _fetch_spotify_trending(self) -> List[Dict]:
        """
        Récupère les musiques tendance depuis des sources alternatives fiables
        
        Returns:
            Liste des musiques tendance
        """
        songs = []
        
        try:
            # Méthode 1: API iTunes/Apple Music (gratuite et fiable)
            itunes_songs = self._fetch_from_itunes()
            songs.extend(itunes_songs)
            
            # Méthode 2: Scraping de sites musicaux alternatifs
            if len(songs) < 5:
                alternative_songs = self._fetch_from_music_sites()
                songs.extend(alternative_songs)
            
            # Méthode 3: Base de données de musiques populaires récentes (fallback)
            if len(songs) < 5:
                fallback_songs = self._get_recent_popular_songs()
                songs.extend(fallback_songs)
            
            logger.info(f"Récupéré {len(songs)} musiques tendance (combiné)")
            return songs[:15]  # Limiter à 15
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tendances: {e}")
            return self._get_recent_popular_songs()  # Fallback complet
    
    def _fetch_from_itunes(self) -> List[Dict]:
        """Récupère depuis l'API iTunes (gratuite et fiable)"""
        try:
            # API iTunes pour les top songs
            url = "https://itunes.apple.com/search"
            params = {
                "term": "pop music 2024 2025",
                "media": "music",
                "entity": "song",
                "limit": 20,
                "country": "US"
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
            
            data = response.json()
            songs = []
            
            for item in data.get("results", [])[:10]:
                try:
                    title = item.get("trackName", "")
                    artist = item.get("artistName", "")
                    
                    if title and artist:
                        songs.append({
                            "title": title,
                            "artist": artist,
                            "source": "itunes"
                        })
                except:
                    continue
            
            logger.info(f"Récupéré {len(songs)} musiques depuis iTunes")
            return songs
            
        except Exception as e:
            logger.error(f"Erreur iTunes: {e}")
            return []
    
    def _fetch_from_music_sites(self) -> List[Dict]:
        """Récupère depuis des sites musicaux alternatifs"""
        songs = []
        
        try:
            # Site 1: Top40-Charts.com (plus simple à scraper)
            songs.extend(self._scrape_top40_charts())
            
            # Site 2: Musicometer.org
            if len(songs) < 5:
                songs.extend(self._scrape_musicometer())
            
            return songs
            
        except Exception as e:
            logger.error(f"Erreur sites musicaux: {e}")
            return []
    
    def _scrape_top40_charts(self) -> List[Dict]:
        """Scrape Top40-Charts.com"""
        try:
            url = "https://top40-charts.com/chart.php?cid=27"  # Hot 100
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            songs = []
            
            # Rechercher les tables ou listes de chansons
            rows = soup.find_all('tr')
            
            for row in rows[:15]:
                try:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        # Généralement: Position, Titre, Artiste
                        title_cell = cells[1] if len(cells) > 1 else None
                        artist_cell = cells[2] if len(cells) > 2 else None
                        
                        if title_cell and artist_cell:
                            title = title_cell.get_text(strip=True)
                            artist = artist_cell.get_text(strip=True)
                            
                            # Nettoyer les textes
                            title = re.sub(r'\d+\.?\s*', '', title)  # Supprimer numéros
                            title = re.sub(r'\s+', ' ', title).strip()
                            artist = re.sub(r'\s+', ' ', artist).strip()
                            
                            if len(title) > 2 and len(artist) > 2:
                                songs.append({
                                    "title": title,
                                    "artist": artist,
                                    "source": "top40_charts"
                                })
                except:
                    continue
            
            logger.info(f"Récupéré {len(songs)} musiques depuis Top40-Charts")
            return songs
            
        except Exception as e:
            logger.error(f"Erreur Top40-Charts: {e}")
            return []
    
    def _scrape_musicometer(self) -> List[Dict]:
        """Scrape alternative simple"""
        try:
            # Essayer un autre site simple
            url = "https://www.officialcharts.com/charts/singles-chart/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            songs = []
            
            # Rechercher différents patterns HTML
            patterns = [
                {'tag': 'div', 'class': re.compile(r'title|track|song')},
                {'tag': 'span', 'class': re.compile(r'title|track|song')},
                {'tag': 'h3', 'class': re.compile(r'title|track|song')},
            ]
            
            for pattern in patterns:
                elements = soup.find_all(pattern['tag'], class_=pattern['class'])
                
                for element in elements[:10]:
                    try:
                        text = element.get_text(strip=True)
                        
                        # Essayer de parser "Titre - Artiste" ou "Artiste - Titre"
                        if " - " in text:
                            parts = text.split(" - ", 1)
                            if len(parts) == 2:
                                title, artist = parts[0].strip(), parts[1].strip()
                                if len(title) > 2 and len(artist) > 2:
                                    songs.append({
                                        "title": title,
                                        "artist": artist,
                                        "source": "musicometer"
                                    })
                    except:
                        continue
                
                if len(songs) >= 5:
                    break
            
            logger.info(f"Récupéré {len(songs)} musiques depuis sites alternatifs")
            return songs
            
        except Exception as e:
            logger.error(f"Erreur sites alternatifs: {e}")
            return []
    
    def _get_recent_popular_songs(self) -> List[Dict]:
        """Base de données de musiques populaires récentes (fallback fiable)"""
        return [
            {"title": "Flowers", "artist": "Miley Cyrus", "source": "popular_2024"},
            {"title": "Anti-Hero", "artist": "Taylor Swift", "source": "popular_2024"},
            {"title": "As It Was", "artist": "Harry Styles", "source": "popular_2024"},
            {"title": "Heat Waves", "artist": "Glass Animals", "source": "popular_2024"},
            {"title": "Stay", "artist": "The Kid LAROI & Justin Bieber", "source": "popular_2024"},
            {"title": "Industry Baby", "artist": "Lil Nas X & Jack Harlow", "source": "popular_2024"},
            {"title": "Good 4 U", "artist": "Olivia Rodrigo", "source": "popular_2024"},
            {"title": "Levitating", "artist": "Dua Lipa", "source": "popular_2024"},
            {"title": "Blinding Lights", "artist": "The Weeknd", "source": "popular_2024"},
            {"title": "Watermelon Sugar", "artist": "Harry Styles", "source": "popular_2024"},
            {"title": "Peaches", "artist": "Justin Bieber", "source": "popular_2024"},
            {"title": "Montero", "artist": "Lil Nas X", "source": "popular_2024"},
            {"title": "drivers license", "artist": "Olivia Rodrigo", "source": "popular_2024"},
            {"title": "positions", "artist": "Ariana Grande", "source": "popular_2024"},
            {"title": "Mood", "artist": "24kGoldn ft. iann dior", "source": "popular_2024"}
        ]
    
    def _fetch_billboard_hot100(self) -> List[Dict]:
        """
        Récupère les musiques populaires via plusieurs méthodes alternatives
        
        Returns:
            Liste des musiques du Billboard et sources alternatives
        """
        songs = []
        
        try:
            # Méthode 1: API MusicBrainz (gratuite et fiable)
            musicbrainz_songs = self._fetch_from_musicbrainz()
            songs.extend(musicbrainz_songs)
            
            # Méthode 2: Scraping Billboard simplifié
            if len(songs) < 5:
                billboard_songs = self._scrape_billboard_alternative()
                songs.extend(billboard_songs)
            
            # Méthode 3: Base de données Billboard récente (fallback)
            if len(songs) < 5:
                fallback_songs = self._get_recent_billboard_songs()
                songs.extend(fallback_songs)
            
            logger.info(f"Récupéré {len(songs)} musiques Billboard (combiné)")
            return songs[:20]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération Billboard: {e}")
            return self._get_recent_billboard_songs()
    
    def _fetch_from_musicbrainz(self) -> List[Dict]:
        """Récupère depuis MusicBrainz API (gratuite)"""
        try:
            # API MusicBrainz pour rechercher des artistes populaires
            popular_artists = [
                "Taylor Swift", "Harry Styles", "Dua Lipa", "The Weeknd", 
                "Ariana Grande", "Billie Eilish", "Post Malone", "Olivia Rodrigo"
            ]
            
            songs = []
            
            for artist in popular_artists[:5]:  # Limiter pour éviter la surcharge
                try:
                    url = "https://musicbrainz.org/ws/2/recording"
                    params = {
                        "query": f'artist:"{artist}" AND primarytype:album',
                        "limit": 3,
                        "fmt": "json"
                    }
                    
                    headers = {
                        "User-Agent": "TikSimPro/1.0 (contact@example.com)"
                    }
                    
                    response = requests.get(url, params=params, headers=headers, timeout=8)
                    if response.status_code != 200:
                        continue
                    
                    data = response.json()
                    
                    for recording in data.get("recordings", []):
                        try:
                            title = recording.get("title", "")
                            if title and len(title) > 2:
                                songs.append({
                                    "title": title,
                                    "artist": artist,
                                    "source": "musicbrainz"
                                })
                        except:
                            continue
                    
                    # Petite pause pour respecter l'API
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.debug(f"Erreur MusicBrainz pour {artist}: {e}")
                    continue
            
            logger.info(f"Récupéré {len(songs)} musiques depuis MusicBrainz")
            return songs
            
        except Exception as e:
            logger.error(f"Erreur MusicBrainz: {e}")
            return []
    
    def _scrape_billboard_alternative(self) -> List[Dict]:
        """Scraping Billboard avec approche simplifiée"""
        try:
            # Essayer une approche plus simple
            url = "https://www.billboard.com/charts/hot-100/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive"
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            songs = []
            
            # Rechercher plusieurs patterns possibles
            patterns = [
                # Pattern 1: Liens avec titres
                soup.find_all('a', href=re.compile(r'/music/')),
                # Pattern 2: Éléments avec classes musicales
                soup.find_all(['h3', 'h4', 'span'], class_=re.compile(r'title|track|song', re.I)),
                # Pattern 3: Divs contenant des infos musicales
                soup.find_all('div', class_=re.compile(r'chart|ranking|position', re.I))
            ]
            
            for pattern_results in patterns:
                for element in pattern_results[:10]:
                    try:
                        text = element.get_text(strip=True)
                        
                        # Nettoyer et parser le texte
                        if len(text) > 5 and len(text) < 100:
                            # Supprimer les numéros de classement
                            clean_text = re.sub(r'^\d+\.?\s*', '', text)
                            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                            
                            # Essayer de séparer titre et artiste
                            if " by " in clean_text.lower():
                                parts = clean_text.split(" by ", 1)
                                if len(parts) == 2:
                                    title, artist = parts[0].strip(), parts[1].strip()
                            elif " - " in clean_text:
                                parts = clean_text.split(" - ", 1)
                                if len(parts) == 2:
                                    title, artist = parts[0].strip(), parts[1].strip()
                            else:
                                # Si pas de séparateur clair, traiter comme titre
                                title = clean_text
                                artist = "Various Artists"
                            
                            if len(title) > 2:
                                songs.append({
                                    "title": title,
                                    "artist": artist,
                                    "source": "billboard_alt"
                                })
                    except:
                        continue
                
                if len(songs) >= 10:
                    break
            
            logger.info(f"Récupéré {len(songs)} musiques depuis Billboard alternatif")
            return songs
            
        except Exception as e:
            logger.error(f"Erreur Billboard alternatif: {e}")
            return []
    
    def _get_recent_billboard_songs(self) -> List[Dict]:
        """Base de données Billboard récente (fallback)"""
        return [
            {"title": "Last Night", "artist": "Morgan Wallen", "source": "billboard_recent"},
            {"title": "Flowers", "artist": "Miley Cyrus", "source": "billboard_recent"},
            {"title": "Kill Bill", "artist": "SZA", "source": "billboard_recent"},
            {"title": "Anti-Hero", "artist": "Taylor Swift", "source": "billboard_recent"},
            {"title": "Creepin'", "artist": "Metro Boomin, The Weeknd, 21 Savage", "source": "billboard_recent"},
            {"title": "Unholy", "artist": "Sam Smith ft. Kim Petras", "source": "billboard_recent"},
            {"title": "As It Was", "artist": "Harry Styles", "source": "billboard_recent"},
            {"title": "Heat Waves", "artist": "Glass Animals", "source": "billboard_recent"},
            {"title": "About Damn Time", "artist": "Lizzo", "source": "billboard_recent"},
            {"title": "Running Up That Hill", "artist": "Kate Bush", "source": "billboard_recent"},
            {"title": "Bad Habit", "artist": "Steve Lacy", "source": "billboard_recent"},
            {"title": "I'm Good", "artist": "David Guetta & Bebe Rexha", "source": "billboard_recent"},
            {"title": "Lavender Haze", "artist": "Taylor Swift", "source": "billboard_recent"},
            {"title": "Vampire", "artist": "Olivia Rodrigo", "source": "billboard_recent"},
            {"title": "Calm Down", "artist": "Rema & Selena Gomez", "source": "billboard_recent"}
        ]
    
    def _fetch_lastfm_trending(self) -> List[Dict]:
        """
        Récupère les tendances musicales via Last.fm et sources alternatives
        
        Returns:
            Liste des musiques tendance
        """
        songs = []
        
        try:
            # Méthode 1: Last.fm API (sans clé, endpoints publics)
            lastfm_songs = self._fetch_lastfm_public()
            songs.extend(lastfm_songs)
            
            # Méthode 2: API Deezer (gratuite)
            if len(songs) < 5:
                deezer_songs = self._fetch_from_deezer()
                songs.extend(deezer_songs)
            
            # Méthode 3: Fallback avec musiques tendance récentes
            if len(songs) < 5:
                fallback_songs = self._get_trending_fallback()
                songs.extend(fallback_songs)
            
            logger.info(f"Récupéré {len(songs)} musiques tendance (Last.fm combiné)")
            return songs[:15]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération Last.fm: {e}")
            return self._get_trending_fallback()
    
    def _fetch_lastfm_public(self) -> List[Dict]:
        """Récupère depuis Last.fm sans clé API"""
        try:
            # Scraping simple du site Last.fm
            url = "https://www.last.fm/music"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            songs = []
            
            # Rechercher les éléments musicaux
            music_elements = soup.find_all(['a', 'span', 'h3'], class_=re.compile(r'track|song|artist', re.I))
            
            current_title = None
            current_artist = None
            
            for element in music_elements[:30]:
                try:
                    text = element.get_text(strip=True)
                    
                    if len(text) > 2 and len(text) < 80:
                        # Essayer de détecter si c'est un titre ou un artiste
                        if element.get('class'):
                            classes = ' '.join(element.get('class', []))
                            
                            if 'track' in classes.lower() or 'song' in classes.lower():
                                current_title = text
                            elif 'artist' in classes.lower():
                                current_artist = text
                            
                            # Si on a les deux, créer une entrée
                            if current_title and current_artist:
                                songs.append({
                                    "title": current_title,
                                    "artist": current_artist,
                                    "source": "lastfm_scrape"
                                })
                                current_title = None
                                current_artist = None
                        
                        # Alternative: parser "Titre - Artiste"
                        elif " - " in text:
                            parts = text.split(" - ", 1)
                            if len(parts) == 2:
                                title, artist = parts[0].strip(), parts[1].strip()
                                if len(title) > 2 and len(artist) > 2:
                                    songs.append({
                                        "title": title,
                                        "artist": artist,
                                        "source": "lastfm_scrape"
                                    })
                except:
                    continue
            
            logger.info(f"Récupéré {len(songs)} musiques depuis Last.fm scraping")
            return songs
            
        except Exception as e:
            logger.error(f"Erreur Last.fm scraping: {e}")
            return []
    
    def _fetch_from_deezer(self) -> List[Dict]:
        """Récupère depuis l'API Deezer (gratuite)"""
        try:
            # API Deezer pour les charts
            url = "https://api.deezer.com/chart/0/tracks"
            params = {"limit": 15}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return []
            
            data = response.json()
            songs = []
            
            for track in data.get("data", []):
                try:
                    title = track.get("title", "")
                    artist_info = track.get("artist", {})
                    artist = artist_info.get("name", "") if artist_info else ""
                    
                    if title and artist:
                        songs.append({
                            "title": title,
                            "artist": artist,
                            "source": "deezer"
                        })
                except:
                    continue
            
            logger.info(f"Récupéré {len(songs)} musiques depuis Deezer")
            return songs
            
        except Exception as e:
            logger.error(f"Erreur Deezer API: {e}")
            return []
    
    def _get_trending_fallback(self) -> List[Dict]:
        """Musiques tendance récentes (fallback fiable)"""
        return [
            {"title": "Paint The Town Red", "artist": "Doja Cat", "source": "trending_2024"},
            {"title": "Vampire", "artist": "Olivia Rodrigo", "source": "trending_2024"},
            {"title": "Cruel Summer", "artist": "Taylor Swift", "source": "trending_2024"},
            {"title": "Flowers", "artist": "Miley Cyrus", "source": "trending_2024"},
            {"title": "Kill Bill", "artist": "SZA", "source": "trending_2024"},
            {"title": "Unholy", "artist": "Sam Smith ft. Kim Petras", "source": "trending_2024"},
            {"title": "Anti-Hero", "artist": "Taylor Swift", "source": "trending_2024"},
            {"title": "As It Was", "artist": "Harry Styles", "source": "trending_2024"},
            {"title": "Bad Habit", "artist": "Steve Lacy", "source": "trending_2024"},
            {"title": "Heat Waves", "artist": "Glass Animals", "source": "trending_2024"},
            {"title": "About Damn Time", "artist": "Lizzo", "source": "trending_2024"},
            {"title": "Running Up That Hill", "artist": "Kate Bush", "source": "trending_2024"},
            {"title": "I'm Good", "artist": "David Guetta & Bebe Rexha", "source": "trending_2024"},
            {"title": "Calm Down", "artist": "Rema & Selena Gomez", "source": "trending_2024"},
            {"title": "Shivers", "artist": "Ed Sheeran", "source": "trending_2024"}
        ]
    
    def _fetch_tiktok_trending(self) -> List[Dict]:
        """
        Récupère les musiques tendance TikTok via plusieurs sources
        
        Returns:
            Liste des musiques TikTok
        """
        songs = []
        
        try:
            # Méthode 1: Base de données de musiques TikTok populaires récentes
            recent_tiktok = self._get_viral_tiktok_songs()
            songs.extend(recent_tiktok)
            
            # Méthode 2: Recherche de tendances musicales sur des sites alternatifs
            if len(songs) < 8:
                alternative_viral = self._fetch_viral_alternatives()
                songs.extend(alternative_viral)
            
            # Méthode 3: Analyse de mots-clés viral actuels
            if len(songs) < 8:
                keyword_songs = self._get_viral_keyword_songs()
                songs.extend(keyword_songs)
            
            logger.info(f"Récupéré {len(songs)} musiques TikTok tendance")
            return songs[:10]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération TikTok: {e}")
            return self._get_viral_tiktok_songs()
    
    def _get_viral_tiktok_songs(self) -> List[Dict]:
        """Base de données de sons viraux TikTok récents"""
        return [
            {"title": "Paint The Town Red", "artist": "Doja Cat", "source": "tiktok", "viral": True},
            {"title": "Vampire", "artist": "Olivia Rodrigo", "source": "tiktok", "viral": True},
            {"title": "Calm Down", "artist": "Rema & Selena Gomez", "source": "tiktok", "viral": True},
            {"title": "Flowers", "artist": "Miley Cyrus", "source": "tiktok", "viral": True},
            {"title": "Kill Bill", "artist": "SZA", "source": "tiktok", "viral": True},
            {"title": "Boy's a Liar Pt. 2", "artist": "PinkPantheress & Ice Spice", "source": "tiktok", "viral": True},
            {"title": "Anti-Hero", "artist": "Taylor Swift", "source": "tiktok", "viral": True},
            {"title": "Creepin'", "artist": "Metro Boomin, The Weeknd, 21 Savage", "source": "tiktok", "viral": True},
            {"title": "Shivers", "artist": "Ed Sheeran", "source": "tiktok", "viral": True},
            {"title": "About Damn Time", "artist": "Lizzo", "source": "tiktok", "viral": True},
            {"title": "Bad Habit", "artist": "Steve Lacy", "source": "tiktok", "viral": True},
            {"title": "Running Up That Hill", "artist": "Kate Bush", "source": "tiktok", "viral": True},
            {"title": "Heat Waves", "artist": "Glass Animals", "source": "tiktok", "viral": True},
            {"title": "As It Was", "artist": "Harry Styles", "source": "tiktok", "viral": True},
            {"title": "I'm Good", "artist": "David Guetta & Bebe Rexha", "source": "tiktok", "viral": True}
        ]
    
    def _fetch_viral_alternatives(self) -> List[Dict]:
        """Recherche sur des sites de tendances musicales"""
        try:
            # Essayer de récupérer depuis des agrégateurs de tendances
            viral_sources = [
                self._check_popvortex(),
                self._check_trending_sounds()
            ]
            
            songs = []
            for source_songs in viral_sources:
                songs.extend(source_songs)
                if len(songs) >= 5:
                    break
            
            return songs
            
        except Exception as e:
            logger.error(f"Erreur viral alternatives: {e}")
            return []
    
    def _check_popvortex(self) -> List[Dict]:
        """Vérifier PopVortex ou sites similaires"""
        try:
            # Site exemple pour les tendances musicales
            url = "https://popvortex.com/music/charts/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            songs = []
            
            # Rechercher des patterns de musique
            music_links = soup.find_all('a', href=re.compile(r'/music/|/song/|/track/'))
            
            for link in music_links[:8]:
                try:
                    text = link.get_text(strip=True)
                    
                    if " - " in text and len(text) > 5:
                        parts = text.split(" - ", 1)
                        if len(parts) == 2:
                            title, artist = parts[0].strip(), parts[1].strip()
                            if len(title) > 2 and len(artist) > 2:
                                songs.append({
                                    "title": title,
                                    "artist": artist,
                                    "source": "popvortex",
                                    "viral": True
                                })
                except:
                    continue
            
            return songs
            
        except Exception as e:
            logger.error(f"Erreur PopVortex: {e}")
            return []
    
    def _check_trending_sounds(self) -> List[Dict]:
        """Vérifier d'autres sources de sons tendance"""
        try:
            # Base de données de sons tendance par mots-clés
            trending_keywords = [
                ("trending sound", "viral audio"),
                ("tiktok hit", "popular song"),
                ("viral music", "social media hit")
            ]
            
            songs = []
            
            # Simuler une recherche basée sur des mots-clés populaires
            for keyword_pair in trending_keywords:
                for keyword in keyword_pair:
                    # Ici on pourrait faire une vraie recherche API
                    # Pour l'instant on utilise des données prédéfinies
                    if "viral" in keyword:
                        viral_songs = self._get_keyword_based_songs(keyword)
                        songs.extend(viral_songs)
            
            return songs[:5]
            
        except Exception as e:
            logger.error(f"Erreur trending sounds: {e}")
            return []
    
    def _get_viral_keyword_songs(self) -> List[Dict]:
        """Récupère des musiques basées sur des mots-clés viraux"""
        return [
            {"title": "Unholy", "artist": "Sam Smith ft. Kim Petras", "source": "viral_keyword", "viral": True},
            {"title": "Lavender Haze", "artist": "Taylor Swift", "source": "viral_keyword", "viral": True},
            {"title": "Karma", "artist": "Taylor Swift", "source": "viral_keyword", "viral": True},
            {"title": "Watermelon Sugar", "artist": "Harry Styles", "source": "viral_keyword", "viral": True},
            {"title": "Levitating", "artist": "Dua Lipa", "source": "viral_keyword", "viral": True}
        ]
    
    def _get_keyword_based_songs(self, keyword: str) -> List[Dict]:
        """Génère des musiques basées sur un mot-clé spécifique"""
        keyword_mapping = {
            "viral": [
                {"title": "Stay", "artist": "The Kid LAROI & Justin Bieber", "source": "keyword_viral", "viral": True},
                {"title": "Industry Baby", "artist": "Lil Nas X & Jack Harlow", "source": "keyword_viral", "viral": True}
            ],
            "trending": [
                {"title": "Good 4 U", "artist": "Olivia Rodrigo", "source": "keyword_trending", "viral": True},
                {"title": "Peaches", "artist": "Justin Bieber", "source": "keyword_trending", "viral": True}
            ],
            "tiktok": [
                {"title": "Montero", "artist": "Lil Nas X", "source": "keyword_tiktok", "viral": True},
                {"title": "drivers license", "artist": "Olivia Rodrigo", "source": "keyword_tiktok", "viral": True}
            ]
        }
        
        for key, songs in keyword_mapping.items():
            if key in keyword.lower():
                return songs
        
        return []
    
    def _fetch_classical_popular(self) -> List[Dict]:
        """
        Récupère les musiques classiques populaires
        
        Returns:
            Liste des musiques classiques
        """
        try:
            # Utiliser un site de musique classique
            url = "https://www.classical.org/most-popular-classical-music/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                # Fallback vers une liste statique
                return [
                    {"title": "Für Elise", "artist": "Beethoven", "source": "classical"},
                    {"title": "Canon in D", "artist": "Pachelbel", "source": "classical"},
                    {"title": "Moonlight Sonata", "artist": "Beethoven", "source": "classical"},
                    {"title": "The Four Seasons", "artist": "Vivaldi", "source": "classical"},
                    {"title": "Symphony No. 5", "artist": "Beethoven", "source": "classical"}
                ]
            
            soup = BeautifulSoup(response.text, 'html.parser')
            songs = []
            
            # Rechercher les pièces classiques populaires
            classical_elements = soup.find_all(['h2', 'h3', 'li'], string=re.compile(r'[A-Z][a-z]'))
            
            for element in classical_elements[:10]:
                try:
                    text = element.get_text(strip=True)
                    
                    # Parser les titres classiques courants
                    classical_patterns = [
                        (r'(.+) by (.+)', lambda m: (m.group(1), m.group(2))),
                        (r'(.+) - (.+)', lambda m: (m.group(1), m.group(2))),
                        (r'([A-Z][a-z\s]+) \((.+)\)', lambda m: (m.group(1), m.group(2)))
                    ]
                    
                    for pattern, parser in classical_patterns:
                        match = re.search(pattern, text)
                        if match:
                            title, artist = parser(match)
                            songs.append({
                                "title": title.strip(),
                                "artist": artist.strip(),
                                "source": "classical"
                            })
                            break
                except:
                    continue
            
            # Ajouter des classiques de base si pas assez trouvés
            if len(songs) < 5:
                fallback_classical = [
                    {"title": "Für Elise", "artist": "Beethoven", "source": "classical"},
                    {"title": "Canon in D", "artist": "Pachelbel", "source": "classical"},
                    {"title": "Moonlight Sonata", "artist": "Beethoven", "source": "classical"},
                    {"title": "The Four Seasons", "artist": "Vivaldi", "source": "classical"},
                    {"title": "Symphony No. 5", "artist": "Beethoven", "source": "classical"}
                ]
                songs.extend(fallback_classical)
            
            logger.info(f"Récupéré {len(songs)} musiques classiques")
            return songs[:10]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération classique: {e}")
            return []
    
    def _fetch_gaming_popular(self) -> List[Dict]:
        """
        Récupère les musiques de jeux populaires
        
        Returns:
            Liste des musiques de jeux
        """
        try:
            # Base de données statique de musiques de jeux populaires
            # Car c'est plus stable que le scraping pour ce type de contenu
            gaming_songs = [
                {"title": "Sweden", "artist": "C418", "source": "minecraft"},
                {"title": "Zelda Main Theme", "artist": "Nintendo", "source": "zelda"},
                {"title": "Super Mario Bros Theme", "artist": "Nintendo", "source": "mario"},
                {"title": "Tetris Theme", "artist": "Hirokazu Tanaka", "source": "tetris"},
                {"title": "Final Fantasy Victory Fanfare", "artist": "Nobuo Uematsu", "source": "final_fantasy"},
                {"title": "Halo Theme", "artist": "Martin O'Donnell", "source": "halo"},
                {"title": "Undertale - Megalovania", "artist": "Toby Fox", "source": "undertale"},
                {"title": "Pokémon Red/Blue Theme", "artist": "Junichi Masuda", "source": "pokemon"},
                {"title": "Skyrim - Dragonborn", "artist": "Jeremy Soule", "source": "skyrim"},
                {"title": "Portal - Still Alive", "artist": "Jonathan Coulton", "source": "portal"}
            ]
            
            logger.info(f"Récupéré {len(gaming_songs)} musiques de jeux")
            return gaming_songs
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération gaming: {e}")
            return []
    
    def _clean_and_format_songs(self, songs: List[Dict], genre: str) -> List[Dict]:
        """
        Nettoie et formate la liste des musiques
        
        Args:
            songs: Liste brute des musiques
            genre: Genre musical
            
        Returns:
            Liste formatée et nettoyée
        """
        formatted_songs = []
        seen_combinations = set()
        
        for song in songs:
            try:
                title = song.get("title", "").strip()
                artist = song.get("artist", "").strip()
                
                if not title or not artist:
                    continue
                
                # Nettoyer les titres
                title = re.sub(r'\[.*?\]|\(.*?\)', '', title).strip()
                artist = re.sub(r'\[.*?\]|\(.*?\)', '', artist).strip()
                
                # Éviter les doublons
                combination = f"{title.lower()}_{artist.lower()}"
                if combination in seen_combinations:
                    continue
                seen_combinations.add(combination)
                
                # Générer des mots-clés
                keywords = []
                keywords.extend(title.lower().split())
                keywords.extend(artist.lower().split())
                keywords = [kw for kw in keywords if len(kw) > 2]
                
                formatted_song = {
                    "title": title,
                    "artist": artist,
                    "keywords": keywords,
                    "musescore_search": f"{title} {artist}",
                    "genre": genre,
                    "source": song.get("source", "unknown"),
                    "viral": song.get("viral", False)
                }
                
                formatted_songs.append(formatted_song)
                
            except Exception as e:
                logger.warning(f"Erreur lors du formatage de la chanson: {e}")
                continue
        
        return formatted_songs
    
    def _extract_viral_tiktok(self, trending_songs: List[Dict]) -> List[Dict]:
        """
        Extrait les musiques virales TikTok depuis la liste des tendances
        
        Args:
            trending_songs: Liste des musiques tendance
            
        Returns:
            Liste des musiques virales TikTok
        """
        viral_songs = []
        
        for song in trending_songs:
            if song.get("viral", False) or song.get("source") == "tiktok":
                viral_songs.append(song)
        
        return viral_songs
    
    def _get_fallback_songs_db(self) -> Dict[str, List]:
        """
        Base de données de fallback en cas d'échec du chargement dynamique
        
        Returns:
            Base de données minimale statique
        """
        return {
            "trending": [
                {
                    "title": "Shape of You",
                    "artist": "Ed Sheeran",
                    "keywords": ["shape", "you", "ed", "sheeran"],
                    "musescore_search": "Shape of You Ed Sheeran",
                    "genre": "pop",
                    "source": "fallback"
                },
                {
                    "title": "Blinding Lights",
                    "artist": "The Weeknd",
                    "keywords": ["blinding", "lights", "weeknd"],
                    "musescore_search": "Blinding Lights Weeknd",
                    "genre": "synthpop",
                    "source": "fallback"
                }
            ],
            "classical": [
                {
                    "title": "Für Elise",
                    "artist": "Beethoven",
                    "keywords": ["fur", "elise", "beethoven"],
                    "musescore_search": "Fur Elise Beethoven",
                    "genre": "classical",
                    "source": "fallback"
                }
            ],
            "gaming": [
                {
                    "title": "Sweden",
                    "artist": "C418",
                    "keywords": ["minecraft", "sweden", "c418"],
                    "musescore_search": "Minecraft Sweden C418",
                    "genre": "game",
                    "source": "fallback"
                }
            ],
            "viral_tiktok": []
        }
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure le générateur avec des paramètres spécifiques
        
        Args:
            config: Paramètres de configuration
            
        Returns:
            True si la configuration a réussi, False sinon
        """
        try:
            # Appliquer les paramètres fournis
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            # Créer les répertoires nécessaires
            os.makedirs(self.sounds_dir, exist_ok=True)
            os.makedirs(self.midi_dir, exist_ok=True)
            
            # Créer le répertoire de sortie
            output_dir = os.path.dirname(self.output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            logger.info(f"Générateur audio configuré: {self.sample_rate} Hz, {self.duration}s")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du générateur audio: {e}")
            return False
    
    def set_output_path(self, path: str) -> None:
        """
        Définit le chemin de sortie pour l'audio
        
        Args:
            path: Chemin du fichier de sortie
        """
        self.output_path = path
        # Créer le répertoire de sortie si nécessaire
        output_dir = os.path.dirname(path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    def set_duration(self, duration: float) -> None:
        """
        Définit la durée de l'audio
        
        Args:
            duration: Durée en secondes
        """
        self.duration = duration
    
    def apply_trend_data(self, trend_data: TrendData) -> None:
        """
        Applique les données de tendances au générateur
        
        Args:
            trend_data: Données de tendances à appliquer
        """
        self.trend_data = trend_data
        
        # Extraire le BPM/beat frequency
        if 'beat_frequency' in trend_data.timing_trends:
            self.beat_frequency = trend_data.timing_trends['beat_frequency']
            logger.info(f"BPM appliqué: {60.0/self.beat_frequency} BPM")
        
        # Rechercher et télécharger automatiquement des musiques populaires
        self._auto_download_trending_music(trend_data)
    
    def _auto_download_trending_music(self, trend_data: TrendData) -> None:
        """
        Télécharge automatiquement des musiques tendance
        
        Args:
            trend_data: Données de tendances pour identifier les musiques populaires
        """
        try:
            # Identifier les musiques à télécharger basées sur les tendances
            songs_to_download = []
            
            # Si des musiques sont spécifiées dans les tendances
            if hasattr(trend_data, 'popular_music') and trend_data.popular_music:
                for music in trend_data.popular_music:
                    if isinstance(music, dict):
                        songs_to_download.append(music)
                    elif isinstance(music, str):
                        # Rechercher dans la base de données
                        found_song = self._find_song_in_db(music)
                        if found_song:
                            songs_to_download.append(found_song)
            
            # Si aucune musique spécifiée, prendre des musiques populaires par défaut
            if not songs_to_download:
                songs_to_download = self.popular_songs_db["trending"][:3]  # Top 3
            
            # Télécharger les musiques
            for song in songs_to_download:
                midi_path = self._download_midi_from_song_info(song)
                if midi_path:
                    self.background_music = midi_path
                    # Extraire la mélodie du MIDI
                    try:
                        self.current_melody = self._extract_melody_from_midi(midi_path)
                        logger.info(f"Mélodie extraite du MIDI: {self.current_melody}")
                        break  # Utiliser la première musique trouvée
                    except Exception as e:
                        logger.error(f"Erreur lors de l'extraction de la mélodie MIDI: {e}")
                        
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement automatique de musiques: {e}")
    
    def _find_song_in_db(self, query: str) -> Optional[Dict]:
        """
        Recherche une chanson dans la base de données
        
        Args:
            query: Requête de recherche
            
        Returns:
            Informations de la chanson trouvée ou None
        """
        query_lower = query.lower()
        
        # Rechercher dans toutes les catégories
        for category, songs in self.popular_songs_db.items():
            for song in songs:
                # Vérifier le titre et l'artiste
                if (query_lower in song["title"].lower() or 
                    query_lower in song["artist"].lower()):
                    return song
                
                # Vérifier les mots-clés
                for keyword in song["keywords"]:
                    if keyword.lower() in query_lower:
                        return song
        
        return None
    
    def _download_midi_from_song_info(self, song_info: Dict) -> Optional[str]:
        """
        Télécharge un fichier MIDI basé sur les informations de la chanson
        
        Args:
            song_info: Informations de la chanson
            
        Returns:
            Chemin du fichier MIDI téléchargé ou None
        """
        try:
            # Construire le nom de fichier pour le cache
            cache_key = f"{song_info['title']}_{song_info['artist']}".replace(" ", "_")
            cached_path = os.path.join(self.midi_dir, f"{cache_key}.mid")
            
            # Vérifier le cache
            if os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
                logger.info(f"MIDI trouvé dans le cache: {cached_path}")
                return cached_path
            
            # Télécharger depuis MuseScore
            midi_path = self._download_from_musescore(song_info["musescore_search"], cached_path)
            if midi_path:
                return midi_path
            
            # Télécharger depuis d'autres sources
            midi_path = self._download_from_alternative_sources(song_info, cached_path)
            if midi_path:
                return midi_path
            
            logger.warning(f"Impossible de télécharger le MIDI pour: {song_info['title']}")
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du MIDI: {e}")
            return None
    
    def _download_from_musescore(self, search_query: str, output_path: str) -> Optional[str]:
        """
        Télécharge un MIDI depuis MuseScore
        
        Args:
            search_query: Requête de recherche
            output_path: Chemin de sortie du fichier
            
        Returns:
            Chemin du fichier téléchargé ou None
        """
        try:
            # API MuseScore (exemple - l'API réelle peut différer)
            search_url = f"https://musescore.com/sheetmusic"
            params = {
                "text": search_query,
                "type": "score"
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            # Rechercher sur MuseScore
            response = requests.get(search_url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Recherche MuseScore échouée: {response.status_code}")
                return None
            
            # Parser la réponse pour trouver des liens MIDI
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Rechercher des liens vers des partitions
            score_links = soup.find_all('a', href=re.compile(r'/user/\d+/scores/\d+'))
            
            for link in score_links[:3]:  # Essayer les 3 premiers résultats
                score_url = urljoin("https://musescore.com", link.get('href'))
                midi_url = self._extract_midi_url_from_score(score_url)
                
                if midi_url:
                    # Télécharger le fichier MIDI
                    midi_response = requests.get(midi_url, headers=headers, timeout=30)
                    if midi_response.status_code == 200:
                        with open(output_path, 'wb') as f:
                            f.write(midi_response.content)
                        
                        # Vérifier que c'est un fichier MIDI valide
                        if self._is_valid_midi(output_path):
                            logger.info(f"MIDI téléchargé depuis MuseScore: {output_path}")
                            return output_path
                        else:
                            os.remove(output_path)
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement depuis MuseScore: {e}")
            return None
    
    def _extract_midi_url_from_score(self, score_url: str) -> Optional[str]:
        """
        Extrait l'URL du fichier MIDI depuis une page de partition MuseScore
        
        Args:
            score_url: URL de la page de partition
            
        Returns:
            URL du fichier MIDI ou None
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(score_url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            # Rechercher les liens MIDI dans la page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Rechercher les boutons de téléchargement MIDI
            midi_links = soup.find_all('a', href=re.compile(r'\.mid$|midi|download'))
            
            for link in midi_links:
                href = link.get('href')
                if href and '.mid' in href.lower():
                    return urljoin(score_url, href)
            
            # Rechercher dans les scripts JSON
            scripts = soup.find_all('script', type='application/json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if 'midi' in str(data).lower():
                        # Rechercher des URLs MIDI dans les données JSON
                        midi_url = self._extract_midi_from_json(data)
                        if midi_url:
                            return midi_url
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de l'URL MIDI: {e}")
            return None
    
    def _extract_midi_from_json(self, data: Any) -> Optional[str]:
        """
        Extrait une URL MIDI depuis des données JSON
        
        Args:
            data: Données JSON à analyser
            
        Returns:
            URL MIDI ou None
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(key, str) and 'midi' in key.lower():
                    if isinstance(value, str) and value.startswith('http'):
                        return value
                
                # Recherche récursive
                result = self._extract_midi_from_json(value)
                if result:
                    return result
        
        elif isinstance(data, list):
            for item in data:
                result = self._extract_midi_from_json(item)
                if result:
                    return result
        
        return None
    
    def _download_from_alternative_sources(self, song_info: Dict, output_path: str) -> Optional[str]:
        """
        Télécharge depuis des sources alternatives (BitMidi, etc.)
        
        Args:
            song_info: Informations de la chanson
            output_path: Chemin de sortie
            
        Returns:
            Chemin du fichier téléchargé ou None
        """
        try:
            # BitMidi
            bitmidi_url = f"https://bitmidi.com/search"
            params = {"q": f"{song_info['title']} {song_info['artist']}"}
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(bitmidi_url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Rechercher les liens de téléchargement MIDI
                midi_links = soup.find_all('a', href=re.compile(r'\.mid$'))
                
                for link in midi_links[:2]:  # Essayer les 2 premiers
                    midi_url = urljoin("https://bitmidi.com", link.get('href'))
                    
                    midi_response = requests.get(midi_url, headers=headers, timeout=30)
                    if midi_response.status_code == 200:
                        with open(output_path, 'wb') as f:
                            f.write(midi_response.content)
                        
                        if self._is_valid_midi(output_path):
                            logger.info(f"MIDI téléchargé depuis BitMidi: {output_path}")
                            return output_path
                        else:
                            os.remove(output_path)
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement depuis les sources alternatives: {e}")
            return None
    
    def _is_valid_midi(self, file_path: str) -> bool:
        """
        Vérifie si un fichier est un MIDI valide
        
        Args:
            file_path: Chemin du fichier à vérifier
            
        Returns:
            True si le fichier est un MIDI valide, False sinon
        """
        try:
            mid = mido.MidiFile(file_path)
            return len(mid.tracks) > 0
        except:
            return False
    
    def _extract_melody_from_midi(self, midi_path: str) -> List[int]:
        """
        Extrait une mélodie à partir d'un fichier MIDI
        
        Args:
            midi_path: Chemin du fichier MIDI
            
        Returns:
            Liste d'indices de notes (0-6 pour Do-Si)
        """
        try:
            mid = mido.MidiFile(midi_path)
            notes = []
            
            # Extraire les notes de toutes les pistes
            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Convertir la note MIDI en indice diatonique
                        midi_note = msg.note % 12  # Note dans l'octave (0-11)
                        
                        # Mapper vers la gamme diatonique majeure
                        # C=0, D=2, E=4, F=5, G=7, A=9, B=11
                        diatonic_map = {0: 0, 2: 1, 4: 2, 5: 3, 7: 4, 9: 5, 11: 6}
                        
                        # Trouver la note diatonique la plus proche
                        closest = min(diatonic_map.keys(), key=lambda x: abs(x - midi_note))
                        notes.append(diatonic_map[closest])
                        
                        # Limiter à 8 notes pour créer un motif
                        if len(notes) >= 8:
                            break
                
                if len(notes) >= 8:
                    break
            
            # Si pas assez de notes, compléter avec un motif par défaut
            if len(notes) < 8:
                default_pattern = [0, 2, 4, 5, 4, 2, 0, 2]
                notes.extend(default_pattern[len(notes):8])
            
            return notes[:8]
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de la mélodie MIDI: {e}")
            return self.current_melody
    
    def _download_music(self, url: str) -> Optional[str]:
        """
        Télécharge une musique depuis une URL
        
        Args:
            url: URL de la musique à télécharger
            
        Returns:
            Chemin du fichier téléchargé, ou None en cas d'échec
        """
        try:
            # Créer un nom de fichier unique
            filename = os.path.join(self.sounds_dir, f"trend_music_{int(time.time())}.mp3")
            
            # Télécharger le fichier
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Musique téléchargée: {filename}")
                return filename
            else:
                logger.error(f"Erreur lors du téléchargement de la musique: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement de la musique: {e}")
            return None
    
    def _extract_melody_from_file(self, file_path: str) -> List[int]:
        """
        Extrait une mélodie à partir d'un fichier audio
        
        Args:
            file_path: Chemin du fichier audio
            
        Returns:
            Liste d'indices de notes (0-6 pour Do-Si)
        """
        try:
            # Si c'est un fichier MIDI, utiliser la méthode MIDI
            if file_path.endswith('.mid') or file_path.endswith('.midi'):
                return self._extract_melody_from_midi(file_path)
            
            # Sinon, utiliser la méthode audio existante
            y, sr = librosa.load(file_path, sr=None, duration=30)
            
            # Extraire les pics d'énergie
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            peaks = librosa.util.peak_pick(onset_env, 
                                          pre_max=3, post_max=3, 
                                          pre_avg=3, post_avg=5, 
                                          delta=0.5, wait=10)
            
            if len(peaks) == 0:
                return self.current_melody
            
            # Extraire les hauteurs (pitches)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            
            # Sélectionner les hauteurs dominantes aux pics d'énergie
            melody = []
            for i in range(min(8, len(peaks))):
                peak_idx = peaks[i]
                peak_pitches = pitches[:, peak_idx]
                peak_mags = magnitudes[:, peak_idx]
                
                if np.sum(peak_mags) == 0:
                    melody.append(3)  # Fa (milieu de la gamme)
                else:
                    strongest_pitch_idx = np.argmax(peak_mags)
                    pitch_hz = peak_pitches[strongest_pitch_idx]
                    
                    if pitch_hz > 0:
                        midi_note = 12 * np.log2(pitch_hz / 440) + 69
                        note_idx = int(midi_note % 12)
                        
                        diatonic_map = {0: 0, 2: 1, 4: 2, 5: 3, 7: 4, 9: 5, 11: 6}
                        closest_diatonic = min(diatonic_map.keys(), key=lambda x: abs(x - note_idx))
                        melody.append(diatonic_map[closest_diatonic])
                    else:
                        melody.append(3)
            
            # Compléter si nécessaire
            while len(melody) < 8:
                if len(melody) == 0:
                    melody = [0, 2, 4, 5, 4, 2, 0, 2]
                else:
                    melody.append(melody[len(melody) % len(melody)])
            
            return melody
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de la mélodie: {e}")
            return self.current_melody
    
    def add_events(self, events: List[AudioEvent]) -> None:
        """
        Ajoute des événements audio à la timeline
        
        Args:
            events: Liste d'événements audio
        """
        self.events.extend(events)
        logger.info(f"{len(events)} événements audio ajoutés, total: {len(self.events)}")
    
    def _generate_basic_sounds(self) -> None:
        """Génère les sons de base (notes, effets, etc.)"""
        # Réinitialiser les listes
        self.notes = []
        self.effect_sounds = {}
        
        # Fréquences de base des notes (gamme de Do majeur)
        note_freqs = {
            0: 262,  # Do
            1: 294,  # Ré
            2: 330,  # Mi
            3: 349,  # Fa
            4: 392,  # Sol
            5: 440,  # La
            6: 494,  # Si
        }
        
        # Générer les notes pour différentes octaves
        logger.info("Génération des sons de notes...")
        for note_idx, freq in note_freqs.items():
            for octave, factor in enumerate([0.5, 1.0, 2.0]):
                note_freq = freq * factor
                note_path = os.path.join(self.sounds_dir, f"note_{note_idx}_oct{octave}.wav")
                
                # Vérifier si la note existe déjà
                if os.path.exists(note_path) and os.path.getsize(note_path) > 0:
                    self.notes.append((note_idx, octave, note_path))
                    continue
                
                # Générer la note
                self._generate_note(note_freq, note_path, note_idx, octave)
        
        # Générer les sons d'effets
        logger.info("Génération des sons d'effets...")
        self._generate_effect_sounds()
    
    def _generate_note(self, frequency: float, output_path: str, note_idx: int, octave: int) -> None:
        """
        Génère un son de note
        
        Args:
            frequency: Fréquence de la note en Hz
            output_path: Chemin du fichier de sortie
            note_idx: Indice de la note (0-6)
            octave: Octave (0-2)
        """
        try:
            # Paramètres
            duration = 0.5  # secondes
            sample_rate = self.sample_rate
            
            # Générer le signal
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            
            # Enveloppe ADSR
            attack = 0.1
            decay = 0.1
            sustain = 0.5
            release = 0.3
            
            # Générer l'enveloppe
            attack_samples = int(attack * sample_rate)
            decay_samples = int(decay * sample_rate)
            release_samples = int(release * sample_rate)
            sustain_samples = int(sample_rate * duration) - attack_samples - decay_samples - release_samples
            
            env = np.zeros(len(t))
            env[:attack_samples] = np.linspace(0, 1, attack_samples)
            env[attack_samples:attack_samples+decay_samples] = np.linspace(1, sustain, decay_samples)
            env[attack_samples+decay_samples:attack_samples+decay_samples+sustain_samples] = sustain
            env[attack_samples+decay_samples+sustain_samples:] = np.linspace(sustain, 0, release_samples)
            
            # Générer le son (sinusoïde avec harmoniques)
            signal = 0.7 * np.sin(2 * np.pi * frequency * t)  # Fondamentale
            signal += 0.2 * np.sin(2 * np.pi * frequency * 2 * t)  # 1ère harmonique
            signal += 0.1 * np.sin(2 * np.pi * frequency * 3 * t)  # 2ème harmonique
            
            # Appliquer l'enveloppe
            signal *= env
            
            # Normaliser
            signal = signal / np.max(np.abs(signal)) * 0.9
            
            # Convertir en stéréo
            stereo_signal = np.column_stack((signal, signal))
            
            # Sauvegarder en format WAV
            sf.write(output_path, stereo_signal, sample_rate)
            
            # Ajouter à la liste des notes
            self.notes.append((note_idx, octave, output_path))
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la note {note_idx} octave {octave}: {e}")
    
    def _generate_effect_sounds(self) -> None:
        """Génère les sons d'effets (explosion, activation, passage, etc.)"""
        # Sons d'explosion
        for size in ["small", "medium", "large"]:
            output_path = os.path.join(self.sounds_dir, f"explosion_{size}.wav")
            
            # Vérifier si le son existe déjà
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                if "explosion" not in self.effect_sounds:
                    self.effect_sounds["explosion"] = {}
                self.effect_sounds["explosion"][size] = output_path
                continue
            
            # Générer le son d'explosion
            try:
                # Paramètres selon la taille
                if size == "small":
                    duration = 0.5
                    base_freq = 100
                elif size == "medium":
                    duration = 0.7
                    base_freq = 80
                else:  # large
                    duration = 1.0
                    base_freq = 60
                
                sample_rate = self.sample_rate
                t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
                
                # Enveloppe rapide pour l'attaque, longue pour la décroissance
                env = np.ones(len(t))
                attack = int(0.05 * sample_rate)
                env[:attack] = np.linspace(0, 1, attack)
                env[int(0.2*len(t)):] = np.linspace(1, 0, len(t)-int(0.2*len(t)))
                
                # Bruit + sinusoïde grave
                noise = np.random.uniform(-1, 1, len(t))
                sine = np.sin(2 * np.pi * base_freq * t)
                
                # Mélanger bruit et sinusoïde
                signal = (0.7 * sine + 0.3 * noise) * env
                
                # Normaliser
                signal = signal / np.max(np.abs(signal)) * 0.9
                
                # Convertir en stéréo
                stereo_signal = np.column_stack((signal, signal))
                
                # Sauvegarder en format WAV
                sf.write(output_path, stereo_signal, sample_rate)
                
                # Ajouter au dictionnaire
                if "explosion" not in self.effect_sounds:
                    self.effect_sounds["explosion"] = {}
                self.effect_sounds["explosion"][size] = output_path
                
            except Exception as e:
                logger.error(f"Erreur lors de la génération du son d'explosion {size}: {e}")
        
        # Son d'activation
        activation_path = os.path.join(self.sounds_dir, "activation.wav")
        if not os.path.exists(activation_path) or os.path.getsize(activation_path) == 0:
            try:
                # Paramètres
                duration = 0.7
                sample_rate = self.sample_rate
                
                # Générer une rampe de fréquence ascendante
                t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
                freq = np.linspace(300, 1000, len(t))
                
                # Générer le signal
                phase = 2 * np.pi * np.cumsum(freq) / sample_rate
                signal = 0.8 * np.sin(phase)
                
                # Enveloppe
                env = np.ones(len(t))
                attack = int(0.1 * sample_rate)
                release = int(0.2 * sample_rate)
                env[:attack] = np.linspace(0, 1, attack)
                env[-release:] = np.linspace(1, 0, release)
                
                # Appliquer l'enveloppe
                signal *= env
                
                # Normaliser
                signal = signal / np.max(np.abs(signal)) * 0.9
                
                # Convertir en stéréo
                stereo_signal = np.column_stack((signal, signal))
                
                # Sauvegarder en format WAV
                sf.write(activation_path, stereo_signal, sample_rate)
                
                # Ajouter au dictionnaire
                self.effect_sounds["activation"] = {"default": activation_path}
                
            except Exception as e:
                logger.error(f"Erreur lors de la génération du son d'activation: {e}")
        else:
            self.effect_sounds["activation"] = {"default": activation_path}
        
        # Son de passage
        passage_path = os.path.join(self.sounds_dir, "passage.wav")
        if not os.path.exists(passage_path) or os.path.getsize(passage_path) == 0:
            try:
                # Paramètres
                duration = 0.3
                sample_rate = self.sample_rate
                
                # Générer un son bref avec une fréquence élevée
                t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
                freq = 1200
                
                # Générer le signal avec un vibrato
                vibrato_freq = 20
                vibrato_depth = 100
                freq_mod = freq + vibrato_depth * np.sin(2 * np.pi * vibrato_freq * t)
                phase = 2 * np.pi * np.cumsum(freq_mod) / sample_rate
                signal = 0.8 * np.sin(phase)
                
                # Enveloppe rapide
                env = np.ones(len(t))
                attack = int(0.05 * sample_rate)
                release = int(0.1 * sample_rate)
                env[:attack] = np.linspace(0, 1, attack)
                env[-release:] = np.linspace(1, 0, release)
                
                # Appliquer l'enveloppe
                signal *= env
                
                # Normaliser
                signal = signal / np.max(np.abs(signal)) * 0.9
                
                # Convertir en stéréo
                stereo_signal = np.column_stack((signal, signal))
                
                # Sauvegarder en format WAV
                sf.write(passage_path, stereo_signal, sample_rate)
                
                # Ajouter au dictionnaire
                self.effect_sounds["passage"] = {"default": passage_path}
                
            except Exception as e:
                logger.error(f"Erreur lors de la génération du son de passage: {e}")
        else:
            self.effect_sounds["passage"] = {"default": passage_path}
    
    def _get_sound_path(self, event: AudioEvent) -> Optional[str]:
        """
        Récupère le chemin du fichier son correspondant à un événement
        
        Args:
            event: Événement audio
            
        Returns:
            Chemin du fichier son, ou None si non trouvé
        """
        event_type = event.event_type
        params = event.params or {}
        
        if event_type == "note":
            note_idx = params.get("note", 0)
            octave = params.get("octave", 1)
            return os.path.join(self.sounds_dir, f"note_{note_idx}_oct{octave}.wav")
            
        elif event_type == "explosion":
            size = params.get("size", "medium")
            if "explosion" in self.effect_sounds and size in self.effect_sounds["explosion"]:
                return self.effect_sounds["explosion"][size]
            return os.path.join(self.sounds_dir, f"explosion_{size}.wav")
            
        elif event_type == "activation":
            if "activation" in self.effect_sounds:
                return self.effect_sounds["activation"]["default"]
            return os.path.join(self.sounds_dir, "activation.wav")
            
        elif event_type == "passage":
            if "passage" in self.effect_sounds:
                return self.effect_sounds["passage"]["default"]
            return os.path.join(self.sounds_dir, "passage.wav")
        
        # Type d'événement non géré
        logger.warning(f"Type d'événement audio non géré: {event_type}")
        return None
    
    def _add_beats_from_music(self) -> None:
        """Génère des événements beat à partir de la musique de fond"""
        if not self.background_music or not os.path.exists(self.background_music):
            return
        
        try:
            # Si c'est un fichier MIDI, extraire les beats différemment
            if self.background_music.endswith('.mid') or self.background_music.endswith('.midi'):
                self._add_beats_from_midi()
                return
            
            # Charger la musique audio
            y, sr = librosa.load(self.background_music, sr=None, duration=self.duration)
            
            # Détecter les beats
            _, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            
            # Créer des événements beat
            beat_events = []
            for i, beat_time in enumerate(beat_times):
                if beat_time <= self.duration:
                    # Alternance des notes sur les temps forts/faibles
                    note_idx = self.current_melody[i % len(self.current_melody)]
                    octave = 1 if i % 4 == 0 else 0  # Temps fort = octave plus haute
                    
                    event = AudioEvent(
                        event_type="note",
                        time=beat_time,
                        position=None,  # Pas de position spatiale pour les beats
                        params={"note": note_idx, "octave": octave}
                    )
                    beat_events.append(event)
            
            # Ajouter les événements
            self.events.extend(beat_events)
            logger.info(f"{len(beat_events)} événements beat extraits de la musique")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des beats: {e}")
    
    def _add_beats_from_midi(self) -> None:
        """Génère des événements beat à partir d'un fichier MIDI"""
        try:
            mid = mido.MidiFile(self.background_music)
            
            # Extraire les événements note_on avec timing
            beat_events = []
            current_time = 0.0
            ticks_per_beat = mid.ticks_per_beat
            
            for track in mid.tracks:
                current_time = 0.0
                
                for msg in track:
                    # Convertir les ticks en secondes (approximatif)
                    if hasattr(msg, 'time'):
                        current_time += mido.tick2second(msg.time, ticks_per_beat, 500000)  # 120 BPM par défaut
                    
                    if msg.type == 'note_on' and msg.velocity > 0 and current_time <= self.duration:
                        # Convertir la note MIDI en indice diatonique
                        midi_note = msg.note % 12
                        diatonic_map = {0: 0, 2: 1, 4: 2, 5: 3, 7: 4, 9: 5, 11: 6}
                        closest = min(diatonic_map.keys(), key=lambda x: abs(x - midi_note))
                        note_idx = diatonic_map[closest]
                        
                        # Déterminer l'octave basée sur la hauteur MIDI
                        octave = 1 if msg.note >= 60 else 0  # C4 = 60
                        
                        event = AudioEvent(
                            event_type="note",
                            time=current_time,
                            position=None,
                            params={"note": note_idx, "octave": octave}
                        )
                        beat_events.append(event)
                        
                        # Limiter le nombre d'événements pour éviter la surcharge
                        if len(beat_events) >= 100:
                            break
                
                if len(beat_events) >= 100:
                    break
            
            # Ajouter les événements
            self.events.extend(beat_events)
            logger.info(f"{len(beat_events)} événements beat extraits du MIDI")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des beats MIDI: {e}")
    
    def generate(self) -> Optional[str]:
        """
        Génère la piste audio finale
        
        Returns:
            Chemin de la piste audio générée, ou None en cas d'échec
        """
        try:
            # Générer les sons de base
            self._generate_basic_sounds()
            
            # Si pas d'événements mais musique de fond, extraire les beats
            if not self.events and self.background_music:
                self._add_beats_from_music()
            
            logger.info(f"Génération de la piste audio à partir de {len(self.events)} événements...")
            
            # Si aucun événement et pas de musique de fond, créer un fichier audio silencieux
            if not self.events and not self.background_music:
                logger.warning("Aucun événement audio et pas de musique de fond, création d'un fichier audio silencieux")
                return self._create_silent_audio()
            
            # Si musique de fond mais pas d'événements, utiliser directement la musique
            if self.background_music and not self.events:
                logger.info("Utilisation directe de la musique de fond")
                return self._use_background_music()
            
            # Créer la timeline audio
            timeline = np.zeros((int(self.sample_rate * self.duration), 2), dtype=np.float32)
            
            # Ajouter les événements sonores
            events_processed = 0
            for event in self.events:
                # Ignorer les événements hors de la durée
                if event.time >= self.duration:
                    continue
                
                # Récupérer le fichier son
                sound_path = self._get_sound_path(event)
                if not sound_path or not os.path.exists(sound_path):
                    continue
                
                try:
                    # Charger le son
                    if sound_path.endswith('.wav'):
                        data, sr = sf.read(sound_path)
                    else:
                        # Utiliser librosa pour d'autres formats
                        data, sr = librosa.load(sound_path, sr=self.sample_rate, mono=False)
                        if data.ndim == 1:  # Mono → stéréo
                            data = np.column_stack((data, data))
                    
                    # Vérifier que le son est bien en stéréo
                    if data.ndim == 1:  # Mono → stéréo
                        data = np.column_stack((data, data))
                    
                    # Calcul des indices dans la timeline
                    start_idx = int(event.time * self.sample_rate)
                    end_idx = min(start_idx + len(data), len(timeline))
                    data_len = end_idx - start_idx
                    
                    # Appliquer le volume selon le type d'événement
                    volume = 1.0
                    if event.event_type == "note":
                        volume = self.note_volume
                    elif event.event_type == "explosion":
                        volume = self.explosion_volume
                    elif event.event_type == "activation":
                        volume = self.activation_volume
                    elif event.event_type == "passage":
                        volume = self.passage_volume
                    
                    # Ajouter à la timeline
                    timeline[start_idx:end_idx] += data[:data_len] * volume
                    events_processed += 1
                    
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de l'événement audio {event.event_type}: {e}")
            
            # Mélanger avec la musique de fond si disponible
            if self.background_music and os.path.exists(self.background_music):
                timeline = self._mix_background_music(timeline)
            
            # Normaliser la timeline
            max_val = np.max(np.abs(timeline))
            if max_val > 1.0:
                timeline = timeline / max_val * 0.95  # Laisser une marge
            
            # Convertir en int16 pour le fichier WAV
            audio_data = (timeline * 32767).astype(np.int16)
            
            # Sauvegarder en format WAV
            wavfile.write(self.output_path, self.sample_rate, audio_data)
            
            logger.info(f"Piste audio générée avec succès: {self.output_path} ({events_processed}/{len(self.events)} événements traités)")
            return self.output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la piste audio: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_silent_audio(self) -> str:
        """
        Crée un fichier audio silencieux
        
        Returns:
            Chemin du fichier audio créé
        """
        # Créer un signal silencieux
        silence = np.zeros((int(self.sample_rate * self.duration), 2), dtype=np.float32)
        
        # Convertir en int16
        silence_int16 = (silence * 32767).astype(np.int16)
        
        # Sauvegarder en format WAV
        wavfile.write(self.output_path, self.sample_rate, silence_int16)
        
        return self.output_path
    
    def _use_background_music(self) -> str:
        """
        Utilise directement la musique de fond comme sortie
        
        Returns:
            Chemin du fichier audio créé
        """
        try:
            # Si c'est un fichier MIDI, le convertir en audio
            if self.background_music.endswith('.mid') or self.background_music.endswith('.midi'):
                return self._convert_midi_to_audio()
            
            # Charger la musique
            if self.background_music.endswith('.wav'):
                data, sr = sf.read(self.background_music)
            else:
                # Utiliser librosa pour d'autres formats
                data, sr = librosa.load(self.background_music, sr=self.sample_rate, mono=False)
            
            # Vérifier que c'est bien en stéréo
            if data.ndim == 1:  # Mono → stéréo
                data = np.column_stack((data, data))
            
            # Ajuster la durée
            if len(data) / sr > self.duration:
                # Couper si trop long
                data = data[:int(self.duration * sr)]
            elif len(data) / sr < self.duration:
                # Ajouter du silence si trop court
                padding = np.zeros((int(self.duration * sr) - len(data), 2), dtype=data.dtype)
                data = np.vstack((data, padding))
            
            # Normaliser
            if data.dtype == np.float32 or data.dtype == np.float64:
                max_val = np.max(np.abs(data))
                if max_val > 0:
                    data = data / max_val * 0.95
                
                # Convertir en int16
                data = (data * 32767).astype(np.int16)
            
            # Sauvegarder en format WAV
            wavfile.write(self.output_path, self.sample_rate, data)
            
            return self.output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de l'utilisation directe de la musique de fond: {e}")
            return self._create_silent_audio()
    
    def _convert_midi_to_audio(self) -> str:
        """
        Convertit un fichier MIDI en audio WAV
        
        Returns:
            Chemin du fichier audio créé
        """
        try:
            # Pour une conversion MIDI simple, on va synthétiser les notes
            mid = mido.MidiFile(self.background_music)
            
            # Créer la timeline audio
            timeline = np.zeros((int(self.sample_rate * self.duration), 2), dtype=np.float32)
            
            # Synthétiser chaque note
            current_time = 0.0
            ticks_per_beat = mid.ticks_per_beat
            
            for track in mid.tracks:
                current_time = 0.0
                
                for msg in track:
                    if hasattr(msg, 'time'):
                        current_time += mido.tick2second(msg.time, ticks_per_beat, 500000)
                    
                    if msg.type == 'note_on' and msg.velocity > 0 and current_time < self.duration:
                        # Synthétiser la note
                        note_freq = 440 * (2 ** ((msg.note - 69) / 12))  # Conversion MIDI vers fréquence
                        note_duration = 0.5  # Durée par défaut
                        
                        # Générer le signal de la note
                        start_sample = int(current_time * self.sample_rate)
                        end_sample = min(start_sample + int(note_duration * self.sample_rate), len(timeline))
                        
                        if start_sample < len(timeline):
                            samples = end_sample - start_sample
                            t = np.linspace(0, note_duration, samples, endpoint=False)
                            
                            # Signal sinusoïdal simple avec enveloppe
                            signal = 0.3 * np.sin(2 * np.pi * note_freq * t)
                            envelope = np.exp(-t * 3)  # Décroissance exponentielle
                            signal *= envelope
                            
                            # Ajouter à la timeline (stéréo)
                            stereo_signal = np.column_stack((signal, signal))
                            timeline[start_sample:end_sample] += stereo_signal
            
            # Normaliser
            max_val = np.max(np.abs(timeline))
            if max_val > 0:
                timeline = timeline / max_val * 0.95
            
            # Convertir en int16
            audio_data = (timeline * 32767).astype(np.int16)
            
            # Sauvegarder
            wavfile.write(self.output_path, self.sample_rate, audio_data)
            
            return self.output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la conversion MIDI vers audio: {e}")
            return self._create_silent_audio()
    
    def _mix_background_music(self, timeline: np.ndarray) -> np.ndarray:
        """
        Mélange la musique de fond avec la timeline existante
        
        Args:
            timeline: Timeline audio existante
            
        Returns:
            Timeline mixée
        """
        try:
            # Si c'est un fichier MIDI, le convertir d'abord
            if self.background_music.endswith('.mid') or self.background_music.endswith('.midi'):
                # Créer une timeline temporaire pour le MIDI
                midi_timeline = np.zeros_like(timeline)
                
                mid = mido.MidiFile(self.background_music)
                current_time = 0.0
                ticks_per_beat = mid.ticks_per_beat
                
                for track in mid.tracks:
                    current_time = 0.0
                    
                    for msg in track:
                        if hasattr(msg, 'time'):
                            current_time += mido.tick2second(msg.time, ticks_per_beat, 500000)
                        
                        if msg.type == 'note_on' and msg.velocity > 0 and current_time < self.duration:
                            note_freq = 440 * (2 ** ((msg.note - 69) / 12))
                            note_duration = 0.5
                            
                            start_sample = int(current_time * self.sample_rate)
                            end_sample = min(start_sample + int(note_duration * self.sample_rate), len(midi_timeline))
                            
                            if start_sample < len(midi_timeline):
                                samples = end_sample - start_sample
                                t = np.linspace(0, note_duration, samples, endpoint=False)
                                signal = 0.2 * np.sin(2 * np.pi * note_freq * t)
                                envelope = np.exp(-t * 3)
                                signal *= envelope
                                
                                stereo_signal = np.column_stack((signal, signal))
                                midi_timeline[start_sample:end_sample] += stereo_signal
                
                # Mélanger avec la timeline
                mixed_timeline = timeline + midi_timeline * 0.5
                return mixed_timeline
            
            # Traitement audio normal
            if self.background_music.endswith('.wav'):
                data, sr = sf.read(self.background_music)
            else:
                data, sr = librosa.load(self.background_music, sr=self.sample_rate, mono=False)
            
            # Vérifier que c'est bien en stéréo
            if data.ndim == 1:
                data = np.column_stack((data, data))
            
            # Convertir en float32 si nécessaire
            if data.dtype == np.int16:
                data = data.astype(np.float32) / 32767.0
            
            # Resample si nécessaire
            if sr != self.sample_rate:
                data = librosa.resample(data.T, orig_sr=sr, target_sr=self.sample_rate).T
            
            # Ajuster la durée
            if len(data) > len(timeline):
                data = data[:len(timeline)]
            elif len(data) < len(timeline):
                if len(data) > len(timeline) / 2:
                    padding = np.zeros((len(timeline) - len(data), 2), dtype=data.dtype)
                    data = np.vstack((data, padding))
                else:
                    repeats = int(np.ceil(len(timeline) / len(data)))
                    data = np.tile(data, (repeats, 1))[:len(timeline)]
            
            # Mélanger avec la timeline (70% musique, 100% effets)
            mixed_timeline = timeline + data * 0.7
            
            return mixed_timeline
            
        except Exception as e:
            logger.error(f"Erreur lors du mixage de la musique de fond: {e}")
            return timeline