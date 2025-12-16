# src/trend_analyzers/gemini_trend_analyzer.py
"""
Gemini-powered Trend Analyzer using Vertex AI
Generates viral captions and optimizes hashtags with AI
"""

import time
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.trend_analyzers.base_trend_analyzer import ITrendAnalyzer
from src.core.data_pipeline import TrendData

logger = logging.getLogger("TikSimPro")


class GeminiTrendAnalyzer(ITrendAnalyzer):
    """
    Trend analyzer using Gemini (Vertex AI) for:
    - Generating viral captions
    - Optimizing hashtags
    - Creating engaging content suggestions

    Falls back to SimpleTrendAnalyzer defaults if Gemini fails.
    """

    def __init__(self,
                 project_id: str,
                 location: str = "us-central1",
                 model_id: str = "gemini-1.5-flash",
                 music_folder: str = "music",
                 cache_dir: str = "trend_cache",
                 region: str = "global",
                 hashtags: List[str] = None):
        """
        Initialize Gemini trend analyzer

        Args:
            project_id: Google Cloud project ID
            location: Vertex AI location (default: us-central1)
            model_id: Gemini model ID (default: gemini-1.5-flash)
            music_folder: Path to folder containing music files
            cache_dir: Directory for caching trend data
            region: Region for trends (kept for compatibility)
            hashtags: Base hashtags list (optional)
        """
        self.project_id = project_id
        self.location = location
        self.model_id = model_id
        self.music_folder = Path(music_folder)
        self.cache_dir = Path(cache_dir)
        self.region = region

        # Create directories if they don't exist
        self.music_folder.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize Vertex AI
        self.model = None
        self._init_vertex_ai()

        # Base viral hashtags (fallback)
        self.VIRAL_HASHTAGS = hashtags or [
            "fyp", "foryou", "viral", "trending", "tiktok",
            "satisfying", "oddlysatisfying", "satisfy", "mesmerizing", "hypnotic",
            "simulation", "physics", "bounce", "circles", "gravity", "motion",
            "animation", "visual", "geometric", "patterns", "colors", "rainbow",
            "watchthis", "amazing", "wow", "mindblowing", "cool", "awesome",
            "smooth", "perfect", "infinite", "endless", "loop", "relaxing",
            "2025", "new", "latest", "trending2025", "viral2025"
        ]

        # Color palettes
        self.COLOR_PALETTES = {
            "rainbow": ["#FF0000", "#FF8000", "#FFFF00", "#80FF00", "#00FF00",
                       "#00FF80", "#00FFFF", "#0080FF", "#0000FF", "#8000FF", "#FF00FF"],
            "tiktok_neon": ["#FF0050", "#00F2EA", "#FFFFFF", "#FE2C55", "#25F4EE"],
            "satisfying": ["#FFD700", "#FF6B35", "#FF1744", "#9C27B0", "#3F51B5", "#00BCD4"],
            "vibrant": ["#E91E63", "#FF5722", "#FF9800", "#4CAF50", "#2196F3", "#9C27B0"],
            "pastel": ["#FFB3E6", "#FFCCB3", "#B3FFB3", "#B3E6FF", "#D1B3FF"],
            "cosmic": ["#1A0033", "#4D0066", "#8000FF", "#CC00FF", "#FF00CC", "#FF3399"]
        }

        logger.info(f"GeminiTrendAnalyzer initialized")
        logger.info(f"Project: {project_id}, Location: {location}, Model: {model_id}")
        logger.info(f"Music folder: {self.music_folder.absolute()}")
        logger.info(f"Gemini model ready: {self.model is not None}")

    def _init_vertex_ai(self) -> bool:
        """
        Initialize Vertex AI and Gemini model

        Returns:
            True if initialization succeeded, False otherwise
        """
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            vertexai.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel(self.model_id)

            logger.info(f"Vertex AI initialized successfully")
            return True

        except ImportError:
            logger.error("google-cloud-aiplatform not installed. Run: pip install google-cloud-aiplatform")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            return False

    def _scan_music_files(self) -> List[Dict[str, Any]]:
        """
        Scan music folder for audio files

        Returns:
            List of music file data
        """
        music_files = []
        supported_formats = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.mid', '.midi']

        if not self.music_folder.exists():
            logger.warning(f"Music folder not found: {self.music_folder}")
            return []

        try:
            for file_path in self.music_folder.iterdir():
                if file_path.suffix.lower() in supported_formats:
                    name = file_path.stem
                    parts = name.split(' - ') if ' - ' in name else [name]

                    if len(parts) >= 2:
                        artist = parts[0].strip()
                        title = parts[1].strip()
                    else:
                        artist = "Unknown Artist"
                        title = name

                    music_data = {
                        "title": title,
                        "artist": artist,
                        "file_path": str(file_path.absolute()),
                        "filename": file_path.name,
                        "format": file_path.suffix.lower(),
                        "size_mb": round(file_path.stat().st_size / (1024*1024), 2),
                    }
                    music_files.append(music_data)

        except Exception as e:
            logger.error(f"Error scanning music folder: {e}")

        return music_files

    def generate_viral_caption(self, video_type: str = "physics_simulation") -> str:
        """
        Generate a viral caption using Gemini

        Args:
            video_type: Type of video content

        Returns:
            Generated viral caption or fallback
        """
        if not self.model:
            logger.warning("Gemini model not available, using fallback caption")
            return self._get_fallback_caption()

        try:
            prompt = f"""Generate a SHORT viral TikTok caption for a {video_type} video.

Requirements:
- Maximum 100 characters
- Create curiosity or engagement
- Use 1-2 emojis maximum
- No hashtags (they are added separately)
- English only

Styles to choose from (pick one randomly):
1. Question that creates curiosity: "Wait for it..." / "Can you guess what happens?"
2. Challenge: "Only 1% can watch without blinking"
3. Reaction bait: "This is so satisfying" / "I can't stop watching"
4. Mystery: "Watch till the end..."

Return ONLY the caption, nothing else."""

            response = self.model.generate_content(prompt)
            caption = response.text.strip()

            # Clean up the response
            caption = caption.strip('"\'')

            # Ensure it's not too long
            if len(caption) > 150:
                caption = caption[:147] + "..."

            logger.info(f"Generated viral caption: {caption}")
            return caption

        except Exception as e:
            logger.error(f"Error generating caption with Gemini: {e}")
            return self._get_fallback_caption()

    def _get_fallback_caption(self) -> str:
        """Get a fallback caption when Gemini fails"""
        fallback_captions = [
            "Wait for it...",
            "This is so satisfying",
            "Can you watch without blinking?",
            "I can't stop watching this",
            "Watch till the end!",
            "Only 1% can look away",
            "This hits different",
            "POV: You found the perfect video"
        ]
        return random.choice(fallback_captions)

    def generate_optimized_hashtags(self, base_hashtags: List[str] = None, count: int = 15) -> List[str]:
        """
        Generate optimized hashtags using Gemini

        Args:
            base_hashtags: Base hashtags to optimize
            count: Number of hashtags to generate

        Returns:
            List of optimized hashtags
        """
        if not self.model:
            return self._get_fallback_hashtags(count)

        try:
            base = base_hashtags or ["physics", "simulation", "satisfying"]

            prompt = f"""Generate {count} viral TikTok hashtags for a satisfying physics simulation video.

Base context: {', '.join(base[:5])}

Requirements:
- Mix of high-volume (fyp, viral) and niche (simulation, physics) hashtags
- Include trending 2025 hashtags
- No # symbol, just the words
- One hashtag per line
- English only

Return ONLY the hashtags, one per line."""

            response = self.model.generate_content(prompt)

            # Parse response
            hashtags = []
            for line in response.text.strip().split('\n'):
                tag = line.strip().strip('#').strip()
                if tag and len(tag) < 30:
                    hashtags.append(tag.lower())

            # Ensure we have enough hashtags
            if len(hashtags) < count:
                hashtags.extend(self._get_fallback_hashtags(count - len(hashtags)))

            logger.info(f"Generated {len(hashtags)} optimized hashtags")
            return hashtags[:count]

        except Exception as e:
            logger.error(f"Error generating hashtags with Gemini: {e}")
            return self._get_fallback_hashtags(count)

    def _get_fallback_hashtags(self, count: int = 15) -> List[str]:
        """Get fallback hashtags when Gemini fails"""
        essential = ["fyp", "viral", "satisfying", "simulation"]
        remaining = [h for h in self.VIRAL_HASHTAGS if h not in essential]
        random.shuffle(remaining)
        return (essential + remaining)[:count]

    def generate_question_texts(self, count: int = 5) -> List[str]:
        """
        Generate engaging question texts using Gemini

        Args:
            count: Number of questions to generate

        Returns:
            List of engaging questions
        """
        if not self.model:
            return self._get_fallback_questions()

        try:
            prompt = f"""Generate {count} SHORT engaging questions for a satisfying physics simulation video on TikTok.

Requirements:
- Maximum 40 characters each
- Create curiosity or challenge viewers
- Can include 1 emoji
- English only

Examples: "Can you count them all?", "Which one hits first?"

Return ONLY the questions, one per line."""

            response = self.model.generate_content(prompt)

            questions = []
            for line in response.text.strip().split('\n'):
                q = line.strip().strip('"\'')
                if q and len(q) < 60:
                    questions.append(q)

            if len(questions) < count:
                questions.extend(self._get_fallback_questions()[:count - len(questions)])

            return questions[:count]

        except Exception as e:
            logger.error(f"Error generating questions with Gemini: {e}")
            return self._get_fallback_questions()

    def _get_fallback_questions(self) -> List[str]:
        """Get fallback questions"""
        return [
            "Can you watch without blinking?",
            "How many circles can you count?",
            "Does this satisfy you?",
            "Can you escape all circles?",
            "Watch till the end!"
        ]

    def generate_cta_texts(self, count: int = 4) -> List[str]:
        """
        Generate call-to-action texts using Gemini

        Args:
            count: Number of CTAs to generate

        Returns:
            List of CTA texts
        """
        if not self.model:
            return self._get_fallback_ctas()

        try:
            prompt = f"""Generate {count} SHORT call-to-action texts for a TikTok video.

Requirements:
- Maximum 35 characters each
- Encourage follows, likes, shares, or comments
- Friendly and engaging tone
- Can include 1 emoji
- English only

Return ONLY the CTAs, one per line."""

            response = self.model.generate_content(prompt)

            ctas = []
            for line in response.text.strip().split('\n'):
                cta = line.strip().strip('"\'')
                if cta and len(cta) < 50:
                    ctas.append(cta)

            if len(ctas) < count:
                ctas.extend(self._get_fallback_ctas()[:count - len(ctas)])

            return ctas[:count]

        except Exception as e:
            logger.error(f"Error generating CTAs with Gemini: {e}")
            return self._get_fallback_ctas()

    def _get_fallback_ctas(self) -> List[str]:
        """Get fallback CTAs"""
        return [
            "Follow for more!",
            "Like if this satisfied you!",
            "Share with a friend!",
            "Comment your favorite part!"
        ]

    def get_trending_hashtags(self, limit: int = 30) -> List[str]:
        """
        Get viral hashtags optimized with Gemini

        Args:
            limit: Maximum number of hashtags to return

        Returns:
            List of trending hashtags
        """
        return self.generate_optimized_hashtags(count=limit)

    def get_popular_music(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get popular music from local folder

        Args:
            limit: Maximum number of music tracks to return

        Returns:
            List of music data from local files
        """
        try:
            music_files = self._scan_music_files()

            if not music_files:
                logger.warning("No music files found in folder")
                return []

            return music_files[:limit]

        except Exception as e:
            logger.error(f"Error getting popular music: {e}")
            return []

    def get_trend_analysis(self) -> TrendData:
        """
        Generate complete trend analysis with AI-generated content

        Returns:
            TrendData with AI-generated captions, hashtags, and suggestions
        """
        try:
            logger.info("Starting Gemini-powered trend analysis")

            current_time = time.time()
            current_date = datetime.now().strftime("%Y-%m-%d")

            # Generate AI content
            ai_caption = self.generate_viral_caption()
            hashtags = self.get_trending_hashtags(25)
            music = self.get_popular_music(15)
            question_texts = self.generate_question_texts(5)
            cta_texts = self.generate_cta_texts(4)

            # Select optimal color palette
            palette_name = random.choice(["rainbow", "tiktok_neon", "satisfying", "vibrant"])
            primary_colors = self.COLOR_PALETTES[palette_name]

            logger.debug(f"Selected color palette: {palette_name}")

            # Create comprehensive trend data with AI content
            trend_data = TrendData(
                timestamp=current_time,
                date=current_date,

                popular_hashtags=hashtags,
                popular_music=music,

                color_trends={
                    "primary_colors": primary_colors,
                    "palette_name": palette_name,
                    "all_palettes": self.COLOR_PALETTES,
                    "style": "satisfying_simulation"
                },

                recommended_settings={
                    "video": {
                        "color_palette": primary_colors,
                        "rotation_speed": random.randint(80, 150),
                        "particle_density": "high",
                        "effects": ["glow", "trails", "screen_shake"],
                        "background": "dark",
                        "contrast": "high"
                    },
                    "audio": {
                        "master_volume": 0.8,
                        "note_volume": 0.6,
                        "effect_volume": 0.4,
                        "sync_to_beat": True,
                        "reverb": 0.3
                    },
                    "publishing": {
                        "platforms": ["tiktok", "instagram", "youtube"],
                        "optimal_times": ["18:00", "19:30", "21:00"],
                        "caption_style": "ai_generated",
                        "engagement_strategy": "challenge_based"
                    },
                    "content": {
                        "ai_caption": ai_caption,
                        "ai_hashtags": hashtags,
                        "question_texts": question_texts,
                        "cta_texts": cta_texts
                    }
                }
            )

            # Cache the trend data
            self._cache_trend_data(trend_data)

            # Log success summary
            logger.info("Gemini trend analysis generated successfully")
            logger.info(f"AI Caption: {ai_caption}")
            logger.info(f"Hashtags: {len(hashtags)}")
            logger.info(f"Music files: {len(music)}")
            logger.info(f"Color palette: {palette_name}")

            return trend_data

        except Exception as e:
            logger.error(f"Error generating trend analysis: {e}")
            # Return minimal fallback data
            fallback_data = TrendData(
                timestamp=time.time(),
                date=datetime.now().strftime("%Y-%m-%d"),
                popular_hashtags=["fyp", "viral", "satisfying", "simulation"],
                popular_music=[],
                color_trends={"primary_colors": ["#FF0050", "#00F2EA", "#FFFFFF"]},
                recommended_settings={
                    "content": {
                        "ai_caption": "Amazing physics simulation!",
                        "ai_hashtags": ["fyp", "viral", "satisfying"],
                        "question_texts": self._get_fallback_questions(),
                        "cta_texts": self._get_fallback_ctas()
                    }
                }
            )
            logger.warning("Returning fallback trend data")
            return fallback_data

    def _cache_trend_data(self, trend_data: TrendData) -> None:
        """Save trend data to cache with proper UTF-8 encoding"""
        try:
            cache_file = self.cache_dir / f"trends_gemini_{datetime.now().strftime('%Y%m%d')}.json"

            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(trend_data.to_json())

            logger.info(f"Trend data cached successfully: {cache_file}")

        except Exception as e:
            logger.error(f"Failed to cache trend data: {e}")


# === UTILITIES ===

def create_gemini_trend_analyzer(project_id: str,
                                 location: str = "us-central1",
                                 model_id: str = "gemini-1.5-flash",
                                 music_folder: str = "music",
                                 cache_dir: str = "trend_cache") -> GeminiTrendAnalyzer:
    """
    Create a GeminiTrendAnalyzer with custom settings

    Args:
        project_id: Google Cloud project ID
        location: Vertex AI location
        model_id: Gemini model ID
        music_folder: Path to music folder
        cache_dir: Path to cache directory

    Returns:
        Configured GeminiTrendAnalyzer instance
    """
    return GeminiTrendAnalyzer(
        project_id=project_id,
        location=location,
        model_id=model_id,
        music_folder=music_folder,
        cache_dir=cache_dir
    )


if __name__ == "__main__":
    # Test the analyzer
    import os

    print("Testing GeminiTrendAnalyzer...")

    # Setup logging for test
    logging.basicConfig(level=logging.INFO)

    # Get project ID from environment or use placeholder
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id")

    if project_id == "your-project-id":
        print("WARNING: Set GOOGLE_CLOUD_PROJECT environment variable")
        print("Example: export GOOGLE_CLOUD_PROJECT=my-gcp-project")

    # Create analyzer
    analyzer = create_gemini_trend_analyzer(project_id=project_id)

    # Test trend analysis
    trend_data = analyzer.get_trend_analysis()

    print(f"\nGenerated caption: {trend_data.recommended_settings.get('content', {}).get('ai_caption')}")
    print(f"Hashtags: {trend_data.popular_hashtags[:5]}")

    print("\nTest completed!")
