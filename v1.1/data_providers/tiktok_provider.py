import os
import time
import json
import random
import logging
from datetime import datetime
from TikTokApi import TikTokApi

from data_providers.base_provider import BaseDataProvider

logger = logging.getLogger("TikSimPro")

class TikTokScraper(BaseDataProvider):
    """
    Scraper TikTok officiel pour tendances, hashtags et musiques (v5.x+ compatible)
    """
    def __init__(self, cache_dir="tiktok_data"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        self.trends_file = os.path.join(cache_dir, "trends.json")
        self.songs_file = os.path.join(cache_dir, "popular_songs.json")
        self.hashtags_file = os.path.join(cache_dir, "trending_hashtags.json")
        
        # Initialiser TikTokApi
        self.api = TikTokApi()
        logger.info("TikTok Scraper initialisé (v5.x TikTokApi)")

    def get_trending_hashtags(self, limit=30, refresh=False):
        if os.path.exists(self.hashtags_file) and not refresh:
            if time.time() - os.path.getmtime(self.hashtags_file) < 86400:
                return json.load(open(self.hashtags_file, 'r'))

        try:
            logger.info("Récupération des hashtags tendance TikTok...")
            trending = self.api.discover.hashtags()
            hashtags = [tag.challenge_info.challenge_name for tag in trending][:limit]

            json.dump(hashtags, open(self.hashtags_file, 'w'))
            logger.info(f"{len(hashtags)} hashtags récupérés.")
            return hashtags

        except Exception as e:
            logger.error(f"Erreur hashtags: {e}")
            return ["fyp", "foryou", "viral", "trending"]

    def get_popular_music(self, limit=20, refresh=False):
        if os.path.exists(self.songs_file) and not refresh:
            if time.time() - os.path.getmtime(self.songs_file) < 86400:
                return json.load(open(self.songs_file, 'r'))

        try:
            logger.info("Récupération des musiques populaires TikTok...")
            trending = self.api.discover.music()
            songs = [{
                "title": music.music_info.title,
                "artist": music.music_info.author_name,
                "url": music.music_info.play_url.uri
            } for music in trending][:limit]

            json.dump(songs, open(self.songs_file, 'w'))
            logger.info(f"{len(songs)} musiques récupérées.")
            return songs

        except Exception as e:
            logger.error(f"Erreur musiques: {e}")
            return [{
                "title": "STAY",
                "artist": "The Kid LAROI & Justin Bieber",
                "url": ""
            }]

    def get_trend_analysis(self, refresh=False):
        if os.path.exists(self.trends_file) and not refresh:
            if time.time() - os.path.getmtime(self.trends_file) < 86400:
                return json.load(open(self.trends_file, 'r'))

        logger.info("Analyse des tendances TikTok en cours...")

        hashtags = self.get_trending_hashtags()
        songs = self.get_popular_music()

        trend_analysis = {
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "popular_hashtags": hashtags[:10],
            "popular_music": [s["title"] for s in songs[:5]],
            "color_trends": {
                "dominant_palette": ["#FF0050", "#00F2EA", "#FFFFFF", "#FE2C55"]
            },
            "timing_trends": {
                "duration_trend": random.choice(["short", "medium", "long"]),
                "beat_frequency": random.choice([0.5, 1.0, 1.5, 2.0])
            },
            "recommended_settings": {
                "video_duration": 30,
                "beat_frequency": 1.0,
                "color_palette": ["#FF0050", "#00F2EA", "#FFFFFF", "#FE2C55"],
                "recommended_hashtags": hashtags[:10],
                "visual_elements": ["text_overlay", "sound_effects", "transitions"]
            }
        }

        json.dump(trend_analysis, open(self.trends_file, 'w'))
        logger.info("Analyse des tendances terminée.")
        return trend_analysis
