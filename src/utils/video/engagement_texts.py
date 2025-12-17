# src/utils/video/engagement_texts.py
"""
Engagement text templates for viral video content.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import random


class VideoType(Enum):
    """Types of videos with specific engagement texts"""
    GRAVITY_FALLS = "gravity_falls"
    ARC_ESCAPE = "arc_escape"
    GENERIC = "generic"


class EngagementTextManager:
    """
    Manages engagement text overlays for videos.
    Supports both templates and AI-generated texts.
    """

    # Template texts by video type and phase
    TEMPLATES = {
        VideoType.GRAVITY_FALLS: {
            "intro": [
                "Can the ball survive 60s?",
                "Guess the number of bounces!",
                "How big will it get?",
                "Watch till the end...",
                "Will it fill the circle?",
                "How many bounces?",
                "Can you count them all?",
                "Getting bigger every bounce!",
            ],
            "progress": [
                "Still going!",
                "Getting bigger!",
                "Can't stop watching",
                "Almost halfway!",
                "Keep counting!",
            ],
            "climax": [
                "TOO BIG!",
                "Almost there!",
                "Will it fit?",
                "So satisfying!",
                "Maximum size!",
            ]
        },
        VideoType.ARC_ESCAPE: {
            "intro": [
                "Can the ball escape in 60s?",
                "Guess the song!",
                "How many layers?",
                "Will it make it?",
                "Watch it escape!",
                "Count the layers!",
                "Can it break free?",
            ],
            "progress": [
                "Breaking through!",
                "Keep watching!",
                "Almost free!",
                "One more layer!",
                "So close!",
            ],
            "climax": [
                "ESCAPE!",
                "Finally free!",
                "It made it!",
                "FREEDOM!",
                "Incredible!",
            ]
        },
        VideoType.GENERIC: {
            "intro": [
                "Wait for it...",
                "Watch till the end!",
                "Can you guess what happens?",
                "This is so satisfying!",
                "Don't look away!",
            ],
            "progress": [
                "Keep watching!",
                "Almost there!",
                "Wait for it...",
            ],
            "climax": [
                "Amazing!",
                "So satisfying!",
                "Did you expect that?",
            ]
        }
    }

    def __init__(self, video_type: VideoType, ai_texts: Optional[Dict[str, List[str]]] = None):
        """
        Initialize engagement text manager.

        Args:
            video_type: Type of video for template selection
            ai_texts: Optional AI-generated texts to use instead of templates
        """
        self.video_type = video_type
        self.ai_texts = ai_texts or {}

        # Cache selected texts to maintain consistency within a video
        self._selected_intro: Optional[str] = None
        self._selected_progress: Optional[str] = None
        self._selected_climax: Optional[str] = None

    def get_intro_text(self) -> str:
        """Get intro text (first 4-5 seconds)"""
        if self._selected_intro:
            return self._selected_intro

        # Try AI-generated first
        if self.ai_texts.get("question_texts"):
            self._selected_intro = random.choice(self.ai_texts["question_texts"])
        else:
            # Fallback to templates
            templates = self.TEMPLATES.get(self.video_type, self.TEMPLATES[VideoType.GENERIC])
            self._selected_intro = random.choice(templates.get("intro", ["Watch this!"]))

        return self._selected_intro

    def get_progress_text(self) -> Optional[str]:
        """Get progress text (middle of video)"""
        if self._selected_progress:
            return self._selected_progress

        templates = self.TEMPLATES.get(self.video_type, self.TEMPLATES[VideoType.GENERIC])
        texts = templates.get("progress", [])

        if texts:
            self._selected_progress = random.choice(texts)
            return self._selected_progress
        return None

    def get_climax_text(self) -> Optional[str]:
        """Get climax text (end or special condition)"""
        if self._selected_climax:
            return self._selected_climax

        templates = self.TEMPLATES.get(self.video_type, self.TEMPLATES[VideoType.GENERIC])
        texts = templates.get("climax", [])

        if texts:
            self._selected_climax = random.choice(texts)
            return self._selected_climax
        return None

    def get_text_for_phase(self, progress: float, special_condition: bool = False) -> Optional[str]:
        """
        Get appropriate text based on video progress.

        Args:
            progress: Video progress from 0.0 to 1.0
            special_condition: If True, return climax text
        """
        if special_condition:
            return self.get_climax_text()

        if progress < 0.15:
            return self.get_intro_text()
        elif 0.4 < progress < 0.6:
            # Show progress text with 30% probability
            if random.random() < 0.3:
                return self.get_progress_text()
        elif progress > 0.9:
            return self.get_climax_text()

        return None

    def get_cta_text(self) -> str:
        """Get call-to-action text"""
        if self.ai_texts.get("cta_texts"):
            return random.choice(self.ai_texts["cta_texts"])

        default_ctas = [
            "Follow for more!",
            "Like if this satisfied you!",
            "Share with a friend!",
            "Comment your guess!",
        ]
        return random.choice(default_ctas)

    def reset(self) -> None:
        """Reset cached selections for a new video"""
        self._selected_intro = None
        self._selected_progress = None
        self._selected_climax = None

    @classmethod
    def from_trend_data(cls, video_type: VideoType, trend_data) -> 'EngagementTextManager':
        """
        Create EngagementTextManager from TrendData with AI-generated texts.

        Args:
            video_type: Type of video
            trend_data: TrendData object with recommended_settings
        """
        ai_texts = {}

        if trend_data and hasattr(trend_data, 'recommended_settings') and trend_data.recommended_settings:
            content = trend_data.recommended_settings.get("content", {})
            ai_texts = {
                "question_texts": content.get("question_texts", []),
                "cta_texts": content.get("cta_texts", [])
            }

        return cls(video_type, ai_texts)

    @classmethod
    def for_gravity_falls(cls, trend_data=None) -> 'EngagementTextManager':
        """Convenience method for GravityFalls videos"""
        if trend_data:
            return cls.from_trend_data(VideoType.GRAVITY_FALLS, trend_data)
        return cls(VideoType.GRAVITY_FALLS)

    @classmethod
    def for_arc_escape(cls, trend_data=None) -> 'EngagementTextManager':
        """Convenience method for ArcEscape videos"""
        if trend_data:
            return cls.from_trend_data(VideoType.ARC_ESCAPE, trend_data)
        return cls(VideoType.ARC_ESCAPE)
