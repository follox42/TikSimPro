# src/audio_generators/viral_audio/layers/air.py
"""
Air Layer - 8-16kHz for shimmer and brightness
Adds "air" and sparkle to the sound
"""

import numpy as np


class AirLayer:
    """
    Generates the air/shimmer frequencies (8-16kHz).
    Adds brightness and perceived quality to the sound.
    """

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.freq_center = 12000  # Hz
        self.attack_ms = 0.3      # Very fast
        self.decay_ms = 40.0

    def generate(self, frequency: float, duration: float,
                 intensity: float = 1.0, richness: float = 0.0) -> np.ndarray:
        """Generate air/shimmer signal"""
        samples = int(self.sample_rate * duration)

        # Filtered noise for natural air sound
        noise = np.random.uniform(-1, 1, samples)

        # Apply bandpass filter (simple IIR approximation)
        signal = self._bandpass_filter(noise, 8000, 16000)

        # Add subtle sine for tonal quality
        t = np.linspace(0, duration, samples)
        signal += np.sin(2 * np.pi * self.freq_center * t) * 0.3

        # Apply envelope
        envelope = self._create_envelope(samples, intensity)
        signal = signal * envelope

        # Normalize
        max_val = np.max(np.abs(signal))
        if max_val > 0:
            signal = signal / max_val

        return signal.astype(np.float32)

    def _bandpass_filter(self, signal: np.ndarray, low: float, high: float) -> np.ndarray:
        """Simple bandpass filter using FFT"""
        # FFT
        fft = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(len(signal), 1 / self.sample_rate)

        # Create bandpass mask
        mask = (freqs >= low) & (freqs <= high)

        # Apply with smooth rolloff
        fft_filtered = fft * mask

        # IFFT
        return np.fft.irfft(fft_filtered, len(signal))

    def _create_envelope(self, samples: int, intensity: float) -> np.ndarray:
        """Fast envelope for air"""
        attack_samples = max(1, int(self.attack_ms * self.sample_rate / 1000))
        decay_samples = int(self.decay_ms * self.sample_rate / 1000)

        envelope = np.zeros(samples)

        # Fast attack
        if attack_samples < samples:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

        # Decay
        decay_start = attack_samples
        if decay_samples > 0 and decay_start < samples:
            decay_len = min(decay_samples, samples - decay_start)
            decay = np.exp(-np.linspace(0, 4, decay_len))
            envelope[decay_start:decay_start + decay_len] = decay

        return envelope
