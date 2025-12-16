# src/audio_generators/viral_audio/layers/tail.py
"""
Tail Layer - Reverb/decay for space and depth
Adds room feel and sustain
"""

import numpy as np


class TailLayer:
    """
    Generates reverb/tail for space and depth.
    Makes sounds feel more natural and "roomy".
    """

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.room_size = 0.4    # 0-1
        self.damping = 0.6      # High frequency absorption
        self.wet_mix = 0.3      # Reverb amount

    def generate(self, frequency: float, duration: float,
                 intensity: float = 1.0, richness: float = 0.0) -> np.ndarray:
        """Generate reverb tail"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Create source impulse (brief tone burst)
        source_freq = max(200, min(800, frequency))
        source_duration = 0.02  # 20ms burst
        source_samples = min(int(source_duration * self.sample_rate), samples)

        source = np.zeros(samples)
        source[:source_samples] = np.sin(2 * np.pi * source_freq * t[:source_samples])
        source[:source_samples] *= np.exp(-np.linspace(0, 5, source_samples))

        # Apply simple reverb (multi-tap delay)
        reverb = self._apply_reverb(source)

        # Mix based on intensity
        wet_amount = self.wet_mix * (0.5 + intensity * 0.5)
        signal = source * (1 - wet_amount) + reverb * wet_amount

        return signal.astype(np.float32)

    def _apply_reverb(self, signal: np.ndarray) -> np.ndarray:
        """Simple multi-tap reverb"""
        samples = len(signal)
        reverb = np.zeros(samples)

        # Delay taps (in ms)
        delays_ms = [23, 37, 53, 79, 97, 127]
        decays = [0.7, 0.5, 0.35, 0.25, 0.18, 0.12]

        for delay_ms, decay in zip(delays_ms, decays):
            delay_samples = int(delay_ms * self.sample_rate / 1000)
            delay_samples = int(delay_samples * self.room_size * 2)

            if delay_samples < samples:
                # Apply damping (low-pass) to delayed signal
                delayed = np.zeros(samples)
                delayed[delay_samples:] = signal[:-delay_samples] if delay_samples > 0 else signal

                # Simple damping
                damped = self._apply_damping(delayed)

                reverb += damped * decay

        return reverb

    def _apply_damping(self, signal: np.ndarray) -> np.ndarray:
        """Apply high-frequency damping"""
        # Simple one-pole lowpass
        damped = np.zeros_like(signal)
        damped[0] = signal[0]

        alpha = self.damping
        for i in range(1, len(signal)):
            damped[i] = alpha * signal[i] + (1 - alpha) * damped[i - 1]

        return damped
