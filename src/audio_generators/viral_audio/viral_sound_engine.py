# src/audio_generators/viral_audio/viral_sound_engine.py
"""
Viral Sound Engine - Main audio generator for TikTok physics simulations
Optimized for viral, satisfying sounds with 5-layer architecture
"""

import numpy as np
import wave
import logging
import os
import json
import random
from typing import Dict, List, Any, Optional
from pathlib import Path

from src.audio_generators.base_audio_generator import IAudioGenerator
from src.core.data_pipeline import TrendData, AudioEvent

from .layers import SubBassLayer, BodyLayer, PresenceLayer, AirLayer, TailLayer
from .mapping import VelocityMapper, ProgressiveBuilder, Humanizer
from .effects import Compressor, Limiter

logger = logging.getLogger("TikSimPro")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class SimpleMidiExtractor:
    """Extractor for midi files with tempo support"""

    def __init__(self):
        self.last_bpm = 120.0  # Default BPM

    def extract_notes(self, midi_path: str) -> List[float]:
        """Extract every notes in a midi file with mido"""
        try:
            import mido
            midi = mido.MidiFile(midi_path)
            notes = []

            for track in midi.tracks:
                for msg in track:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Convert midi note to frequency
                        freq = 440.0 * (2 ** ((msg.note - 69) / 12))
                        notes.append(freq)

            logger.info(f"{len(notes)} notes extracted from {midi_path}")
            return notes

        except Exception as e:
            logger.error(f"Error MIDI: {e}")
            return self.get_default_melody()

    def get_note_name(self, midi_number):
        """
        Donne le nom de la note (ex: 60 -> 'C4')
        """
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_number // 12) - 1
        note_index = midi_number % 12
        return f"{notes[note_index]}{octave}"

    def extract_notes_with_bpm(self, midi_path: str) -> tuple:
        """Extract notes AND BPM from MIDI file"""
        try:
            import mido
            midi = mido.MidiFile(midi_path)
            notes = []
            bpm = 120.0  # Default
            
            # Extract tempo (BPM)
            for track in midi.tracks:
                for msg in track:
                    if msg.type == 'set_tempo':
                        # tempo is in microseconds per beat
                        bpm = 60_000_000 / msg.tempo
                        logger.info(f"Extracted BPM: {bpm}")
                        break
            
            # Extract notes
            for msg in midi.tracks[len(midi.tracks) - 1]:  # Use last track for melody
                if msg.type == 'note_on' and msg.velocity > 0:
                    freq = 440.0 * (2 ** ((msg.note - 69) / 12))
                    print(msg)
                    print("Note:", self.get_note_name(msg.note), "Frequency:", freq)
                    notes.append(freq)

            self.last_bpm = bpm
            logger.info(f"{len(notes)} notes extracted, BPM: {bpm:.1f} from {midi_path}")
            return notes, bpm

        except Exception as e:
            logger.error(f"Error MIDI: {e}")
            return self.get_default_melody(), 120.0

    def get_bpm(self) -> float:
        """Get the last extracted BPM"""
        return self.last_bpm

    def get_default_melody(self) -> List[float]:
        """Default melody in C major"""
        return [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]


class ViralSoundEngine(IAudioGenerator):
    """
    Production-ready audio generator optimized for viral TikTok physics videos.

    Features:
    - 5-layer sound architecture (Sub, Body, Presence, Air, Tail)
    - Velocity-mapped dynamics (harder hit = louder/bassier)
    - Progressive build system (sound gets richer over time)
    - Three modes: Maximum Punch / ASMR Relaxant / MIDI Music
    - <1ms attack times for satisfying snap
    - 5kHz presence for ASMR engagement
    """

    # Mode mixing ratios (for synth modes)
    MODE_MIX = {
        'maximum_punch': {
            'sub': 1.0,
            'body': 0.9,
            'presence': 0.5,
            'air': 0.3,
            'tail': 0.25
        },
        'asmr_relaxant': {
            'sub': 0.2,
            'body': 0.6,
            'presence': 1.0,
            'air': 0.8,
            'tail': 0.6
        },
        'midi_music': {
            'sub': 0.6,
            'body': 1.0,
            'presence': 0.7,
            'air': 0.4,
            'tail': 0.4
        },
        # NOUVEAUX MODES
        'melodic': {
            'sub': 0.4,
            'body': 0.8,
            'presence': 0.9,
            'air': 0.6,
            'tail': 0.7
        },
        'physics_sync': {
            'sub': 0.8,
            'body': 1.0,
            'presence': 0.6,
            'air': 0.3,
            'tail': 0.2
        }
    }

    # Liste des modes pour sélection aléatoire
    RANDOM_MODES = ['maximum_punch', 'asmr_relaxant', 'midi_music', 'melodic', 'physics_sync']

    # Timbre presets - randomly selected per video for variety
    TIMBRE_PRESETS = {
        'crystal': {'sub': 0.3, 'body': 0.5, 'presence': 1.0, 'air': 0.9, 'tail': 0.5},
        'deep': {'sub': 1.0, 'body': 0.9, 'presence': 0.3, 'air': 0.2, 'tail': 0.4},
        'pop': {'sub': 0.5, 'body': 1.0, 'presence': 0.7, 'air': 0.4, 'tail': 0.2},
        'soft': {'sub': 0.4, 'body': 0.7, 'presence': 0.5, 'air': 0.6, 'tail': 0.7},
        'bright': {'sub': 0.2, 'body': 0.6, 'presence': 0.9, 'air': 1.0, 'tail': 0.3},
    }

    def __init__(self, sample_rate: int = 44100, mode: str = 'maximum_punch',
                 progressive_build: bool = True, music_folder: str = './music'):
        self.sample_rate = sample_rate
        self.output_path = "output/viral_audio.wav"
        self.duration = 30.0
        self.mode = mode
        self.music_folder = music_folder

        # Layer generators
        self.layers = {
            'sub': SubBassLayer(sample_rate),
            'body': BodyLayer(sample_rate),
            'presence': PresenceLayer(sample_rate),
            'air': AirLayer(sample_rate),
            'tail': TailLayer(sample_rate)
        }

        # Mapping and processing
        self.velocity_mapper = VelocityMapper()
        self.progressive_builder = ProgressiveBuilder(enabled=progressive_build)
        self.humanizer = Humanizer()

        # Effects
        self.compressor = Compressor(sample_rate)
        self.limiter = Limiter(sample_rate)

        # State
        self.events: List[AudioEvent] = []
        self.audio_data: Optional[np.ndarray] = None

        # MIDI mode state
        self.midi_notes: List[float] = []
        self.current_note_index = 0
        self.midi_extractor = SimpleMidiExtractor()
        self.extracted_bpm: float = 120.0  # Extracted from MIDI
        self.selected_midi_path: Optional[str] = None

        # Timbre state (randomly selected per video)
        self.current_timbre: Optional[str] = None

        # === SONS PERSONNALISÉS ===
        # Modes: "generated" (synthèse), "file" (fichier audio), "random" (aléatoire entre les deux), "viral" (sons memes)
        self.collision_sound_mode = "generated"  # Mode pour les rebonds
        self.passage_sound_mode = "generated"    # Mode pour les passages (default: generated)

        # Dossiers de sons (pour mode "file" ou "random")
        self.collision_sounds_folder = "./sounds/collision"
        self.passage_sounds_folder = "./sounds/passage"
        self.viral_sounds_folder = "./sounds/viral"  # Dossier sons viraux (miou, bruh, etc.)

        # Fichiers spécifiques (optionnel, prioritaire sur le dossier)
        self.collision_sound_file = None
        self.passage_sound_file = None

        # === OPTIONS SONS VIRAUX ===
        self.viral_sounds_enabled = False  # Activer/désactiver les sons viraux
        self.viral_sound_duration_min = 0.0  # Durée min en secondes (0 = pas de filtre)
        self.viral_sound_duration_max = 7.0  # Durée max en secondes (7s max)
        self.viral_fallback_to_generated = True  # Fallback sur synthèse si pas de son

        # Cache des sons chargés
        self._sound_cache: Dict[str, np.ndarray] = {}
        self._sound_durations: Dict[str, float] = {}  # Cache des durées

        logger.info(f"ViralSoundEngine initialized - Mode: {mode}, Progressive: {progressive_build}")

    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the engine"""
        try:
            if 'mode' in config:
                self.set_mode(config['mode'])
            if 'progressive_build' in config:
                self.progressive_builder.enabled = config['progressive_build']
            if 'sample_rate' in config:
                self.sample_rate = config['sample_rate']
            if 'music_folder' in config:
                self.music_folder = config['music_folder']

            # === Configuration sons personnalisés ===
            if 'collision_sound_mode' in config:
                self.collision_sound_mode = config['collision_sound_mode']
            if 'passage_sound_mode' in config:
                self.passage_sound_mode = config['passage_sound_mode']
            if 'collision_sounds_folder' in config:
                self.collision_sounds_folder = config['collision_sounds_folder']
            if 'passage_sounds_folder' in config:
                self.passage_sounds_folder = config['passage_sounds_folder']
            if 'collision_sound_file' in config:
                self.collision_sound_file = config['collision_sound_file']
            if 'passage_sound_file' in config:
                self.passage_sound_file = config['passage_sound_file']
            if 'viral_sounds_folder' in config:
                self.viral_sounds_folder = config['viral_sounds_folder']

            # Options sons viraux
            if 'viral_sounds_enabled' in config:
                self.viral_sounds_enabled = config['viral_sounds_enabled']
            if 'viral_sound_duration_min' in config:
                self.viral_sound_duration_min = max(0.0, min(7.0, config['viral_sound_duration_min']))
            if 'viral_sound_duration_max' in config:
                self.viral_sound_duration_max = max(0.0, min(7.0, config['viral_sound_duration_max']))
            if 'viral_fallback_to_generated' in config:
                self.viral_fallback_to_generated = config['viral_fallback_to_generated']

            return True
        except Exception as e:
            logger.error(f"Configuration error: {e}")
            return False

    def _load_audio_file(self, file_path: str) -> Optional[np.ndarray]:
        """Charge un fichier audio WAV et retourne les samples"""
        if file_path in self._sound_cache:
            return self._sound_cache[file_path]

        try:
            if not file_path.lower().endswith('.wav'):
                logger.warning(f"Unsupported audio format: {file_path}")
                return None

            # Utiliser le module wave standard (pas de dépendance externe)
            with wave.open(file_path, 'rb') as wav:
                rate = wav.getframerate()
                n_channels = wav.getnchannels()
                sample_width = wav.getsampwidth()
                n_frames = wav.getnframes()

                raw_data = wav.readframes(n_frames)

            # Convertir en numpy array
            if sample_width == 2:  # 16-bit
                data = np.frombuffer(raw_data, dtype=np.int16)
                data = data.astype(np.float32) / 32768.0
            elif sample_width == 4:  # 32-bit
                data = np.frombuffer(raw_data, dtype=np.int32)
                data = data.astype(np.float32) / 2147483648.0
            elif sample_width == 1:  # 8-bit
                data = np.frombuffer(raw_data, dtype=np.uint8)
                data = (data.astype(np.float32) - 128) / 128.0
            else:
                logger.warning(f"Unsupported sample width: {sample_width}")
                return None

            # Si stéréo, prendre le mono (moyenne des canaux)
            if n_channels > 1:
                data = data.reshape(-1, n_channels).mean(axis=1)

            # Resampler si nécessaire (interpolation linéaire simple)
            if rate != self.sample_rate:
                num_samples = int(len(data) * self.sample_rate / rate)
                indices = np.linspace(0, len(data) - 1, num_samples)
                data = np.interp(indices, np.arange(len(data)), data).astype(np.float32)

            self._sound_cache[file_path] = data
            logger.info(f"Loaded audio file: {file_path} ({len(data)} samples)")
            return data

        except Exception as e:
            logger.error(f"Error loading audio file {file_path}: {e}")
            return None

    def _get_random_sound_from_folder(self, folder: str) -> Optional[np.ndarray]:
        """Charge un fichier audio aléatoire depuis un dossier"""
        try:
            folder_path = Path(folder)
            if not folder_path.exists():
                logger.warning(f"Sound folder not found: {folder}")
                return None

            sound_files = list(folder_path.glob('*.wav')) + list(folder_path.glob('*.WAV'))
            if not sound_files:
                logger.warning(f"No sound files in {folder}")
                return None

            selected = random.choice(sound_files)
            return self._load_audio_file(str(selected))

        except Exception as e:
            logger.error(f"Error getting random sound: {e}")
            return None

    def _get_sound_duration(self, file_path: str) -> float:
        """Retourne la durée d'un fichier audio en secondes"""
        if file_path in self._sound_durations:
            return self._sound_durations[file_path]

        try:
            with wave.open(file_path, 'rb') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                duration = frames / float(rate)
                self._sound_durations[file_path] = duration
                return duration
        except Exception:
            return 0.0

    def _get_random_viral_sound(self) -> Optional[np.ndarray]:
        """Charge un son viral aléatoire depuis sounds/viral/ (tous sous-dossiers)
        Filtre par durée min/max si configuré"""
        try:
            folder_path = Path(self.viral_sounds_folder)
            if not folder_path.exists():
                logger.warning(f"Viral sounds folder not found: {self.viral_sounds_folder}")
                return None

            # Cherche dans tous les sous-dossiers (animals, bass, memes)
            sound_files = []
            for subdir in ['animals', 'bass', 'memes']:
                subdir_path = folder_path / subdir
                if subdir_path.exists():
                    sound_files.extend(list(subdir_path.glob('*.wav')))

            # Cherche aussi à la racine
            sound_files.extend(list(folder_path.glob('*.wav')))

            if not sound_files:
                logger.warning(f"No viral sounds found in {self.viral_sounds_folder}")
                return None

            # Filtrer par durée si min/max configurés
            if self.viral_sound_duration_min > 0 or self.viral_sound_duration_max < 7.0:
                filtered_files = []
                for f in sound_files:
                    duration = self._get_sound_duration(str(f))
                    if self.viral_sound_duration_min <= duration <= self.viral_sound_duration_max:
                        filtered_files.append(f)

                if filtered_files:
                    sound_files = filtered_files
                    logger.debug(f"Filtered to {len(sound_files)} sounds by duration ({self.viral_sound_duration_min}-{self.viral_sound_duration_max}s)")
                else:
                    logger.warning(f"No sounds match duration filter {self.viral_sound_duration_min}-{self.viral_sound_duration_max}s")
                    return None

            selected = random.choice(sound_files)
            logger.info(f"Selected viral sound: {selected.name}")
            return self._load_audio_file(str(selected))

        except Exception as e:
            logger.error(f"Error getting viral sound: {e}")
            return None

    def _apply_sound_to_buffer(self, sound: np.ndarray, start_time: float, volume: float = 1.0, pitch_shift: float = 1.0):
        """Applique un son au buffer audio principal"""
        if sound is None or len(sound) == 0:
            return

        # Pitch shift simple (resample avec interpolation linéaire)
        if pitch_shift != 1.0:
            new_length = int(len(sound) / pitch_shift)
            if new_length > 0:
                # Interpolation linéaire pour le pitch shift
                old_indices = np.arange(len(sound))
                new_indices = np.linspace(0, len(sound) - 1, new_length)
                sound = np.interp(new_indices, old_indices, sound).astype(np.float32)

        start_sample = int(start_time * self.sample_rate)
        end_sample = min(start_sample + len(sound), len(self.audio_data))

        if start_sample < len(self.audio_data):
            length = end_sample - start_sample
            self.audio_data[start_sample:end_sample] += sound[:length] * volume

    def set_mode(self, mode: str):
        """Switch between audio modes (supports 'random' for random selection)"""
        # Mode random: sélectionne un mode aléatoirement
        if mode == 'random':
            mode = random.choice(self.RANDOM_MODES)
            logger.info(f"Mode random a sélectionné: {mode}")

        if mode not in self.MODE_MIX:
            logger.warning(f"Unknown mode '{mode}', using 'maximum_punch'")
            mode = 'maximum_punch'
        self.mode = mode

        # Load MIDI if needed (midi_music or melodic modes)
        if mode in ['midi_music', 'melodic']:
            self._load_random_midi()

        logger.info(f"Mode set to: {mode}")

    def _load_random_midi(self):
        """Load a random MIDI file from the music folder and extract BPM"""
        try:
            music_path = Path(self.music_folder)
            if not music_path.exists():
                logger.warning(f"Music folder not found: {self.music_folder}")
                self.midi_notes = self.midi_extractor.get_default_melody()
                self.extracted_bpm = 120.0
                return

            midi_files = list(music_path.glob('*.mid')) + list(music_path.glob('*.midi'))

            if not midi_files:
                logger.warning(f"No MIDI files in {self.music_folder}")
                self.midi_notes = self.midi_extractor.get_default_melody()
                self.extracted_bpm = 120.0
                return

            # Select random MIDI file
            selected_midi = random.choice(midi_files)
            self.selected_midi_path = str(selected_midi)
            logger.info(f"Selected MIDI: {selected_midi.name}")

            # Extract notes AND BPM
            self.midi_notes, self.extracted_bpm = self.midi_extractor.extract_notes_with_bpm(str(selected_midi))
            self.current_note_index = 0

            logger.info(f"MIDI loaded - Notes: {len(self.midi_notes)}, BPM: {self.extracted_bpm:.1f}")

        except Exception as e:
            logger.error(f"Error loading MIDI: {e}")
            self.midi_notes = self.midi_extractor.get_default_melody()
            self.extracted_bpm = 120.0

    def get_bpm(self) -> float:
        """Get the extracted BPM from the loaded MIDI"""
        return self.extracted_bpm

    def set_output_path(self, path: str):
        """Set output file path"""
        self.output_path = path
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)

    def set_duration(self, duration: float):
        """Set audio duration"""
        self.duration = duration

    def apply_trend_data(self, trend_data: TrendData):
        """Apply trend data (for future features)"""
        pass

    def add_events(self, events: List[AudioEvent]):
        """Add audio events from video generator"""
        self.events.extend(events)
        logger.debug(f"Added {len(events)} events, total: {len(self.events)}")

    def generate(self) -> Optional[str]:
        """Generate the final audio track"""
        try:
            # Select random timbre for this video (variety between videos)
            self.current_timbre = random.choice(list(self.TIMBRE_PRESETS.keys()))
            logger.info(f"Generating viral audio - Mode: {self.mode}, Timbre: {self.current_timbre}, Events: {len(self.events)}")

            # Load MIDI if in midi_music mode and not already loaded
            if self.mode == 'midi_music' and not self.midi_notes:
                self._load_random_midi()

            # Initialize audio buffer
            total_samples = int(self.sample_rate * self.duration)
            self.audio_data = np.zeros(total_samples, dtype=np.float32)

            # Filter collision events
            collision_events = [e for e in self.events if e.event_type == 'collision']
            logger.info(f"Processing {len(collision_events)} collision events")

            # Reset note index for MIDI mode
            self.current_note_index = 0

            for event in self.events:
                if event.event_type == 'collision':
                    self._process_collision(event)
                elif event.event_type == 'passage':  # <--- NOUVEAU
                    self._process_passage(event)

            # Apply master effects
            self._apply_master_effects()

            # Normalize and save
            self._normalize_and_save()

            logger.info(f"Viral audio generated: {self.output_path}")
            return self.output_path

        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _process_collision(self, event: AudioEvent):
        """Process a single collision event - routes to appropriate mode handler"""
        # === SONS PERSONNALISÉS ===
        # Si mode "file" ou "random", on utilise un fichier audio
        if self.collision_sound_mode in ['file', 'random']:
            if self._process_collision_file(event):
                return  # Succès, on ne génère pas de son synthétisé

        # Route vers le handler approprié selon le mode
        if self.mode == 'physics_sync':
            self._process_collision_physics_sync(event)
            return
        if self.mode == 'melodic':
            self._process_collision_melodic(event)
            return

        # Mode standard (maximum_punch, asmr_relaxant, midi_music)
        self._process_collision_standard(event)

    def _process_collision_file(self, event: AudioEvent) -> bool:
        """
        Traite une collision avec un fichier audio.
        Retourne True si succès, False sinon (fallback sur synthèse).
        """
        velocity = event.params.get('velocity_magnitude', 800.0)
        velocity_normalized = min(1.0, velocity / 2000.0)

        # Récupérer le son
        sound = None
        if self.collision_sound_file:
            # Fichier spécifique configuré
            sound = self._load_audio_file(self.collision_sound_file)
        elif self.collision_sounds_folder:
            # Son aléatoire depuis le dossier
            sound = self._get_random_sound_from_folder(self.collision_sounds_folder)

        if sound is None:
            return False  # Pas de son, fallback sur synthèse

        # Calculer volume et pitch basés sur la vélocité
        volume = 0.5 + (velocity_normalized * 0.5)  # 0.5 - 1.0
        pitch_shift = 0.8 + (velocity_normalized * 0.4)  # 0.8 - 1.2 (plus rapide = plus aigu)

        # Appliquer le son
        self._apply_sound_to_buffer(sound, event.time, volume, pitch_shift)
        return True

    def _process_passage_file(self, event: AudioEvent) -> bool:
        """
        Traite un passage avec un fichier audio.
        Retourne True si succès, False sinon (fallback sur synthèse).
        """
        layer_index = event.params.get('layer_index', 0)
        total_layers = event.params.get('total_layers', 10)

        # Récupérer le son
        sound = None
        if self.passage_sound_file:
            # Fichier spécifique configuré
            sound = self._load_audio_file(self.passage_sound_file)
        elif self.passage_sounds_folder:
            # Son aléatoire depuis le dossier
            sound = self._get_random_sound_from_folder(self.passage_sounds_folder)

        if sound is None:
            return False  # Pas de son, fallback sur synthèse

        # Progression : plus on avance dans les couches, plus le pitch monte
        progress = layer_index / max(total_layers, 1)
        pitch_shift = 0.7 + (progress * 0.6)  # 0.7 - 1.3

        # Volume légèrement plus fort pour les passages importants
        volume = 0.6 + (progress * 0.2)

        # Appliquer le son
        self._apply_sound_to_buffer(sound, event.time, volume, pitch_shift)
        return True

    def _process_collision_standard(self, event: AudioEvent):
        """Process collision with standard modes (punch, asmr, midi)"""
        # Get velocity and bounce data
        velocity = event.params.get('velocity_magnitude', 800.0)
        bounce_count = event.params.get('bounce_count', 1)
        ball_size = event.params.get('ball_size', 30.0)

        # Map velocity to audio parameters
        audio_params = self.velocity_mapper.map(velocity)

        # Apply humanization (slight randomness)
        audio_params = self.humanizer.humanize(audio_params)

        # Update progressive builder
        self.progressive_builder.update(bounce_count)

        # Get active layers based on progressive build
        active_layers = self.progressive_builder.get_active_layers()
        harmonic_richness = self.progressive_builder.get_harmonic_richness()

        # Calculate base frequency based on mode
        if self.mode == 'midi_music' and self.midi_notes:
            # MIDI mode: use next note from the melody
            base_freq = self.midi_notes[self.current_note_index % len(self.midi_notes)]
            self.current_note_index += 1
        else:
            # Synth mode: bigger ball = lower pitch
            base_freq = 200.0 * (30.0 / max(ball_size, 10.0))
            base_freq = max(80, min(500, base_freq))

        # Sound duration based on velocity
        sound_duration = 0.15 + (audio_params['intensity'] * 0.15)
        samples = int(self.sample_rate * sound_duration)

        # Generate each active layer
        layer_signals = {}
        for layer_name in active_layers:
            if layer_name in self.layers:
                layer = self.layers[layer_name]
                signal = layer.generate(
                    frequency=base_freq,
                    duration=sound_duration,
                    intensity=audio_params['intensity'],
                    richness=harmonic_richness
                )

                # Apply progressive volume modifier
                volume_mod = self.progressive_builder.get_layer_volume(layer_name)
                layer_signals[layer_name] = signal * volume_mod

        # Mix layers according to mode
        mixed = self._mix_layers(layer_signals)

        # Apply to main buffer at event time
        start_sample = int(event.time * self.sample_rate)
        end_sample = min(start_sample + len(mixed), len(self.audio_data))

        if start_sample < len(self.audio_data) and len(mixed) > 0:
            length = end_sample - start_sample
            # Apply master volume from velocity
            mixed = mixed[:length] * audio_params['volume']
            self.audio_data[start_sample:end_sample] += mixed

    def _process_collision_physics_sync(self, event: AudioEvent):
        """
        Mode physics_sync: Son qui varie selon la vitesse et force de collision.
        Plus rapide = plus aigu, plus fort = plus de basse
        """
        velocity = event.params.get('velocity_magnitude', 800.0)
        bounce_count = event.params.get('bounce_count', 1)
        ball_size = event.params.get('ball_size', 30.0)

        # Mapper la vitesse vers la fréquence (plus rapide = plus aigu)
        # Vitesse 0-2000 -> Fréquence 80-800 Hz
        velocity_normalized = min(1.0, velocity / 2000.0)
        base_freq = 80 + (velocity_normalized * 720)  # 80 Hz - 800 Hz

        # Mapper la taille vers le mixage sub/body (plus gros = plus de basse)
        size_normalized = min(1.0, ball_size / 100.0)

        # Durée basée sur la vitesse (plus rapide = plus court)
        sound_duration = 0.3 - (velocity_normalized * 0.2)  # 0.1s - 0.3s
        sound_duration = max(0.05, sound_duration)

        # Intensité basée sur la vitesse
        intensity = 0.5 + (velocity_normalized * 0.5)

        # Générer les couches avec mixage dynamique
        # Sub bass plus fort pour grosses balles
        sub_signal = self.layers['sub'].generate(
            base_freq * 0.5, sound_duration,
            intensity=0.5 + (size_normalized * 0.5),
            richness=0.3
        )

        # Body avec fréquence basée sur vitesse
        body_signal = self.layers['body'].generate(
            base_freq, sound_duration,
            intensity=0.7 + (velocity_normalized * 0.3),
            richness=0.5
        )

        # Presence plus forte pour collisions rapides
        presence_signal = self.layers['presence'].generate(
            base_freq * 2, sound_duration * 0.5,
            intensity=velocity_normalized,
            richness=0.4
        )

        # Ajuster les longueurs
        max_len = max(len(sub_signal), len(body_signal), len(presence_signal))
        sub_signal = np.pad(sub_signal, (0, max(0, max_len - len(sub_signal))))
        body_signal = np.pad(body_signal, (0, max(0, max_len - len(body_signal))))
        presence_signal = np.pad(presence_signal, (0, max(0, max_len - len(presence_signal))))

        # Mixage dynamique basé sur la physique
        mixed = (
            sub_signal[:max_len] * (0.3 + size_normalized * 0.4) +
            body_signal[:max_len] * 0.8 +
            presence_signal[:max_len] * velocity_normalized * 0.5
        )

        # Appliquer au buffer
        start_sample = int(event.time * self.sample_rate)
        end_sample = min(start_sample + len(mixed), len(self.audio_data))

        if start_sample < len(self.audio_data):
            length = end_sample - start_sample
            volume = 0.5 + (velocity_normalized * 0.3)
            self.audio_data[start_sample:end_sample] += mixed[:length] * volume

    def _process_collision_melodic(self, event: AudioEvent):
        """
        Mode melodic: Utilise les notes MIDI pour créer des mélodies
        harmoniques basées sur les collisions.
        """
        bounce_count = event.params.get('bounce_count', 1)
        velocity = event.params.get('velocity_magnitude', 800.0)

        if not self.midi_notes:
            self._load_random_midi()

        # Sélectionner une note basée sur le bounce count (progression mélodique)
        note_idx = bounce_count % len(self.midi_notes) if self.midi_notes else 0
        base_freq = self.midi_notes[note_idx] if self.midi_notes else 440.0

        # Variation basée sur la vitesse
        velocity_normalized = min(1.0, velocity / 2000.0)

        sound_duration = 0.25 + (velocity_normalized * 0.15)

        # Générer le son principal
        body = self.layers['body'].generate(base_freq, sound_duration, intensity=0.8, richness=0.6)
        presence = self.layers['presence'].generate(base_freq * 2, sound_duration * 0.7, intensity=0.5, richness=0.4)
        air = self.layers['air'].generate(base_freq * 1.5, sound_duration, intensity=0.3, richness=0.3)
        tail = self.layers['tail'].generate(base_freq, sound_duration * 1.5, intensity=0.4, richness=0.5)

        # Ajuster les longueurs
        max_len = max(len(body), len(presence), len(air), len(tail))
        body = np.pad(body, (0, max(0, max_len - len(body))))
        presence = np.pad(presence, (0, max(0, max_len - len(presence))))
        air = np.pad(air, (0, max(0, max_len - len(air))))
        tail = np.pad(tail, (0, max(0, max_len - len(tail))))

        # Mixage mélodique
        mixed = body[:max_len] * 0.6 + presence[:max_len] * 0.3 + air[:max_len] * 0.2 + tail[:max_len] * 0.3

        # Ajouter une harmonique (quinte) si haute vélocité
        if velocity_normalized > 0.6:
            fifth_freq = base_freq * 1.5
            harmonic = self.layers['body'].generate(fifth_freq, sound_duration * 0.8, intensity=0.3, richness=0.4)
            harmonic = np.pad(harmonic, (0, max(0, max_len - len(harmonic))))
            mixed += harmonic[:max_len] * 0.2

        # Appliquer au buffer
        start_sample = int(event.time * self.sample_rate)
        end_sample = min(start_sample + len(mixed), len(self.audio_data))

        if start_sample < len(self.audio_data):
            length = end_sample - start_sample
            self.audio_data[start_sample:end_sample] += mixed[:length] * 0.6

    def _process_passage(self, event: AudioEvent):
        """Gère le son 'magique' du passage d'un niveau"""

        layer_index = event.params.get('layer_index', 0)
        total_layers = event.params.get('total_layers', 10)

        # === SONS VIRAUX (prioritaire si activé) ===
        if self.viral_sounds_enabled:
            sound = self._get_random_viral_sound()
            if sound is not None:
                # Progression : pitch varie selon la couche
                progress = layer_index / max(total_layers, 1)
                pitch_shift = 0.8 + (progress * 0.4)  # 0.8 - 1.2
                volume = 0.7 + (progress * 0.2)  # 0.7 - 0.9

                self._apply_sound_to_buffer(sound, event.time, volume, pitch_shift)
                return  # Succès avec son viral

            # Pas de son viral trouvé
            if not self.viral_fallback_to_generated:
                return  # Pas de fallback, on sort

            # Fallback vers génération synthétique
            logger.debug("Viral sound not found, falling back to generated")

        # === SONS PERSONNALISÉS (mode file/random) ===
        if self.passage_sound_mode in ['file', 'random']:
            if self._process_passage_file(event):
                return  # Succès, on ne génère pas de son synthétisé

        # === GÉNÉRATION SYNTHÉTIQUE (fallback) ===
        # 1. Paramètres
        # Plus le cercle est petit (index élevé), plus le son est aigu
        
        # 2. Choix de la fréquence (Harmonie)
        # On veut un accord ou une note plus haute que la basse actuelle
        if self.mode == 'midi_music' and self.midi_notes:
            # En mode MIDI, on joue un accord (3 notes de la gamme)
            root_idx = self.current_note_index % len(self.midi_notes)
            freqs = [
                self.midi_notes[root_idx], # Tonique
                self.midi_notes[(root_idx + 2) % len(self.midi_notes)], # Tierce
                self.midi_notes[(root_idx + 4) % len(self.midi_notes)]  # Quinte
            ]
        else:
            # En mode Synthé, on monte dans les aigus progressivement
            base_freq = 440.0 * (1.0 + (layer_index / total_layers))
            freqs = [base_freq, base_freq * 1.5] # Quinte pure

        # 3. Génération du son "Release"
        # On utilise principalement AIR et TAIL pour l'effet "Magique"
        sound_duration = 1.5 # Beaucoup plus long qu'un rebond
        
        passage_mix = np.zeros(int(self.sample_rate * sound_duration))
        
        for f in freqs:
            # AIR : Le souffle (le "Whoosh")
            air = self.layers['air'].generate(f, sound_duration, intensity=0.6, richness=0.8)
            
            # TAIL : La résonance (le "Bing")
            tail = self.layers['tail'].generate(f, sound_duration, intensity=0.5, richness=1.0)
            
            # PRESENCE : Un tout petit "click" cristallin au début
            presence = self.layers['presence'].generate(f * 2, 0.1, intensity=0.3, richness=0.5)
            # On pad la presence pour qu'elle fasse la même taille
            presence = np.pad(presence, (0, len(passage_mix) - len(presence)))
            
            # Mixage des couches pour cette fréquence
            # On applique une enveloppe d'attaque plus douce (fade-in)
            note_signal = (air * 0.5) + (tail * 0.8) + (presence * 0.2)
            
            # Fade In/Out manuel pour adoucir
            fade_len = int(0.1 * self.sample_rate) # 100ms fade in
            fade_in = np.linspace(0, 1, fade_len)
            note_signal[:fade_len] *= fade_in
            
            # Ajouter au mix global du passage (attention aux longueurs)
            l = min(len(passage_mix), len(note_signal))
            passage_mix[:l] += note_signal[:l]

        # 4. Ajout au buffer principal
        start_sample = int(event.time * self.sample_rate)
        end_sample = min(start_sample + len(passage_mix), len(self.audio_data))
        
        if start_sample < len(self.audio_data):
            l = end_sample - start_sample
            # On ajoute le son de passage par dessus le reste (mixage additif)
            self.audio_data[start_sample:end_sample] += passage_mix[:l] * 0.7 # Volume à 70% pour pas saturer
            
    def _mix_layers(self, layer_signals: Dict[str, np.ndarray]) -> np.ndarray:
        """Mix layers according to current timbre (randomly selected per video)"""
        if not layer_signals:
            return np.zeros(100)

        # Get max length
        max_len = max(len(s) for s in layer_signals.values())
        mixed = np.zeros(max_len, dtype=np.float32)

        # Use timbre preset for variety between videos
        if self.current_timbre and self.current_timbre in self.TIMBRE_PRESETS:
            mix_ratios = self.TIMBRE_PRESETS[self.current_timbre]
        else:
            mix_ratios = self.MODE_MIX.get(self.mode, self.MODE_MIX['maximum_punch'])

        for layer_name, signal in layer_signals.items():
            ratio = mix_ratios.get(layer_name, 0.5)
            # Pad signal if needed
            if len(signal) < max_len:
                signal = np.pad(signal, (0, max_len - len(signal)))
            mixed += signal * ratio

        return mixed

    def _apply_master_effects(self):
        """Apply master effects chain"""
        if self.audio_data is None or np.max(np.abs(self.audio_data)) == 0:
            return

        # Compression for punch
        self.audio_data = self.compressor.process(self.audio_data)

        # Limiting to prevent clipping
        self.audio_data = self.limiter.process(self.audio_data)

    def _normalize_and_save(self):
        """Normalize and save to WAV"""
        if self.audio_data is None:
            return

        # Normalize to -1dB
        max_val = np.max(np.abs(self.audio_data))
        if max_val > 0:
            target = 0.9  # -1dB headroom
            self.audio_data = self.audio_data * (target / max_val)

        # Fade in/out to avoid clicks
        fade_samples = int(0.01 * self.sample_rate)
        if len(self.audio_data) > fade_samples * 2:
            fade_in = np.linspace(0, 1, fade_samples)
            fade_out = np.linspace(1, 0, fade_samples)
            self.audio_data[:fade_samples] *= fade_in
            self.audio_data[-fade_samples:] *= fade_out

        # Convert to 16-bit PCM
        audio_int16 = (self.audio_data * 32767).astype(np.int16)

        # Save WAV
        with wave.open(self.output_path, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(audio_int16.tobytes())

        logger.info(f"Audio saved: {self.output_path}")

if __name__ == "__main__":
    
    engine = ViralSoundEngine(mode='midi_music', music_folder="./music")
    engine.set_output_path("test_viral_audio.wav")
    for i in range(50):
        engine.add_events([
            AudioEvent(time=i * 0.5, event_type='collision', params={'velocity_magnitude': 800 + i * 100, 'bounce_count': i + 1, 'ball_size': 20 + i * 5}),
        ])
        print(f"Added event at {i * 0.5}s")
    path = engine.generate()
    print(f"Generated viral audio at: {path}")