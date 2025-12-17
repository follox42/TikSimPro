# src/audio_generators/viral_audio/mapping/velocity_mapper.py
"""
Velocity Mapper - Maps physics velocity to audio parameters
Harder hits = louder, bassier sounds
"""

import math
from typing import Dict


class VelocityMapper:
    """
    Maps collision velocity from physics engine to audio parameters.

    Mapping:
    - Low velocity (<500 px/s) → Soft, higher frequency
    - Medium velocity (500-1000 px/s) → Normal, balanced
    - High velocity (>1000 px/s) → Loud, bass boost
    """

    def __init__(self, max_velocity: float = 1500.0):
        self.max_velocity = max_velocity
        self.min_velocity = 100.0

    def map(self, velocity: float) -> Dict[str, float]:
        """
        Map velocity to audio parameters.

        Args:
            velocity: Collision velocity in pixels/second

        Returns:
            Dict with: volume, intensity, bass_boost, attack_speed
        """
        # Normalize velocity (0.0 to 1.0)
        normalized = (velocity - self.min_velocity) / (self.max_velocity - self.min_velocity)
        normalized = max(0.0, min(1.0, normalized))

        # Volume: exponential curve for more dynamic range
        # Soft hits barely audible, hard hits PUNCH
        volume = normalized ** 1.3
        volume = 0.3 + volume * 0.7  # Range: 0.3 to 1.0

        # Intensity: affects sound character
        intensity = normalized

        # Bass boost: harder hits = more sub bass
        bass_boost = 1.0 + (normalized * 0.5)  # 1.0 to 1.5x

        # Attack speed: faster hits = snappier
        # Range: 1.0 (fast) to 0.5 (slow)
        attack_speed = 0.5 + normalized * 0.5

        # Presence boost: always important
        presence_boost = 1.0 + (normalized * 0.3)

        return {
            'volume': volume,
            'intensity': intensity,
            'bass_boost': bass_boost,
            'attack_speed': attack_speed,
            'presence_boost': presence_boost,
            'normalized_velocity': normalized
        }
