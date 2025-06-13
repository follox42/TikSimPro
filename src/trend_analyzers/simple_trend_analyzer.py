# trend_analyzers/simple_trend_analyzer.py
"""
Simple Fixed Trend Analyzer for Physics Simulation Videos
"""

import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.trend_analyzers.base_trend_analyzer import ITrendAnalyzer, TrendData


class SimpleTrendAnalyzer(ITrendAnalyzer):
    """
    Simple trend analyzer with fixed viral hashtags for simulation videos
    Manages local music folder and provides optimized settings
    """
    
    def __init__(self, 
                 music_folder: str = "music",
                 cache_dir: str = "trend_cache",
                 region: str = "global",
                 hashtags: str = [
            # Core viral hashtags
            "fyp", "foryou", "viral", "trending", "tiktok",
            
            # Satisfying content hashtags  
            "satisfying", "oddlysatisfying", "satisfy", "mesmerizing", "hypnotic",
            
            # Physics/simulation hashtags
            "simulation", "physics", "bounce", "circles", "gravity", "motion",
            
            # Visual/aesthetic hashtags
            "animation", "visual", "geometric", "patterns", "colors", "rainbow",
            
            # Engagement hashtags
            "watchthis", "amazing", "wow", "mindblowing", "cool", "awesome",
            
            # Interactive hashtags
            "challenge", "test", "canyou", "howmany", "guess", "focus",
            
            # Trending descriptors
            "smooth", "perfect", "infinite", "endless", "loop", "relaxing",
            
            # Year/time-based
            "2025", "new", "latest", "trending2025", "viral2025"
        ]):
        """
        Initialize simple trend analyzer
        
        Args:
            music_folder: Path to folder containing music files (.mp3, .wav, .m4a)
            cache_dir: Directory for caching trend data
            region: Region for trends (not used in simple version, kept for compatibility)
        """
        self.music_folder = Path(music_folder)
        self.cache_dir = Path(cache_dir)
        self.region = region
        
        # Create directories if they don't exist
        self.music_folder.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Fixed viral hashtags optimized for physics simulation videos
        self.VIRAL_HASHTAGS = hashtags
        
        # Fixed color palettes optimized for satisfying content
        self.COLOR_PALETTES = {
            "rainbow": ["#FF0000", "#FF8000", "#FFFF00", "#80FF00", "#00FF00", 
                       "#00FF80", "#00FFFF", "#0080FF", "#0000FF", "#8000FF", "#FF00FF"],
            "tiktok_neon": ["#FF0050", "#00F2EA", "#FFFFFF", "#FE2C55", "#25F4EE"],
            "satisfying": ["#FFD700", "#FF6B35", "#FF1744", "#9C27B0", "#3F51B5", "#00BCD4"],
            "vibrant": ["#E91E63", "#FF5722", "#FF9800", "#4CAF50", "#2196F3", "#9C27B0"],
            "pastel": ["#FFB3E6", "#FFCCB3", "#B3FFB3", "#B3E6FF", "#D1B3FF"],
            "cosmic": ["#1A0033", "#4D0066", "#8000FF", "#CC00FF", "#FF00CC", "#FF3399"]
        }
        
        print(f"📁 Music folder: {self.music_folder.absolute()}")
        print(f"💾 Cache dir: {self.cache_dir.absolute()}")
        print(f"🎵 Available music files: {len(self._scan_music_files())}")
    
    def _scan_music_files(self) -> List[Dict[str, Any]]:
        """
        Scan music folder for audio files
        
        Returns:
            List of music file data
        """
        music_files = []
        supported_formats = ['.mp3', '.wav', '.m4a', '.ogg', '.flac']
        
        if not self.music_folder.exists():
            print(f"⚠️  Music folder not found: {self.music_folder}")
            return []
        
        for file_path in self.music_folder.iterdir():
            if file_path.suffix.lower() in supported_formats:
                # Extract basic info from filename
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
        
        return music_files

    def get_trending_hashtags(self, limit: int = 30) -> List[str]:
        """
        Get viral hashtags optimized for simulation videos
        
        Args:
            limit: Maximum number of hashtags to return
            
        Returns:
            List of trending hashtags
        """
        # Shuffle to get variety while keeping core hashtags
        hashtags = self.VIRAL_HASHTAGS.copy()
        random.shuffle(hashtags)
        
        # Always include essential hashtags at the beginning
        essential = ["fyp", "viral", "satisfying", "simulation"]
        result = essential.copy()
        
        # Add remaining hashtags up to limit
        for tag in hashtags:
            if tag not in result and len(result) < limit:
                result.append(tag)
        
        return result[:limit]
    
    def get_popular_music(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get popular music from local folder
        
        Args:
            limit: Maximum number of music tracks to return
            
        Returns:
            List of music data from local files
        """
        music_files = self._scan_music_files()
        
        if not music_files:
            # Return empty list if no music found
            print("⚠️  No music files found in folder")
            return []
        
        return music_files[:limit]
    
    def get_trend_analysis(self) -> TrendData:
        """
        Generate complete trend analysis for simulation videos
        
        Returns:
            TrendData optimized for physics simulation content
        """
        current_time = time.time()
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get hashtags and music
        hashtags = self.get_trending_hashtags(25)
        music = self.get_popular_music(15)
        
        # Select optimal color palette
        palette_name = random.choice(["rainbow", "tiktok_neon", "satisfying", "vibrant"])
        primary_colors = self.COLOR_PALETTES[palette_name]
        
        # Create comprehensive trend data
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
                    "caption_style": "question",
                    "engagement_strategy": "challenge_based"
                },
                "content": {
                    "question_texts": [
                        "Can you watch without blinking? 👀",
                        "How many circles can you count? 🔢", 
                        "Does this satisfy you? 😌",
                        "Can you escape all circles? 🎯",
                        "Watch till the end! What happens? 🤔"
                    ],
                    "cta_texts": [
                        "Follow for more satisfying content! 👆",
                        "Like if this satisfied you! ❤️",
                        "Share with someone who needs this! 📤",
                        "Comment your favorite part! 💬"
                    ]
                }
            }
        )
        
        # Cache the trend data
        self._cache_trend_data(trend_data)
        
        print(f"✅ Generated trend analysis:")
        print(f"   📊 {len(hashtags)} hashtags")
        print(f"   🎵 {len(music)} music files")
        print(f"   🎨 {palette_name} color palette")
        
        return trend_data
    
    def _cache_trend_data(self, trend_data: TrendData) -> None:
        """Save trend data to cache"""
        try:
            cache_file = self.cache_dir / f"trends_{datetime.now().strftime('%Y%m%d')}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(trend_data.to_json())
            print(f"💾 Cached trend data: {cache_file}")
        except Exception as e:
            print(f"⚠️  Failed to cache trend data: {e}")
    
    def add_music_file(self, file_path: str, artist: str = None, title: str = None) -> bool:
        """
        Add a music file to the music folder
        
        Args:
            file_path: Path to the music file to add
            artist: Artist name (optional)
            title: Song title (optional)
            
        Returns:
            True if file was added successfully
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                print(f"❌ File not found: {file_path}")
                return False
            
            # Create proper filename with artist and title
            if artist and title:
                filename = f"{artist} - {title}{source_path.suffix}"
            else:
                filename = source_path.name
            
            destination = self.music_folder / filename
            
            # Copy file to music folder
            import shutil
            shutil.copy2(source_path, destination)
            
            print(f"✅ Added music file: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add music file: {e}")
            return False
    
    def list_music_files(self) -> None:
        """Print all available music files"""
        music_files = self._scan_music_files()
        
        if not music_files:
            print("📂 No music files found")
            print(f"   Add .mp3, .wav, or .m4a files to: {self.music_folder.absolute()}")
            return
        
        print(f"🎵 Found {len(music_files)} music files:")
        for i, music in enumerate(music_files, 1):
            print(f"   {i:2d}. {music['artist']} - {music['title']}")
            print(f"       📁 {music['filename']} ({music['size_mb']} MB)")