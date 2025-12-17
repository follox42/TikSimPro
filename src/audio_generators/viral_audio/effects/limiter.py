# src/audio_generators/viral_audio/effects/limiter.py
"""
Limiter - Peak limiting to prevent clipping
"""

import numpy as np


class Limiter:
    """
    Simple brickwall limiter to prevent clipping.
    """

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.ceiling_db = -0.5  # Output ceiling
        self.release_ms = 100.0

    def process(self, signal: np.ndarray) -> np.ndarray:
        """Apply limiting to signal"""
        if len(signal) == 0:
            return signal

        ceiling_lin = 10 ** (self.ceiling_db / 20)
        release_coef = np.exp(-1.0 / (self.release_ms * self.sample_rate / 1000))

        # Find peaks above ceiling
        abs_signal = np.abs(signal)
        limited = signal.copy()

        # Envelope follower for smooth limiting
        gain = np.ones_like(signal)
        peak_hold = 0.0

        for i in range(len(signal)):
            # Update peak
            if abs_signal[i] > peak_hold:
                peak_hold = abs_signal[i]
            else:
                peak_hold = peak_hold * release_coef

            # Calculate gain if above ceiling
            if peak_hold > ceiling_lin:
                gain[i] = ceiling_lin / peak_hold
            else:
                gain[i] = 1.0

        # Apply gain
        limited = signal * gain

        # Hard clip as safety (should rarely trigger)
        limited = np.clip(limited, -ceiling_lin, ceiling_lin)

        return limited
