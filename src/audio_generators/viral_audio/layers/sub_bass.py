# src/audio_generators/viral_audio/layers/sub_bass.py
"""
Sub Bass Layer - Deep 50-150Hz for physical impact
The "punch in the chest" feeling
"""

import numpy as np


class SubBassLayer:
    """
    Generates powerful sub-bass frequencies (50-150Hz).
    Creates the physical impact feeling in satisfying videos.
    """

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.freq_center = 80  # Hz - sweet spot for sub
        self.attack_ms = 5.0   # Slightly slower for natural bass
        self.decay_ms = 120.0

    def generate(self, frequency: float, duration: float,
                 intensity: float = 1.0, richness: float = 0.0) -> np.ndarray:
        """Generate sub bass signal"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Map to sub frequency range (50-150Hz)
        sub_freq = self.freq_center * (frequency / 200.0)
        sub_freq = max(50, min(150, sub_freq))

        # Pure sine for clean sub
        signal = np.sin(2 * np.pi * sub_freq * t)

        # Add first harmonic for punch (2x frequency)
        if richness > 0.2:
            harm_amp = 0.3 * richness
            signal += np.sin(2 * np.pi * sub_freq * 2 * t) * harm_amp

        # Apply envelope
        envelope = self._create_envelope(samples, intensity)
        signal = signal * envelope

        return signal.astype(np.float32)

    def _create_envelope(self, samples: int, intensity: float) -> np.ndarray:
        """Create punchy envelope for sub bass"""
        # Faster attack for harder hits
        attack_ms = self.attack_ms * (1.5 - intensity * 0.5)
        attack_samples = max(1, int(attack_ms * self.sample_rate / 1000))
        decay_samples = int(self.decay_ms * self.sample_rate / 1000)

        envelope = np.zeros(samples)

        # Attack - fast exponential
        if attack_samples > 0 and attack_samples < samples:
            attack = 1 - np.exp(-np.linspace(0, 5, attack_samples))
            envelope[:attack_samples] = attack

        # Decay - exponential fall
        decay_start = attack_samples
        if decay_samples > 0 and decay_start < samples:
            decay_len = min(decay_samples, samples - decay_start)
            decay = np.exp(-np.linspace(0, 4, decay_len))
            envelope[decay_start:decay_start + decay_len] = decay

        return envelope
