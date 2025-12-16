# src/audio_generators/viral_audio/layers/body.py
"""
Body Layer - 150-500Hz for warmth and presence
The main "tone" of the sound
"""

import numpy as np


class BodyLayer:
    """
    Generates the body frequencies (150-500Hz).
    Provides warmth and the main character of the sound.
    """

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.freq_center = 300  # Hz
        self.attack_ms = 1.5    # Fast for punch
        self.decay_ms = 80.0

    def generate(self, frequency: float, duration: float,
                 intensity: float = 1.0, richness: float = 0.0) -> np.ndarray:
        """Generate body signal"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Map to body frequency range
        body_freq = frequency * 1.5
        body_freq = max(150, min(500, body_freq))

        # Triangle wave for warmth
        signal = 2 * np.abs(2 * (t * body_freq - np.floor(t * body_freq + 0.5))) - 1

        # Add harmonics for richness
        if richness > 0.1:
            # 2nd harmonic
            signal += np.sin(2 * np.pi * body_freq * 2 * t) * 0.4 * richness
            # 3rd harmonic
            signal += np.sin(2 * np.pi * body_freq * 3 * t) * 0.2 * richness

        # Apply envelope
        envelope = self._create_envelope(samples, intensity)
        signal = signal * envelope

        return signal.astype(np.float32)

    def _create_envelope(self, samples: int, intensity: float) -> np.ndarray:
        """Create snappy envelope"""
        attack_ms = self.attack_ms * (1.3 - intensity * 0.3)
        attack_samples = max(1, int(attack_ms * self.sample_rate / 1000))
        decay_samples = int(self.decay_ms * self.sample_rate / 1000)

        envelope = np.zeros(samples)

        # Fast attack
        if attack_samples > 0 and attack_samples < samples:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

        # Peak hold briefly
        hold_samples = min(int(0.005 * self.sample_rate), samples - attack_samples)
        envelope[attack_samples:attack_samples + hold_samples] = 1.0

        # Decay
        decay_start = attack_samples + hold_samples
        if decay_samples > 0 and decay_start < samples:
            decay_len = min(decay_samples, samples - decay_start)
            decay = np.exp(-np.linspace(0, 4, decay_len))
            envelope[decay_start:decay_start + decay_len] = decay

        return envelope
