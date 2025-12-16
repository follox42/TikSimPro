# src/audio_generators/viral_audio/mapping/humanizer.py
"""
Humanizer - Adds subtle randomization for natural feel
Prevents robotic, mechanical sound
"""

import random
from typing import Dict


class Humanizer:
    """
    Adds subtle human-like variations to audio parameters.

    Variations:
    - Pitch: +/- 2% (barely noticeable, adds life)
    - Volume: +/- 5% (dynamic variation)
    - Timing: handled at event level
    """

    def __init__(self,
                 pitch_variance: float = 0.02,
                 volume_variance: float = 0.05):
        self.pitch_variance = pitch_variance
        self.volume_variance = volume_variance

    def humanize(self, params: Dict[str, float]) -> Dict[str, float]:
        """
        Apply humanization to audio parameters.

        Args:
            params: Audio parameters from velocity mapper

        Returns:
            Humanized parameters
        """
        result = params.copy()

        # Volume variation
        vol_mult = 1.0 + random.uniform(-self.volume_variance, self.volume_variance)
        result['volume'] = min(1.0, max(0.1, result['volume'] * vol_mult))

        # Pitch variation (stored as multiplier)
        pitch_mult = 1.0 + random.uniform(-self.pitch_variance, self.pitch_variance)
        result['pitch_multiplier'] = pitch_mult

        # Intensity variation
        int_var = random.uniform(-0.05, 0.05)
        result['intensity'] = min(1.0, max(0.0, result['intensity'] + int_var))

        return result
