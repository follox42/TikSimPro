# src/audio_generators/satisfying_audio_generator.py
"""
Satisfying Audio Generator - Based on ASMR/TikTok viral sound research

Key principles:
- Short attack (<10ms), fast decay (50-200ms)
- Sub-bass rumble (50-100Hz) for depth
- Bright clarity (2-8kHz)
- No sustained tones - pops, clicks, pings
- One consistent sound per action type
- Melody notes played on collisions
"""

import numpy as np
import wave
import logging
import random
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from src.audio_generators.base_audio_generator import IAudioGenerator
from src.core.data_pipeline import TrendData, AudioEvent

logger = logging.getLogger("TikSimPro")


class SoundType(Enum):
    """Types de sons satisfaisants"""
    BOUNCE_POP = "bounce_pop"       # Pop satisfaisant pour rebonds
    PASSAGE_CHIME = "passage_chime" # Chime pour passages de layer
    IMPACT_THUD = "impact_thud"     # Impact sourd
    CELEBRATION = "celebration"      # Son de célébration


@dataclass
class SoundPreset:
    """Preset de son avec tous les paramètres"""
    name: str
    base_freq: float        # Fréquence de base (Hz)
    attack_ms: float        # Attaque (ms)
    decay_ms: float         # Decay (ms)
    release_ms: float       # Release (ms)
    sub_bass_amount: float  # Quantité de sub-bass (0-1)
    brightness: float       # Brillance haute fréquence (0-1)
    harmonics: List[float]  # Ratios d'harmoniques
    noise_amount: float     # Bruit (0-1)
    pitch_drop: float       # Chute de pitch (0-1)


# Presets de sons satisfaisants basés sur la recherche
SATISFYING_PRESETS = {
    SoundType.BOUNCE_POP: SoundPreset(
        name="Satisfying Pop",
        base_freq=220.0,        # A3 - fréquence agréable
        attack_ms=2.0,          # Attaque très rapide
        decay_ms=80.0,          # Decay court
        release_ms=120.0,       # Release moyen
        sub_bass_amount=0.4,    # Sub-bass présent mais pas dominant
        brightness=0.6,         # Assez brillant
        harmonics=[2.0, 3.0, 4.0],  # Harmoniques simples
        noise_amount=0.08,      # Légère texture
        pitch_drop=0.15         # Légère chute de pitch (satisfaisant)
    ),
    SoundType.PASSAGE_CHIME: SoundPreset(
        name="Gentle Chime",
        base_freq=523.25,       # C5 - chime aigu
        attack_ms=5.0,          # Attaque douce
        decay_ms=150.0,         # Decay plus long
        release_ms=300.0,       # Release long (résonance)
        sub_bass_amount=0.1,    # Peu de sub-bass
        brightness=0.8,         # Très brillant
        harmonics=[2.0, 3.0, 4.5, 6.0],  # Harmoniques de cloche
        noise_amount=0.02,      # Très peu de bruit
        pitch_drop=0.0          # Pas de chute
    ),
    SoundType.IMPACT_THUD: SoundPreset(
        name="Soft Thud",
        base_freq=80.0,         # Basse fréquence
        attack_ms=3.0,          # Rapide
        decay_ms=60.0,          # Court
        release_ms=100.0,       # Court
        sub_bass_amount=0.7,    # Beaucoup de sub-bass
        brightness=0.3,         # Peu brillant
        harmonics=[2.0],        # Simple
        noise_amount=0.15,      # Texture
        pitch_drop=0.3          # Chute de pitch prononcée
    ),
    SoundType.CELEBRATION: SoundPreset(
        name="Victory Sparkle",
        base_freq=880.0,        # A5 - aigu joyeux
        attack_ms=3.0,
        decay_ms=100.0,
        release_ms=400.0,
        sub_bass_amount=0.2,
        brightness=0.9,
        harmonics=[1.5, 2.0, 3.0, 4.0, 5.0],
        noise_amount=0.05,
        pitch_drop=-0.1         # Légère montée de pitch
    )
}


class SatisfyingSoundEngine:
    """Moteur de génération de sons satisfaisants"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.pi2 = 2 * np.pi

    def generate_sound(self, preset: SoundPreset, frequency: float = None,
                       duration: float = None, volume: float = 0.7) -> np.ndarray:
        """
        Génère un son satisfaisant basé sur un preset

        Args:
            preset: Le preset de son à utiliser
            frequency: Fréquence override (pour jouer des notes de mélodie)
            duration: Durée override en secondes
            volume: Volume (0-1)
        """
        freq = frequency if frequency else preset.base_freq

        # Calculer la durée totale
        total_ms = preset.attack_ms + preset.decay_ms + preset.release_ms
        dur = duration if duration else (total_ms / 1000.0)
        dur = max(dur, total_ms / 1000.0)  # Au moins la durée de l'enveloppe

        samples = int(dur * self.sample_rate)
        t = np.linspace(0, dur, samples)

        # 1. Générer la fondamentale avec pitch drop/rise
        pitch_env = self._create_pitch_envelope(samples, preset.pitch_drop)
        fundamental = np.sin(self.pi2 * freq * t * pitch_env)

        # 2. Ajouter les harmoniques
        signal = fundamental.copy()
        for i, harm_ratio in enumerate(preset.harmonics):
            harm_freq = freq * harm_ratio
            if harm_freq < self.sample_rate / 2:  # Éviter aliasing
                amplitude = 0.5 / (i + 2)  # Décroissance naturelle
                signal += amplitude * np.sin(self.pi2 * harm_freq * t * pitch_env)

        # 3. Ajouter sub-bass (50-100Hz)
        if preset.sub_bass_amount > 0:
            sub_freq = min(freq * 0.5, 80)  # Sub-bass
            sub_bass = preset.sub_bass_amount * 0.5 * np.sin(self.pi2 * sub_freq * t)
            signal += sub_bass

        # 4. Ajouter texture/bruit filtré
        if preset.noise_amount > 0:
            noise = self._generate_filtered_noise(samples, freq, preset.brightness)
            signal += noise * preset.noise_amount

        # 5. Appliquer l'enveloppe ADSR
        envelope = self._create_adsr_envelope(
            samples,
            preset.attack_ms,
            preset.decay_ms,
            0.3,  # Sustain level bas pour sons courts
            preset.release_ms
        )
        signal *= envelope

        # 6. Appliquer brillance (boost hautes fréquences)
        if preset.brightness > 0.5:
            signal = self._add_brightness(signal, preset.brightness)

        # 7. Soft limiting pour éviter distorsion
        signal = np.tanh(signal * 1.5) * 0.7

        # 8. Appliquer volume
        signal *= volume

        return signal.astype(np.float32)

    def _create_pitch_envelope(self, samples: int, pitch_drop: float) -> np.ndarray:
        """Crée une enveloppe de pitch (drop ou rise)"""
        if abs(pitch_drop) < 0.01:
            return np.ones(samples)

        # Courbe exponentielle pour le pitch
        t = np.linspace(0, 1, samples)
        if pitch_drop > 0:
            # Drop: commence haut, descend
            return 1.0 + pitch_drop * np.exp(-t * 8)
        else:
            # Rise: commence bas, monte
            return 1.0 + pitch_drop * (1 - np.exp(-t * 8))

    def _create_adsr_envelope(self, samples: int, attack_ms: float,
                              decay_ms: float, sustain: float,
                              release_ms: float) -> np.ndarray:
        """Crée une enveloppe ADSR avec courbes exponentielles"""
        envelope = np.zeros(samples)

        attack_samples = int(attack_ms * self.sample_rate / 1000)
        decay_samples = int(decay_ms * self.sample_rate / 1000)
        release_samples = int(release_ms * self.sample_rate / 1000)

        # Attack (courbe exponentielle)
        if attack_samples > 0:
            t = np.linspace(0, 1, attack_samples)
            attack_curve = 1 - np.exp(-t * 5)  # Courbe rapide
            envelope[:attack_samples] = attack_curve

        # Decay
        decay_start = attack_samples
        decay_end = min(decay_start + decay_samples, samples)
        if decay_end > decay_start:
            t = np.linspace(0, 1, decay_end - decay_start)
            decay_curve = sustain + (1 - sustain) * np.exp(-t * 4)
            envelope[decay_start:decay_end] = decay_curve

        # Release
        release_start = decay_end
        if release_start < samples:
            remaining = samples - release_start
            t = np.linspace(0, 1, remaining)
            release_curve = sustain * np.exp(-t * 3)
            envelope[release_start:] = release_curve

        return envelope

    def _generate_filtered_noise(self, samples: int, center_freq: float,
                                  brightness: float) -> np.ndarray:
        """Génère du bruit filtré autour de la fréquence centrale"""
        noise = np.random.normal(0, 1, samples)

        # Filtre passe-bande simple autour de center_freq
        # Plus brightness est haut, plus on garde les hautes fréquences
        cutoff_low = center_freq * 0.5
        cutoff_high = center_freq * (2 + brightness * 4)

        # FFT filtering
        fft = np.fft.rfft(noise)
        freqs = np.fft.rfftfreq(samples, 1/self.sample_rate)

        # Créer le filtre
        filter_mask = np.zeros_like(freqs)
        mask = (freqs >= cutoff_low) & (freqs <= cutoff_high)
        filter_mask[mask] = 1.0

        # Appliquer et retourner
        filtered = np.fft.irfft(fft * filter_mask, samples)
        return filtered / (np.max(np.abs(filtered)) + 1e-8)

    def _add_brightness(self, signal: np.ndarray, brightness: float) -> np.ndarray:
        """Ajoute de la brillance (boost hautes fréquences)"""
        # Simple high shelf boost via différentiation
        diff = np.diff(signal, prepend=signal[0])
        boost_amount = (brightness - 0.5) * 0.3
        return signal + diff * boost_amount


class MelodyPlayer:
    """Joue les notes de mélodie depuis un fichier MIDI"""

    def __init__(self):
        self.notes = []
        self.current_index = 0

    def load_midi(self, midi_path: str) -> bool:
        """Charge les notes depuis le dernier track du MIDI (mélodie)"""
        try:
            import mido
            midi = mido.MidiFile(midi_path)
            self.notes = []

            # Dernier track = mélodie
            if len(midi.tracks) > 0:
                last_track = midi.tracks[-1]
                for msg in last_track:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        freq = 440.0 * (2 ** ((msg.note - 69) / 12))
                        self.notes.append(freq)

            if not self.notes or len(self.notes) < 10:
                self._load_default_melody()

            self.current_index = 0
            logger.info(f"Loaded {len(self.notes)} melody notes from {midi_path}")
            return True

        except Exception as e:
            logger.error(f"Error loading MIDI: {e}")
            self._load_default_melody()
            return False

    def _load_default_melody(self):
        """Mélodie par défaut agréable (pentatonique)"""
        # Gamme pentatonique majeure - très satisfaisante
        self.notes = [
            261.63,  # C4
            293.66,  # D4
            329.63,  # E4
            392.00,  # G4
            440.00,  # A4
            523.25,  # C5
            587.33,  # D5
            659.25,  # E5
        ]
        logger.info("Using default pentatonic melody")

    def get_next_note(self) -> float:
        """Retourne la prochaine note de la mélodie"""
        if not self.notes:
            return 440.0  # A4 par défaut

        note = self.notes[self.current_index % len(self.notes)]
        self.current_index += 1
        return note

    def reset(self):
        """Remet la mélodie au début"""
        self.current_index = 0


class SatisfyingAudioGenerator(IAudioGenerator):
    """
    Générateur audio satisfaisant pour vidéos virales

    Principes:
    - Un son cohérent par type d'action
    - Notes de mélodie jouées sur les collisions
    - Sons courts et percussifs (pas de tons soutenus)
    - Sub-bass pour profondeur, hautes fréquences pour clarté
    """

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.duration = 30.0
        self.output_path = "output/satisfying_audio.wav"

        # Moteur de sons
        self.sound_engine = SatisfyingSoundEngine(sample_rate)
        self.melody_player = MelodyPlayer()

        # Audio buffer
        self.audio_data = None

        # Events
        self.events: List[AudioEvent] = []

        # Configuration - presets par défaut
        self.master_volume = 0.7
        self.bounce_preset = SATISFYING_PRESETS[SoundType.BOUNCE_POP]
        self.passage_preset = SATISFYING_PRESETS[SoundType.PASSAGE_CHIME]
        self.bounce_sound_name = "bounce_pop"
        self.passage_sound_name = "passage_chime"

        logger.info("SatisfyingAudioGenerator initialized")

    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure le générateur avec presets personnalisés"""
        try:
            self.master_volume = config.get("volume", 0.7)

            # Config depuis production_config (format dict avec preset)
            if "bounce_sound" in config and isinstance(config["bounce_sound"], dict):
                bounce_cfg = config["bounce_sound"]
                self.bounce_sound_name = bounce_cfg.get("name", "custom")
                if "preset" in bounce_cfg:
                    # Créer un SoundPreset depuis le dict
                    preset_dict = bounce_cfg["preset"]
                    self.bounce_preset = SoundPreset(
                        name=self.bounce_sound_name,
                        base_freq=preset_dict.get("base_freq", 220.0),
                        attack_ms=preset_dict.get("attack_ms", 2.0),
                        decay_ms=preset_dict.get("decay_ms", 80.0),
                        release_ms=preset_dict.get("release_ms", 120.0),
                        sub_bass_amount=preset_dict.get("sub_bass_amount", 0.4),
                        brightness=preset_dict.get("brightness", 0.6),
                        harmonics=preset_dict.get("harmonics", [2.0, 3.0]),
                        noise_amount=preset_dict.get("noise_amount", 0.08),
                        pitch_drop=preset_dict.get("pitch_drop", 0.15),
                    )

            if "passage_sound" in config and isinstance(config["passage_sound"], dict):
                passage_cfg = config["passage_sound"]
                self.passage_sound_name = passage_cfg.get("name", "custom")
                if "preset" in passage_cfg:
                    preset_dict = passage_cfg["preset"]
                    self.passage_preset = SoundPreset(
                        name=self.passage_sound_name,
                        base_freq=preset_dict.get("base_freq", 523.25),
                        attack_ms=preset_dict.get("attack_ms", 5.0),
                        decay_ms=preset_dict.get("decay_ms", 150.0),
                        release_ms=preset_dict.get("release_ms", 300.0),
                        sub_bass_amount=preset_dict.get("sub_bass_amount", 0.1),
                        brightness=preset_dict.get("brightness", 0.8),
                        harmonics=preset_dict.get("harmonics", [2.0, 3.0, 4.5]),
                        noise_amount=preset_dict.get("noise_amount", 0.02),
                        pitch_drop=preset_dict.get("pitch_drop", 0.0),
                    )

            logger.info(f"Configured: volume={self.master_volume}, bounce={self.bounce_sound_name}, passage={self.passage_sound_name}")
            return True

        except Exception as e:
            logger.error(f"Config error: {e}")
            return False

    def apply_trend_data(self, trend_data: TrendData) -> None:
        """Charge la mélodie depuis les données de tendance"""
        if trend_data and trend_data.popular_music:
            for music in trend_data.popular_music:
                if 'file_path' in music:
                    path = music['file_path']
                    if path.endswith(('.mid', '.midi')):
                        self.melody_player.load_midi(path)
                        return

        # Pas de MIDI trouvé, utiliser mélodie par défaut
        self.melody_player._load_default_melody()

    def load_midi(self, midi_path: str) -> bool:
        """Charge un fichier MIDI directement"""
        return self.melody_player.load_midi(midi_path)

    def add_events(self, events: List[AudioEvent]) -> None:
        """Ajoute des événements audio"""
        self.events.extend(events)
        logger.debug(f"Added {len(events)} events, total: {len(self.events)}")

    def set_output_path(self, path: str):
        """Définit le chemin de sortie"""
        self.output_path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def set_duration(self, duration: float):
        """Définit la durée de l'audio"""
        self.duration = duration

    def generate(self) -> Optional[str]:
        """Génère l'audio satisfaisant"""
        try:
            logger.info(f"Generating satisfying audio ({len(self.events)} events)...")

            # Créer le buffer audio
            total_samples = int(self.sample_rate * self.duration)
            self.audio_data = np.zeros(total_samples, dtype=np.float32)

            # Réinitialiser la mélodie
            self.melody_player.reset()

            # Trier les events par temps
            sorted_events = sorted(self.events, key=lambda e: e.time)

            # Traiter chaque event
            for event in sorted_events:
                self._process_event(event)

            # Normaliser
            self._normalize()

            # Sauvegarder
            self._save_wav()

            logger.info(f"Audio generated: {self.output_path}")
            return self.output_path

        except Exception as e:
            logger.error(f"Generation error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _process_event(self, event: AudioEvent):
        """Traite un événement audio"""
        start_sample = int(event.time * self.sample_rate)

        if start_sample >= len(self.audio_data):
            return

        # Déterminer le type de son et la fréquence
        if event.event_type == "collision":
            # Collision = note de mélodie avec son de rebond
            frequency = self.melody_player.get_next_note()
            preset = self.bounce_preset
            volume = min(0.8, event.params.get("volume", 0.6) + 0.2)

        elif event.event_type == "passage":
            # Passage = chime avec note de mélodie
            frequency = self.melody_player.get_next_note()
            preset = self.passage_preset
            volume = 0.7

        else:
            # Autres events = son de rebond standard
            frequency = self.melody_player.get_next_note()
            preset = self.bounce_preset
            volume = 0.5

        # Générer le son
        sound = self.sound_engine.generate_sound(
            preset,
            frequency=frequency,
            volume=volume * self.master_volume
        )

        # Mixer dans le buffer
        end_sample = min(start_sample + len(sound), len(self.audio_data))
        length = end_sample - start_sample

        if length > 0:
            self.audio_data[start_sample:end_sample] += sound[:length]

    def _normalize(self):
        """Normalise l'audio avec soft limiting"""
        if self.audio_data is None:
            return

        # Soft limiting
        self.audio_data = np.tanh(self.audio_data * 1.2) * 0.85

        # Normaliser si nécessaire
        max_val = np.max(np.abs(self.audio_data))
        if max_val > 0.95:
            self.audio_data = self.audio_data / max_val * 0.9

    def _save_wav(self):
        """Sauvegarde en fichier WAV"""
        if self.audio_data is None:
            return

        # Convertir en 16-bit
        audio_16bit = (self.audio_data * 32767).astype(np.int16)

        with wave.open(self.output_path, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(audio_16bit.tobytes())


# Fonction helper pour créer le générateur
def create_satisfying_generator(sample_rate: int = 44100) -> SatisfyingAudioGenerator:
    """Crée un générateur audio satisfaisant"""
    return SatisfyingAudioGenerator(sample_rate)
