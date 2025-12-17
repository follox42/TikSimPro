# src/audio_generators/viral_audio/mapping/progressive_builder.py
"""
Progressive Builder - Builds sound richness over time/bounces
More bounces = richer, fuller sound
"""

from typing import List, Dict


class ProgressiveBuilder:
    """
    Manages progressive sound building over bounces.

    Early bounces: Simple sounds (body + presence)
    More bounces: Richer sounds (all layers + harmonics)
    """

    # Layer unlock schedule (bounce count thresholds)
    LAYER_SCHEDULE = {
        'body': 0,      # Always active
        'presence': 0,  # Always active (critical for engagement!)
        'sub': 3,       # Unlock at bounce 3
        'air': 6,       # Unlock at bounce 6
        'tail': 10      # Unlock at bounce 10
    }

    # Harmonic richness stages
    RICHNESS_STAGES = [
        (0, 0.0),
        (5, 0.2),
        (10, 0.4),
        (20, 0.6),
        (30, 0.8),
        (50, 1.0)
    ]

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.bounce_count = 0

    def update(self, bounce_count: int):
        """Update bounce count"""
        self.bounce_count = bounce_count

    def get_active_layers(self) -> List[str]:
        """Get list of currently active layers"""
        if not self.enabled:
            return list(self.LAYER_SCHEDULE.keys())

        return [
            layer for layer, threshold in self.LAYER_SCHEDULE.items()
            if self.bounce_count >= threshold
        ]

    def get_harmonic_richness(self) -> float:
        """Get current harmonic richness (0.0 to 1.0)"""
        if not self.enabled:
            return 0.5

        for threshold, richness in reversed(self.RICHNESS_STAGES):
            if self.bounce_count >= threshold:
                return richness
        return 0.0

    def get_layer_volume(self, layer_name: str) -> float:
        """
        Get volume modifier for a layer.
        Newly unlocked layers fade in over 3 bounces.
        """
        if not self.enabled:
            return 1.0

        threshold = self.LAYER_SCHEDULE.get(layer_name, 0)
        bounces_since_unlock = self.bounce_count - threshold

        if bounces_since_unlock < 0:
            return 0.0
        elif bounces_since_unlock < 3:
            # Fade in over 3 bounces
            return (bounces_since_unlock + 1) / 3.0
        else:
            return 1.0
