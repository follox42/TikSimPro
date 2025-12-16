# src/audio_generators/viral_audio/effects/compressor.py
"""
Compressor - Dynamic range compression for punch and consistency
"""

import numpy as np


class Compressor:
    """
    Simple compressor for adding punch and controlling dynamics.
    """

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.threshold_db = -12.0
        self.ratio = 4.0
        self.attack_ms = 5.0
        self.release_ms = 50.0

    def process(self, signal: np.ndarray) -> np.ndarray:
        """Apply compression to signal"""
        if len(signal) == 0:
            return signal

        # Convert to absolute values for envelope following
        abs_signal = np.abs(signal)

        # Calculate attack and release coefficients
        attack_coef = np.exp(-1.0 / (self.attack_ms * self.sample_rate / 1000))
        release_coef = np.exp(-1.0 / (self.release_ms * self.sample_rate / 1000))

        # Envelope follower
        envelope = np.zeros_like(signal)
        envelope[0] = abs_signal[0]

        for i in range(1, len(signal)):
            if abs_signal[i] > envelope[i - 1]:
                envelope[i] = attack_coef * envelope[i - 1] + (1 - attack_coef) * abs_signal[i]
            else:
                envelope[i] = release_coef * envelope[i - 1] + (1 - release_coef) * abs_signal[i]

        # Convert threshold to linear
        threshold_lin = 10 ** (self.threshold_db / 20)

        # Calculate gain reduction
        gain = np.ones_like(signal)
        above_threshold = envelope > threshold_lin

        if np.any(above_threshold):
            # Calculate compression for samples above threshold
            over_db = 20 * np.log10(envelope[above_threshold] / threshold_lin + 1e-10)
            compressed_db = over_db / self.ratio
            gain_reduction_db = over_db - compressed_db
            gain[above_threshold] = 10 ** (-gain_reduction_db / 20)

        # Apply gain
        compressed = signal * gain

        # Makeup gain (compensate for compression)
        makeup_gain = 1.0 / (10 ** (self.threshold_db / 20 / self.ratio))
        makeup_gain = min(makeup_gain, 2.0)  # Limit makeup gain

        return compressed * makeup_gain
