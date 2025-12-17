# src/audio_generators/simple_midi_audio_generator.py
"""
Simple audi generator for midi files.
"""

import numpy as np
import wave
import logging
import random
from typing import Dict, List, Any, Optional, Tuple
import os

from src.audio_generators.base_audio_generator import IAudioGenerator
from src.core.data_pipeline import TrendData, AudioEvent

logger = logging.getLogger("TikSimPro")

class SimpleMidiExtractor:
    """Extractor for midi files"""
    
    def extract_notes(self, midi_path: str) -> List[float]:
        """Extract notes from last track (melody) in a midi file"""
        try:
            import mido
            midi = mido.MidiFile(midi_path)
            notes = []

            # Extract from last track only (contains melody)
            last_track = midi.tracks[len(midi.tracks) - 1]
            for msg in last_track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Convert midi note to frequency
                    freq = 440.0 * (2 ** ((msg.note - 69) / 12))
                    notes.append(freq)

            logger.info(f"{len(notes)} melody notes extracted from {midi_path}")
            return notes

        except Exception as e:
            logger.error(f"Error MIDI: {e}")
            return self.get_default_melody()
    
    def get_default_melody(self) -> List[float]:
        """Default melody in C major"""
        # C major: C D E F G A B C
        return [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]

class AdvancedSoundGenerator:
    """Générateur de sons ultra-avancé pour créer tous types de sons"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.pi = np.pi
        
    # ===== FORMES D'ONDES DE BASE =====
    
    def generate_waveform(self, waveform_type: str, frequency: float, samples: int, 
                         phase: float = 0.0) -> np.ndarray:
        """Génère différents types de formes d'ondes"""
        t = np.linspace(0, samples / self.sample_rate, samples)
        
        if waveform_type == "sine":
            return np.sin(2 * self.pi * frequency * t + phase)
        elif waveform_type == "square":
            return np.sign(np.sin(2 * self.pi * frequency * t + phase))
        elif waveform_type == "sawtooth":
            return 2 * (t * frequency - np.floor(t * frequency + 0.5)) 
        elif waveform_type == "triangle":
            saw = 2 * (t * frequency - np.floor(t * frequency + 0.5))
            return 2 * np.abs(saw) - 1
        elif waveform_type == "pulse":
            return np.where(np.sin(2 * self.pi * frequency * t + phase) > 0, 1, -1)
        elif waveform_type == "noise":
            return np.random.uniform(-1, 1, samples)
        elif waveform_type == "pink_noise":
            return self._generate_pink_noise(samples)
        elif waveform_type == "brown_noise":
            return self._generate_brown_noise(samples)
        else:
            return np.sin(2 * self.pi * frequency * t + phase)
    
    def _generate_pink_noise(self, samples: int) -> np.ndarray:
        """Génère du bruit rose (1/f noise)"""
        white = np.random.normal(0, 1, samples)
        # Approximation simple du bruit rose
        pink = np.zeros(samples)
        pink[0] = white[0]
        for i in range(1, samples):
            pink[i] = white[i] * 0.5 + pink[i-1] * 0.3
        return pink / (np.max(np.abs(pink)) + 1e-8)
    
    def _generate_brown_noise(self, samples: int) -> np.ndarray:
        """Génère du bruit brun (Brownian noise)"""
        white = np.random.normal(0, 1, samples)
        brown = np.cumsum(white)
        return brown / (np.max(np.abs(brown)) + 1e-8)
    
    # ===== SYSTÈME D'HARMONIQUES AVANCÉ =====
    
    def add_harmonics(self, fundamental: np.ndarray, frequency: float, samples: int,
                     harmonics_config: List[Dict[str, Any]]) -> np.ndarray:
        """
        Ajoute des harmoniques personnalisables
        harmonics_config = [
            {"harmonic": 2, "amplitude": 0.5, "waveform": "sine", "phase": 0},
            {"harmonic": 3, "amplitude": 0.3, "waveform": "triangle", "phase": 0.5},
            ...
        ]
        """
        result = fundamental.copy()
        
        for harmonic_config in harmonics_config:
            harmonic_number = harmonic_config.get("harmonic", 2)
            amplitude = harmonic_config.get("amplitude", 0.5)
            waveform = harmonic_config.get("waveform", "sine")
            phase = harmonic_config.get("phase", 0.0)
            
            harmonic_freq = frequency * harmonic_number
            if harmonic_freq < self.sample_rate / 2:  # Évite l'aliasing
                harmonic_wave = self.generate_waveform(
                    waveform, harmonic_freq, samples, phase * 2 * self.pi
                )
                result += harmonic_wave * amplitude
        
        return result
    
    def add_subharmonics(self, fundamental: np.ndarray, frequency: float, samples: int,
                        subharmonics_config: List[Dict[str, Any]]) -> np.ndarray:
        """Ajoute des sous-harmoniques"""
        result = fundamental.copy()
        
        for sub_config in subharmonics_config:
            divisor = sub_config.get("divisor", 2)
            amplitude = sub_config.get("amplitude", 0.3)
            waveform = sub_config.get("waveform", "sine")
            phase = sub_config.get("phase", 0.0)
            
            sub_freq = frequency / divisor
            if sub_freq >= 20:  # Fréquence audible minimum
                sub_wave = self.generate_waveform(
                    waveform, sub_freq, samples, phase * 2 * self.pi
                )
                result += sub_wave * amplitude
        
        return result
    
    # ===== SYSTÈME D'ENVELOPPES AVANCÉ =====
    
    def create_adsr_envelope(self, samples: int, attack_ms: float = 10.0, 
                           decay_ms: float = 50.0, sustain_level: float = 0.7,
                           release_ms: float = 200.0, curve_type: str = "exponential") -> np.ndarray:
        """Enveloppe ADSR avec différents types de courbes"""
        envelope = np.ones(samples)
        
        # Conversion en échantillons
        attack_samples = max(1, int(attack_ms * self.sample_rate / 1000))
        decay_samples = max(1, int(decay_ms * self.sample_rate / 1000))
        release_samples = max(1, int(release_ms * self.sample_rate / 1000))
        
        # Ajustement des durées si nécessaire
        total_env = attack_samples + decay_samples + release_samples
        if total_env >= samples:
            ratio = samples / total_env * 0.9
            attack_samples = max(1, int(attack_samples * ratio))
            decay_samples = max(1, int(decay_samples * ratio))
            release_samples = max(1, int(release_samples * ratio))
        
        sustain_samples = samples - attack_samples - decay_samples - release_samples
        pos = 0
        
        # Attack
        if attack_samples > 0:
            if curve_type == "linear":
                attack_curve = np.linspace(0, 1, attack_samples)
            elif curve_type == "exponential":
                attack_curve = 1 - np.exp(-np.linspace(0, 5, attack_samples))
            elif curve_type == "logarithmic":
                attack_curve = np.log(np.linspace(1, np.e, attack_samples))
            else:  # sine
                attack_curve = np.sin(np.linspace(0, self.pi / 2, attack_samples))
            
            envelope[pos:pos + attack_samples] = attack_curve
            pos += attack_samples
        
        # Decay
        if decay_samples > 0:
            if curve_type == "linear":
                decay_curve = np.linspace(1, sustain_level, decay_samples)
            elif curve_type == "exponential":
                decay_curve = sustain_level + (1 - sustain_level) * np.exp(-np.linspace(0, 3, decay_samples))
            else:
                decay_curve = np.linspace(1, sustain_level, decay_samples)
            
            envelope[pos:pos + decay_samples] = decay_curve
            pos += decay_samples
        
        # Sustain
        if sustain_samples > 0:
            envelope[pos:pos + sustain_samples] = sustain_level
            pos += sustain_samples
        
        # Release
        if release_samples > 0:
            if curve_type == "exponential":
                release_curve = sustain_level * np.exp(-np.linspace(0, 5, release_samples))
            else:
                release_curve = sustain_level * np.cos(np.linspace(0, self.pi / 2, release_samples))
            
            envelope[pos:pos + release_samples] = release_curve
        
        return envelope
    
    def create_custom_envelope(self, samples: int, points: List[Tuple[float, float]]) -> np.ndarray:
        """
        Crée une enveloppe personnalisée à partir de points de contrôle
        points = [(time_ratio, amplitude), ...] où time_ratio est entre 0 et 1
        """
        envelope = np.ones(samples)
        
        if len(points) < 2:
            return envelope
        
        # Trie les points par temps
        points = sorted(points, key=lambda x: x[0])
        
        for i in range(len(points) - 1):
            start_time, start_amp = points[i]
            end_time, end_amp = points[i + 1]
            
            start_sample = int(start_time * samples)
            end_sample = int(end_time * samples)
            
            if start_sample < end_sample:
                segment_samples = end_sample - start_sample
                segment = np.linspace(start_amp, end_amp, segment_samples)
                envelope[start_sample:end_sample] = segment
        
        return envelope
    
    # ===== SYSTÈME DE TURBULENCES ET MODULATIONS =====
    
    def add_frequency_modulation(self, signal: np.ndarray, mod_frequency: float,
                               mod_depth: float, samples: int) -> np.ndarray:
        """Modulation de fréquence (vibrato)"""
        t = np.linspace(0, samples / self.sample_rate, samples)
        modulation = np.sin(2 * self.pi * mod_frequency * t) * mod_depth
        
        # Application de la modulation via interpolation
        result = np.zeros_like(signal)
        for i in range(samples):
            mod_index = i + modulation[i]
            if 0 <= mod_index < samples - 1:
                # Interpolation linéaire
                floor_idx = int(mod_index)
                frac = mod_index - floor_idx
                result[i] = signal[floor_idx] * (1 - frac) + signal[floor_idx + 1] * frac
            else:
                result[i] = signal[i]
        
        return result
    
    def add_amplitude_modulation(self, signal: np.ndarray, mod_frequency: float,
                               mod_depth: float, samples: int) -> np.ndarray:
        """Modulation d'amplitude (tremolo)"""
        t = np.linspace(0, samples / self.sample_rate, samples)
        modulation = 1 + mod_depth * np.sin(2 * self.pi * mod_frequency * t)
        return signal * modulation
    
    def add_turbulence(self, signal: np.ndarray, turbulence_config: Dict[str, Any]) -> np.ndarray:
        """
        Ajoute des turbulences/perturbations complexes
        turbulence_config = {
            "noise_type": "pink",
            "noise_amount": 0.1,
            "flutter_rate": 2.0,
            "flutter_depth": 0.05,
            "wow_rate": 0.3,
            "wow_depth": 0.02
        }
        """
        samples = len(signal)
        result = signal.copy()
        
        # Bruit de fond
        noise_type = turbulence_config.get("noise_type", "pink")
        noise_amount = turbulence_config.get("noise_amount", 0.1)
        if noise_amount > 0:
            noise = self.generate_waveform(noise_type, 0, samples)
            result += noise * noise_amount
        
        # Flutter (fluctuations rapides)
        flutter_rate = turbulence_config.get("flutter_rate", 2.0)
        flutter_depth = turbulence_config.get("flutter_depth", 0.05)
        if flutter_depth > 0:
            result = self.add_frequency_modulation(result, flutter_rate, flutter_depth, samples)
        
        # Wow (fluctuations lentes)
        wow_rate = turbulence_config.get("wow_rate", 0.3)
        wow_depth = turbulence_config.get("wow_depth", 0.02)
        if wow_depth > 0:
            result = self.add_frequency_modulation(result, wow_rate, wow_depth, samples)
        
        return result
    
    # ===== SYSTÈME DE FILTRES =====
    
    def apply_lowpass_filter(self, signal: np.ndarray, cutoff_freq: float, resonance: float = 0.7) -> np.ndarray:
        """Filtre passe-bas simple"""
        # Filtre IIR simple
        alpha = np.exp(-2 * self.pi * cutoff_freq / self.sample_rate)
        result = np.zeros_like(signal)
        result[0] = signal[0] * (1 - alpha)
        
        for i in range(1, len(signal)):
            result[i] = alpha * result[i-1] + (1 - alpha) * signal[i]
        
        # Ajout de résonance
        if resonance > 0:
            # Feedback simple pour la résonance
            for i in range(2, len(signal)):
                result[i] += resonance * 0.3 * (result[i-1] - result[i-2])
        
        return result
    
    def apply_highpass_filter(self, signal: np.ndarray, cutoff_freq: float) -> np.ndarray:
        """Filtre passe-haut simple"""
        alpha = np.exp(-2 * self.pi * cutoff_freq / self.sample_rate)
        result = np.zeros_like(signal)
        result[0] = signal[0]
        
        for i in range(1, len(signal)):
            result[i] = alpha * (result[i-1] + signal[i] - signal[i-1])
        
        return result
    
    def apply_bandpass_filter(self, signal: np.ndarray, low_freq: float, high_freq: float) -> np.ndarray:
        """Filtre passe-bande"""
        # Combinaison passe-haut et passe-bas
        high_passed = self.apply_highpass_filter(signal, low_freq)
        return self.apply_lowpass_filter(high_passed, high_freq)
    
    def apply_notch_filter(self, signal: np.ndarray, notch_freq: float, q_factor: float = 10) -> np.ndarray:
        """Filtre coupe-bande (notch)"""
        # Implémentation simple d'un filtre notch
        samples = len(signal)
        t = np.linspace(0, samples / self.sample_rate, samples)
        
        # Génération d'une sinusoïde à éliminer
        notch_signal = np.sin(2 * self.pi * notch_freq * t)
        
        # Soustraction avec facteur Q
        correlation = np.correlate(signal, notch_signal, mode='same')
        adjustment = correlation * notch_signal / (q_factor * len(signal))
        
        return signal - adjustment[:len(signal)]
    
    # ===== SYSTÈME D'EFFETS AVANCÉS =====
    
    def apply_reverb(self, signal: np.ndarray, room_size: float = 0.5, 
                    damping: float = 0.5, wet_level: float = 0.3) -> np.ndarray:
        """Réverbération simple"""
        samples = len(signal)
        
        # Délais multiples pour simuler la réverbération
        delays = [
            int(0.03 * self.sample_rate),   # 30ms
            int(0.05 * self.sample_rate),   # 50ms
            int(0.08 * self.sample_rate),   # 80ms
            int(0.12 * self.sample_rate),   # 120ms
        ]
        
        gains = [0.7, 0.5, 0.3, 0.2]
        
        reverb_signal = np.zeros(samples + max(delays))
        reverb_signal[:samples] = signal
        
        for delay, gain in zip(delays, gains):
            gain *= room_size
            for i in range(samples):
                if i + delay < len(reverb_signal):
                    reverb_signal[i + delay] += signal[i] * gain * (1 - damping)
        
        # Mixage wet/dry
        return signal * (1 - wet_level) + reverb_signal[:samples] * wet_level
    
    def apply_delay(self, signal: np.ndarray, delay_ms: float, feedback: float = 0.3,
                   wet_level: float = 0.3) -> np.ndarray:
        """Effet de délai/écho"""
        delay_samples = int(delay_ms * self.sample_rate / 1000)
        samples = len(signal)
        
        delayed_signal = np.zeros(samples + delay_samples)
        delayed_signal[:samples] = signal
        
        # Application du feedback
        for i in range(samples):
            if i + delay_samples < len(delayed_signal):
                delayed_signal[i + delay_samples] += signal[i] * feedback
                
                # Feedback récursif
                if i + 2 * delay_samples < len(delayed_signal):
                    delayed_signal[i + 2 * delay_samples] += signal[i] * feedback * feedback
        
        return signal * (1 - wet_level) + delayed_signal[:samples] * wet_level
    
    def apply_chorus(self, signal: np.ndarray, rate: float = 2.0, depth: float = 0.02,
                    mix: float = 0.5) -> np.ndarray:
        """Effet de chorus"""
        samples = len(signal)
        t = np.linspace(0, samples / self.sample_rate, samples)
        
        # Modulation de délai variable
        modulation = depth * np.sin(2 * self.pi * rate * t)
        
        chorus_signal = np.zeros_like(signal)
        for i in range(samples):
            delay_samples = modulation[i] * self.sample_rate
            delayed_idx = i - delay_samples
            
            if 0 <= delayed_idx < samples - 1:
                floor_idx = int(delayed_idx)
                frac = delayed_idx - floor_idx
                chorus_signal[i] = signal[floor_idx] * (1 - frac) + signal[floor_idx + 1] * frac
            else:
                chorus_signal[i] = signal[i]
        
        return signal * (1 - mix) + chorus_signal * mix
    
    def apply_distortion(self, signal: np.ndarray, drive: float = 2.0, tone: float = 0.5) -> np.ndarray:
        """Distorsion/saturation"""
        # Saturation douce (soft clipping)
        driven_signal = signal * drive
        
        # Fonction de saturation
        saturated = np.tanh(driven_signal)
        
        # Contrôle de tonalité (filtre simple)
        if tone < 0.5:
            # Plus sombre
            saturated = self.apply_lowpass_filter(saturated, 1000 + tone * 4000)
        else:
            # Plus brillant
            saturated = self.apply_highpass_filter(saturated, (tone - 0.5) * 500)
        
        return saturated * 0.7  # Compensation de volume
    
    def apply_bitcrusher(self, signal: np.ndarray, bits: int = 8, sample_rate_reduction: int = 1) -> np.ndarray:
        """Effet de dégradation numérique"""
        # Réduction de la résolution en bits
        max_val = 2 ** (bits - 1) - 1
        crushed = np.round(signal * max_val) / max_val
        
        # Réduction du taux d'échantillonnage
        if sample_rate_reduction > 1:
            decimated = crushed[::sample_rate_reduction]
            # Interpolation pour retrouver la taille originale
            crushed = np.interp(np.arange(len(signal)), 
                              np.arange(0, len(signal), sample_rate_reduction), 
                              decimated)
        
        return crushed
    
    # ===== GÉNÉRATEUR PRINCIPAL ULTRA-COMPLET =====
    
    def generate_advanced_sound(self, config: Dict[str, Any]) -> np.ndarray:
        """
        Générateur principal qui combine tous les éléments
        
        Exemple de config:
        {
            "frequency": 440.0,
            "duration": 1.0,
            "volume": 0.7,
            "waveform": "sine",
            
            "harmonics": [
                {"harmonic": 2, "amplitude": 0.5, "waveform": "sine"},
                {"harmonic": 3, "amplitude": 0.3, "waveform": "triangle"}
            ],
            
            "envelope": {
                "type": "adsr",
                "attack_ms": 10,
                "decay_ms": 100,
                "sustain_level": 0.7,
                "release_ms": 300,
                "curve_type": "exponential"
            },
            
            "modulation": {
                "fm_frequency": 5.0,
                "fm_depth": 0.1,
                "am_frequency": 3.0,
                "am_depth": 0.2
            },
            
            "turbulence": {
                "noise_type": "pink",
                "noise_amount": 0.05,
                "flutter_rate": 2.0,
                "flutter_depth": 0.02
            },
            
            "filters": [
                {"type": "lowpass", "cutoff": 2000, "resonance": 0.7},
                {"type": "highpass", "cutoff": 100}
            ],
            
            "effects": [
                {"type": "reverb", "room_size": 0.6, "wet_level": 0.3},
                {"type": "delay", "delay_ms": 125, "feedback": 0.2},
                {"type": "chorus", "rate": 1.5, "depth": 0.03}
            ]
        }
        """
        
        # Paramètres de base
        frequency = config.get("frequency", 440.0)
        duration = config.get("duration", 1.0)
        volume = config.get("volume", 0.7)
        waveform = config.get("waveform", "sine")
        
        samples = int(self.sample_rate * duration)
        
        # 1. Génération de l'onde de base
        signal = self.generate_waveform(waveform, frequency, samples)
        
        # 2. Ajout des harmoniques
        harmonics_config = config.get("harmonics", [])
        if harmonics_config:
            signal = self.add_harmonics(signal, frequency, samples, harmonics_config)
        
        # 3. Ajout des sous-harmoniques
        subharmonics_config = config.get("subharmonics", [])
        if subharmonics_config:
            signal = self.add_subharmonics(signal, frequency, samples, subharmonics_config)
        
        # 4. Application des modulations
        modulation = config.get("modulation", {})
        if "fm_frequency" in modulation:
            signal = self.add_frequency_modulation(
                signal, modulation["fm_frequency"], 
                modulation.get("fm_depth", 0.1), samples
            )
        if "am_frequency" in modulation:
            signal = self.add_amplitude_modulation(
                signal, modulation["am_frequency"], 
                modulation.get("am_depth", 0.2), samples
            )
        
        # 5. Ajout des turbulences
        turbulence = config.get("turbulence", {})
        if turbulence:
            signal = self.add_turbulence(signal, turbulence)
        
        # 6. Application des filtres
        filters = config.get("filters", [])
        for filter_config in filters:
            filter_type = filter_config.get("type", "lowpass")
            if filter_type == "lowpass":
                signal = self.apply_lowpass_filter(
                    signal, filter_config.get("cutoff", 1000),
                    filter_config.get("resonance", 0.7)
                )
            elif filter_type == "highpass":
                signal = self.apply_highpass_filter(
                    signal, filter_config.get("cutoff", 100)
                )
            elif filter_type == "bandpass":
                signal = self.apply_bandpass_filter(
                    signal, filter_config.get("low_freq", 100),
                    filter_config.get("high_freq", 1000)
                )
            elif filter_type == "notch":
                signal = self.apply_notch_filter(
                    signal, filter_config.get("notch_freq", 60),
                    filter_config.get("q_factor", 10)
                )
        
        # 7. Application de l'enveloppe
        envelope_config = config.get("envelope", {})
        if envelope_config.get("type") == "custom":
            points = envelope_config.get("points", [(0, 0), (0.1, 1), (0.9, 0.7), (1, 0)])
            envelope = self.create_custom_envelope(samples, points)
        else:
            # Enveloppe ADSR par défaut
            envelope = self.create_adsr_envelope(
                samples,
                envelope_config.get("attack_ms", 10),
                envelope_config.get("decay_ms", 100),
                envelope_config.get("sustain_level", 0.7),
                envelope_config.get("release_ms", 300),
                envelope_config.get("curve_type", "exponential")
            )
        
        signal *= envelope
        
        # 8. Application des effets
        effects = config.get("effects", [])
        for effect_config in effects:
            effect_type = effect_config.get("type", "reverb")
            if effect_type == "reverb":
                signal = self.apply_reverb(
                    signal, effect_config.get("room_size", 0.5),
                    effect_config.get("damping", 0.5),
                    effect_config.get("wet_level", 0.3)
                )
            elif effect_type == "delay":
                signal = self.apply_delay(
                    signal, effect_config.get("delay_ms", 125),
                    effect_config.get("feedback", 0.3),
                    effect_config.get("wet_level", 0.3)
                )
            elif effect_type == "chorus":
                signal = self.apply_chorus(
                    signal, effect_config.get("rate", 2.0),
                    effect_config.get("depth", 0.02),
                    effect_config.get("mix", 0.5)
                )
            elif effect_type == "distortion":
                signal = self.apply_distortion(
                    signal, effect_config.get("drive", 2.0),
                    effect_config.get("tone", 0.5)
                )
            elif effect_type == "bitcrusher":
                signal = self.apply_bitcrusher(
                    signal, effect_config.get("bits", 8),
                    effect_config.get("sample_rate_reduction", 1)
                )
        
        # 9. Application du volume final
        signal *= volume
        
        # 10. Normalisation et limitation
        max_val = np.max(np.abs(signal))
        if max_val > 1.0:
            signal = signal / max_val * 0.95  # Évite la saturation
        
        return signal
    
    # ===== PRESETS DE SONS AVANCÉS =====
    
    def satisfying_bounce(self, frequency: float, duration: float, volume: float = 0.6) -> np.ndarray:
        """Son de rebond satisfaisant avec le nouveau système"""
        config = {
            "frequency": frequency,
            "duration": duration,
            "volume": volume,
            "waveform": "sine",
            "harmonics": [
                {"harmonic": 2, "amplitude": 0.3, "waveform": "sine"},
                {"harmonic": 3, "amplitude": 0.15, "waveform": "triangle"}
            ],
            "envelope": {
                "type": "adsr",
                "attack_ms": 2,
                "decay_ms": 50,
                "sustain_level": 0.4,
                "release_ms": 200,
                "curve_type": "exponential"
            },
            "modulation": {
                "fm_frequency": 8.0,
                "fm_depth": 0.05
            },
            "turbulence": {
                "noise_type": "pink",
                "noise_amount": 0.02
            },
            "effects": [
                {"type": "reverb", "room_size": 0.3, "wet_level": 0.2}
            ]
        }
        return self.generate_advanced_sound(config)

    def asmr_pop(self, frequency: float = 300, duration: float = 0.2, volume: float = 0.5) -> np.ndarray:
        """Pop ASMR satisfaisant"""
        config = {
            "frequency": frequency,
            "duration": duration,
            "volume": volume,
            "waveform": "sine",
            "harmonics": [
                {"harmonic": 1.5, "amplitude": 0.4, "waveform": "triangle"}
            ],
            "envelope": {
                "type": "adsr",
                "attack_ms": 0.5,
                "decay_ms": 30,
                "sustain_level": 0.1,
                "release_ms": 60,
                "curve_type": "exponential"
            },
            "turbulence": {
                "noise_type": "pink",
                "noise_amount": 0.15
            },
            "filters": [
                {"type": "highpass", "cutoff": 150}
            ]
        }
        return self.generate_advanced_sound(config)

    def soft_chime(self, frequency: float = 523, duration: float = 0.8, volume: float = 0.4) -> np.ndarray:
        """Carillon doux"""
        config = {
            "frequency": frequency,
            "duration": duration,
            "volume": volume,
            "waveform": "sine",
            "harmonics": [
                {"harmonic": 2.4, "amplitude": 0.3, "waveform": "sine"},
                {"harmonic": 3.8, "amplitude": 0.2, "waveform": "sine"},
                {"harmonic": 5.2, "amplitude": 0.1, "waveform": "sine"}
            ],
            "envelope": {
                "type": "adsr",
                "attack_ms": 5,
                "decay_ms": 200,
                "sustain_level": 0.6,
                "release_ms": 400,
                "curve_type": "exponential"
            },
            "effects": [
                {"type": "reverb", "room_size": 0.7, "wet_level": 0.4}
            ]
        }
        return self.generate_advanced_sound(config)

    def water_drop(self, frequency: float, duration: float, volume: float = 0.5) -> np.ndarray:
        """Goutte d'eau"""
        config = {
            "frequency": frequency,
            "duration": duration,
            "volume": volume,
            "waveform": "sine",
            "harmonics": [
                {"harmonic": 2, "amplitude": 0.2, "waveform": "sine"}
            ],
            "envelope": {
                "type": "custom",
                "points": [(0, 0), (0.02, 1), (0.1, 0.3), (1, 0)]
            },
            "modulation": {
                "fm_frequency": 12.0,
                "fm_depth": 0.1
            },
            "filters": [
                {"type": "bandpass", "low_freq": 200, "high_freq": 2000}
            ],
            "effects": [
                {"type": "reverb", "room_size": 0.4, "wet_level": 0.3}
            ]
        }
        return self.generate_advanced_sound(config)

    def gentle_pluck(self, frequency: float, duration: float, volume: float = 0.4) -> np.ndarray:
        """Pincement doux"""
        config = {
            "frequency": frequency,
            "duration": duration,
            "volume": volume,
            "waveform": "triangle",
            "harmonics": [
                {"harmonic": 2, "amplitude": 0.3, "waveform": "sine"},
                {"harmonic": 3, "amplitude": 0.2, "waveform": "triangle"}
            ],
            "envelope": {
                "type": "adsr",
                "attack_ms": 1,
                "decay_ms": 150,
                "sustain_level": 0.3,
                "release_ms": 300,
                "curve_type": "exponential"
            },
            "filters": [
                {"type": "lowpass", "cutoff": 1500, "resonance": 0.3}
            ]
        }
        return self.generate_advanced_sound(config)

    def crystal_ting(self, frequency: float, duration: float, volume: float = 0.35) -> np.ndarray:
        """Tintement cristallin"""
        config = {
            "frequency": frequency,
            "duration": duration,
            "volume": volume,
            "waveform": "sine",
            "harmonics": [
                {"harmonic": 2.1, "amplitude": 0.4, "waveform": "sine"},
                {"harmonic": 3.3, "amplitude": 0.2, "waveform": "sine"},
                {"harmonic": 4.7, "amplitude": 0.1, "waveform": "sine"}
            ],
            "envelope": {
                "type": "adsr",
                "attack_ms": 2,
                "decay_ms": 300,
                "sustain_level": 0.4,
                "release_ms": 500,
                "curve_type": "exponential"
            },
            "modulation": {
                "am_frequency": 4.0,
                "am_depth": 0.1
            },
            "effects": [
                {"type": "reverb", "room_size": 0.8, "wet_level": 0.5},
                {"type": "chorus", "rate": 0.7, "depth": 0.02, "mix": 0.3}
            ]
        }
        return self.generate_advanced_sound(config)
    
    # Alias pour compatibilité
    def piano_note(self, frequency: float, duration: float = 0.5, volume: float = 0.7) -> np.ndarray:
        return self.gentle_pluck(frequency, duration, volume)
    
    def bell_note(self, frequency: float, duration: float = 0.8, volume: float = 0.6) -> np.ndarray:
        return self.crystal_ting(frequency, duration, volume)
    
    def soft_note(self, frequency: float, duration: float = 0.4, volume: float = 0.5) -> np.ndarray:
        return self.soft_chime(frequency, duration, volume)
    
    def percussion_hit(self, frequency: float = 200, duration: float = 0.2, volume: float = 0.8) -> np.ndarray:
        return self.asmr_pop(frequency, duration, volume)

    # ===== NOUVEAUX PRESETS ULTRA-SATISFAISANTS =====

    def ultra_satisfying_bounce(self, frequency: float, duration: float = 0.6, volume: float = 0.6) -> np.ndarray:
        """Rebond ultra-satisfaisant avec harmoniques riches et reverb longue"""
        config = {
            "frequency": frequency,
            "duration": duration,
            "volume": volume,
            "waveform": "sine",
            "harmonics": [
                {"harmonic": 2, "amplitude": 0.4, "waveform": "sine"},
                {"harmonic": 3, "amplitude": 0.2, "waveform": "sine"},
                {"harmonic": 4, "amplitude": 0.1, "waveform": "sine"},
                {"harmonic": 5, "amplitude": 0.05, "waveform": "triangle"}
            ],
            "subharmonics": [
                {"divisor": 2, "amplitude": 0.15, "waveform": "sine"}
            ],
            "envelope": {
                "type": "adsr",
                "attack_ms": 1,
                "decay_ms": 80,
                "sustain_level": 0.3,
                "release_ms": 400,
                "curve_type": "exponential"
            },
            "modulation": {
                "fm_frequency": 6.0,
                "fm_depth": 0.03
            },
            "effects": [
                {"type": "reverb", "room_size": 0.6, "damping": 0.3, "wet_level": 0.4},
                {"type": "chorus", "rate": 0.8, "depth": 0.01, "mix": 0.2}
            ]
        }
        return self.generate_advanced_sound(config)

    def deep_asmr_pop(self, frequency: float = 250, duration: float = 0.25, volume: float = 0.5) -> np.ndarray:
        """Pop profond ASMR avec sous-harmonique riche"""
        config = {
            "frequency": frequency,
            "duration": duration,
            "volume": volume,
            "waveform": "sine",
            "harmonics": [
                {"harmonic": 1.5, "amplitude": 0.5, "waveform": "triangle"}
            ],
            "subharmonics": [
                {"divisor": 2, "amplitude": 0.25, "waveform": "sine"}
            ],
            "envelope": {
                "type": "custom",
                "points": [(0, 0), (0.01, 1), (0.05, 0.6), (0.15, 0.2), (1, 0)]
            },
            "turbulence": {
                "noise_type": "pink",
                "noise_amount": 0.08
            },
            "filters": [
                {"type": "bandpass", "low_freq": 80, "high_freq": 800}
            ],
            "effects": [
                {"type": "reverb", "room_size": 0.5, "wet_level": 0.3}
            ]
        }
        return self.generate_advanced_sound(config)

    def velvet_chime(self, frequency: float = 523, duration: float = 1.0, volume: float = 0.4) -> np.ndarray:
        """Carillon velouté avec decay long"""
        config = {
            "frequency": frequency,
            "duration": duration,
            "volume": volume,
            "waveform": "sine",
            "harmonics": [
                {"harmonic": 2.2, "amplitude": 0.35, "waveform": "sine"},
                {"harmonic": 3.5, "amplitude": 0.25, "waveform": "sine"},
                {"harmonic": 5.1, "amplitude": 0.15, "waveform": "sine"},
                {"harmonic": 7.3, "amplitude": 0.08, "waveform": "sine"}
            ],
            "envelope": {
                "type": "adsr",
                "attack_ms": 3,
                "decay_ms": 250,
                "sustain_level": 0.5,
                "release_ms": 600,
                "curve_type": "exponential"
            },
            "modulation": {
                "am_frequency": 3.0,
                "am_depth": 0.08
            },
            "effects": [
                {"type": "reverb", "room_size": 0.8, "damping": 0.2, "wet_level": 0.5},
                {"type": "delay", "delay_ms": 80, "feedback": 0.15, "wet_level": 0.2}
            ]
        }
        return self.generate_advanced_sound(config)

    def bubble_pop(self, frequency: float = 400, duration: float = 0.15, volume: float = 0.55) -> np.ndarray:
        """Pop de bulle satisfaisant"""
        config = {
            "frequency": frequency,
            "duration": duration,
            "volume": volume,
            "waveform": "sine",
            "harmonics": [
                {"harmonic": 2, "amplitude": 0.3, "waveform": "sine"},
                {"harmonic": 3, "amplitude": 0.15, "waveform": "sine"}
            ],
            "envelope": {
                "type": "custom",
                "points": [(0, 0), (0.02, 1), (0.08, 0.4), (1, 0)]
            },
            "modulation": {
                "fm_frequency": 15.0,
                "fm_depth": 0.08
            },
            "filters": [
                {"type": "highpass", "cutoff": 120}
            ],
            "effects": [
                {"type": "reverb", "room_size": 0.4, "wet_level": 0.25}
            ]
        }
        return self.generate_advanced_sound(config)

# Alias pour compatibilité
SimpleSoundGenerator = AdvancedSoundGenerator

class SimpleMidiAudioGenerator(IAudioGenerator):
    """Generator for simple sound with midi file"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.output_path = "output/simple_midi_audio.wav"
        self.duration = 30.0
        
        # Composants
        self.midi_extractor = SimpleMidiExtractor()
        self.sound_gen = SimpleSoundGenerator(sample_rate)
        
        # État
        self.melody_notes = []
        self.events = []
        self.audio_data = None
        self.trend_data = None
        
        # Configuration avec nouveaux sons satisfaisants
        self.sound_types = [
            "satisfying_bounce", "asmr_pop", "soft_chime",
            "water_drop", "gentle_pluck", "crystal_ting",
            # Nouveaux presets ultra-satisfaisants
            "ultra_satisfying_bounce", "deep_asmr_pop",
            "velvet_chime", "bubble_pop"
        ]
        self.current_sound = "satisfying_bounce"
        self.volume = 0.5  # Volume plus doux pour les sons ASMR
        self.max_simultaneous_notes = 3  # Moins de superposition pour plus de clarté
        self.auto_volume_adjust = True    # Auto adjust volume
        
        logger.info("🎵 Générateur Audio Simple MIDI initialisé")
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """Simple configuration"""
        try:
            self.current_sound = config.get("sound_type")
            if not self.current_sound:
                self.current_sound = self.sound_types[random.randint(0, len(self.sound_types) - 1)]

            self.volume = config.get("volume", 0.7)
            self.max_simultaneous_notes = config.get("max_simultaneous_notes", 4)
            self.auto_volume_adjust = config.get("auto_volume_adjust", True)
            
            if self.current_sound not in self.sound_types:
                index = random.randint(0, len(self.sound_types) - 1)
                self.current_sound = self.sound_types[index]
            
            logger.info(f"Configuration: sound={self.current_sound}, volume={self.volume}")
            return True
            
        except Exception as e:
            logger.error(f"Error config: {e}")
            return False
    
    def select_music(self, musics: list):
        # Random selection
        index = random.randint(0, len(musics) - 1)
        return musics[index]

    def apply_trend_data(self, trend_data: TrendData) -> None:
        """Apply the tendance to the melody"""
        self.trend_data = trend_data
        
        midi_files = []
        # Look for a midi files
        if trend_data and trend_data.popular_music:
            for music in trend_data.popular_music:
                if 'file_path' in music:
                    file_path = music['file_path']
                    if file_path.endswith(('.mid', '.midi')):
                        midi_files.append(file_path)
        
        # Select the music
        musics_path = self.select_music(midi_files)
        self.melody_notes = self.midi_extractor.extract_notes(musics_path)
        logger.info(f"Melody loaded from {file_path}")

        if music:
            return
        
        # Midi file not found, using default melody
        self.melody_notes = self.midi_extractor.get_default_melody()
        logger.warning("Default melody used")
    
    def add_events(self, events: List[AudioEvent]) -> None:
        self.events.extend(events)
        logger.debug(f"Addes {len(events)} evenements")
    
    def generate(self) -> Optional[str]:
        """Generate audio inheritance"""
        try:
            logger.info("🎵 Starting simple generation..")
            
            # Audio buffer 
            total_samples = int(self.sample_rate * self.duration)
            self.audio_data = np.zeros(total_samples, dtype=np.float32)
            
            # Sélectionner un son aléatoire parmi les sons satisfaisants
            self.sound = random.choice(self.sound_types)
            logger.info(f"Sound type: {self.sound}")

            # Process events
            self._process_events()
            
            # Normalize and save
            self._normalize_and_save()
            
            logger.info(f"Generated audio: {self.output_path}")
            return self.output_path
            
        except Exception as e:
            logger.error(f"Error generation: {e}")
            return None
    
    def _process_events(self):
        """Process events and play the nites"""
        if not self.melody_notes:
            logger.warning("Unavailable melody")
            return

        note_index = 0

        active_notes_timeline = np.zeros(len(self.audio_data))

        for event in self.events:
            try:
                # Play a note on any interesting events
                if event.event_type in ["collision", "passage", "particle_bounce", "circle_activation", "countdown_beep"]:

                    # Go to the next note
                    frequency = self.melody_notes[note_index % len(self.melody_notes)]
                    note_index += 1
                    
                    # Smart calcule of the volume
                    start_sample = int(event.time * self.sample_rate)
                    
                    # Generate the sound for this note
                    sound = self._generate_sound(frequency, event)
                    
                    # Mange superposed sounds
                    end_sample = min(start_sample + len(sound), len(self.audio_data))

                    if start_sample < len(self.audio_data):
                        length = end_sample - start_sample
                        
                        # Count the simultanous active notes
                        if self.auto_volume_adjust:

                            region_activity = np.mean(np.abs(self.audio_data[start_sample:end_sample]))
                            volume_reduction = 1.0 / (1.0 + region_activity * 2)  # Progressive reduction
                            sound = sound * volume_reduction
                        
                        # Natural superposition
                        self.audio_data[start_sample:end_sample] += sound[:length]

            except Exception as e:
                logger.warning(f"Error event: {e}")

    def _generate_sound(self, frequency: float, event: AudioEvent) -> np.ndarray:
        """Génère un son satisfaisant selon le type configuré"""
        
        # Ajuster le volume et la durée selon l'événement
        volume = self.volume
        duration = 0.5  # Durée plus courte pour les sons ASMR
        
        if event.params:
            volume *= event.params.get("intensity", 1.0)
            volume *= event.params.get("volume", 1.0)
            duration *= event.params.get("duration", 1.0)
        
        # Générer le son selon le type
        if self.sound == "satisfying_bounce":
            return self.sound_gen.satisfying_bounce(frequency, duration, volume)
        elif self.sound == "asmr_pop":
            return self.sound_gen.asmr_pop(frequency, duration, volume)
        elif self.sound == "soft_chime":
            return self.sound_gen.soft_chime(frequency, duration, volume)
        elif self.sound == "water_drop":
            return self.sound_gen.water_drop(frequency, duration, volume)
        elif self.sound == "gentle_pluck":
            return self.sound_gen.gentle_pluck(frequency, duration, volume)
        elif self.sound == "crystal_ting":
            return self.sound_gen.crystal_ting(frequency, duration, volume)
        # Nouveaux presets ultra-satisfaisants
        elif self.sound == "ultra_satisfying_bounce":
            return self.sound_gen.ultra_satisfying_bounce(frequency, duration, volume)
        elif self.sound == "deep_asmr_pop":
            return self.sound_gen.deep_asmr_pop(frequency, duration, volume)
        elif self.sound == "velvet_chime":
            return self.sound_gen.velvet_chime(frequency, duration, volume)
        elif self.sound == "bubble_pop":
            return self.sound_gen.bubble_pop(frequency, duration, volume)
        else:
            # Fallback vers le son de rebond satisfaisant
            return self.sound_gen.satisfying_bounce(frequency, duration, volume)
    
    def _normalize_and_save(self):
        """Normalize and save the audio output"""
        
        # Step 1: Normalization
        max_val = np.max(np.abs(self.audio_data))

        if max_val > 1.0:
            # Soft compression to prevent clipping
            compression_ratio = 0.8 / max_val
            self.audio_data = self.audio_data * compression_ratio
            logger.info(f"Compression applied: {compression_ratio:.3f}")
        else:
            # Gentle amplification if the signal is too weak
            if 0 < max_val < 0.3:
                amplification = 0.7 / max_val
                self.audio_data = self.audio_data * amplification
                logger.info(f"Amplification applied: {amplification:.3f}")
        
        # Step 2: Apply smooth fade in/out (50 ms)
        fade_samples = int(0.05 * self.sample_rate)  # 50 ms fade duration
        if len(self.audio_data) > fade_samples * 2:
            # Smooth fade-in (sinusoidal)
            fade_in = np.sin(np.linspace(0, np.pi / 2, fade_samples)) ** 2
            self.audio_data[:fade_samples] *= fade_in

            # Smooth fade-out (cosine-based)
            fade_out = np.cos(np.linspace(0, np.pi / 2, fade_samples)) ** 2
            self.audio_data[-fade_samples:] *= fade_out

        # Step 3: Export as WAV file
        self._save_to_wav()

    def _save_to_wav(self):
        """Save the audio buffer to a WAV file"""
        
        try:
            # Convert float32 to 16-bit PCM
            audio_int16 = (self.audio_data * 32767).astype(np.int16)

            with wave.open(self.output_path, 'w') as wav_file:
                wav_file.setnchannels(1)         # Mono
                wav_file.setsampwidth(2)         # 16-bit samples
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            logger.info(f"WAV file saved: {self.output_path}")
        
        except Exception as e:
            logger.error(f"Error while saving WAV: {e}")
            raise
