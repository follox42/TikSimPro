# src/audio_generators/viral_audio/layers/presence.py
"""
Presence Layer - 2-6kHz for clarity and "tingle"
The magic 5kHz frequency for ASMR engagement (+45% engagement)
"""

import numpy as np


class PresenceLayer:
    """
    Generates the presence/tingle frequencies (2-6kHz).
    Research shows 5kHz is the "tingle" frequency for ASMR content.
    This layer is critical for viral engagement.
    """

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.freq_target = 5000  # The magic tingle frequency
        self.attack_ms = 0.5    # Ultra-fast for snap (<1ms)
        self.decay_ms = 50.0

    def generate(self, frequency: float, duration: float,
                 intensity: float = 1.0, richness: float = 0.0) -> np.ndarray:
        """Generate presence/tingle signal"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Target 5kHz with slight variation
        presence_freq = self.freq_target + (frequency - 200) * 5
        presence_freq = max(2000, min(6000, presence_freq))

        # Pure sine at presence frequency
        signal = np.sin(2 * np.pi * presence_freq * t)

        # Add transient "click" for snap
        click = self._generate_click(samples)
        signal = signal * 0.7 + click * 0.3

        # Add shimmer harmonics for ASMR
        if richness > 0.3:
            # Upper harmonics for sparkle
            signal += np.sin(2 * np.pi * presence_freq * 1.5 * t) * 0.15 * richness
            signal += np.sin(2 * np.pi * presence_freq * 2.0 * t) * 0.08 * richness

        # Apply ultra-fast envelope
        envelope = self._create_envelope(samples, intensity)
        signal = signal * envelope

        return signal.astype(np.float32)

    def _generate_click(self, samples: int) -> np.ndarray:
        """Generate transient click for snap (<1ms)"""
        click = np.zeros(samples)
        click_samples = min(int(0.0008 * self.sample_rate), samples)

        if click_samples > 0:
            # Sharp exponential decay
            click[:click_samples] = np.exp(-np.linspace(0, 12, click_samples))

        return click

    def _create_envelope(self, samples: int, intensity: float) -> np.ndarray:
        """Ultra-fast envelope for snap"""
        attack_ms = self.attack_ms
        attack_samples = max(1, int(attack_ms * self.sample_rate / 1000))
        decay_samples = int(self.decay_ms * self.sample_rate / 1000)

        envelope = np.zeros(samples)

        # Ultra-fast attack
        if attack_samples < samples:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

        # Brief peak
        peak_samples = min(int(0.008 * self.sample_rate), samples - attack_samples)
        envelope[attack_samples:attack_samples + peak_samples] = 1.0

        # Smooth decay
        decay_start = attack_samples + peak_samples
        if decay_samples > 0 and decay_start < samples:
            decay_len = min(decay_samples, samples - decay_start)
            decay = np.exp(-np.linspace(0, 5, decay_len))
            envelope[decay_start:decay_start + decay_len] = decay

        return envelope
