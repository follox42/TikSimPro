# src/audio_generators/simple_midi_audio_generator.py
"""
Simple audi generator for midi files.
"""

import numpy as np
import wave
import logging
import random
from typing import Dict, List, Any, Optional
import os

from src.audio_generators.base_audio_generator import IAudioGenerator
from src.core.data_pipeline import TrendData, AudioEvent

logger = logging.getLogger("TikSimPro")

class SimpleMidiExtractor:
    """Extractor for midi files"""
    
    def extract_notes(self, midi_path: str) -> List[float]:
        """Extract every notes in a midi file with mido"""
        try:
            import mido
            midi = mido.MidiFile(midi_path)
            notes = []
            
            for track in midi.tracks:
                for msg in track:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Convert midi note in frequence
                        freq = 440.0 * (2 ** ((msg.note - 69) / 12))
                        notes.append(freq)
            
            logger.info(f"{len(notes)} notes extracted from {midi_path}")
            return notes
            
        except Exception as e:
            logger.error(f"Error MIDI: {e}")
            return self.get_default_melody()
    
    def get_default_melody(self) -> List[float]:
        """Default melody in C major"""
        # C major: C D E F G A B C
        return [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]

class SimpleSoundGenerator:
    """Simple sound generator"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
    
    def _create_smooth_envelope(self, samples: int, 
                             attack_ms: float = 5.0,
                             decay_ms: float = 50.0,
                             sustain_level: float = 0.7,
                             release_ms: float = 100.0) -> np.ndarray:
        """
        🎯 UNIVERSAL SMOOTH ENVELOPE - Prevents ALL audio clicks
        
        Args:
            samples: Total number of samples in the sound
            attack_ms: Attack time in milliseconds (fade-in)
            decay_ms: Decay time in milliseconds (drop after peak)
            sustain_level: Sustain amplitude level (0 to 1)
            release_ms: Release time in milliseconds (fade-out)
        """
        
        envelope = np.ones(samples)

        # Convert envelope timing from milliseconds to samples
        attack_samples = max(1, int(attack_ms * self.sample_rate / 1000))
        decay_samples = max(1, int(decay_ms * self.sample_rate / 1000))
        release_samples = max(1, int(release_ms * self.sample_rate / 1000))
        
        # If envelope exceeds total duration, scale everything down proportionally
        total_env_samples = attack_samples + decay_samples + release_samples
        if total_env_samples >= samples:
            ratio = samples / total_env_samples * 0.9  # safety margin
            attack_samples = max(1, int(attack_samples * ratio))
            decay_samples = max(1, int(decay_samples * ratio))
            release_samples = max(1, int(release_samples * ratio))

        sustain_samples = samples - attack_samples - decay_samples - release_samples
        current_pos = 0

        # Attack phase: 0 → 1 using smooth sine-based curve
        if attack_samples > 0:
            attack_curve = np.sin(np.linspace(0, np.pi / 2, attack_samples)) ** 2
            envelope[current_pos:current_pos + attack_samples] = attack_curve
            current_pos += attack_samples

        # Decay phase: 1 → sustain_level (linear)
        if decay_samples > 0:
            decay_curve = np.linspace(1, sustain_level, decay_samples)
            envelope[current_pos:current_pos + decay_samples] = decay_curve
            current_pos += decay_samples

        # Sustain phase: constant amplitude
        if sustain_samples > 0:
            envelope[current_pos:current_pos + sustain_samples] = sustain_level
            current_pos += sustain_samples

        # Release phase: sustain_level → 0 using smooth cosine-based curve
        if release_samples > 0:
            release_curve = np.cos(np.linspace(0, np.pi / 2, release_samples)) ** 2
            envelope[current_pos:current_pos + release_samples] = release_curve * sustain_level

        return envelope

    def piano_note(self, frequency: float, duration: float = 0.5, volume: float = 0.7) -> np.ndarray:
        """Pino sound"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        harmonic_generator = lambda level: np.sin(2 * np.pi * frequency * t * level) * 1 / 2**(level-1)
        
        # Piano with harmonics
        note = (harmonic_generator(1) +
                harmonic_generator(2) +
                harmonic_generator(3))
        
        # Piano envelope (fast attack, quick decay)
        envelope = self._create_smooth_envelope(
            samples,
            attack_ms=2,      # Fast attack
            decay_ms=80,      # Realistic piano decay
            sustain_level=0.6, # 60% volume
            release_ms=150    # Natural release piano
        )

        return note * envelope * volume
    
    def bell_note(self, frequency: float, duration: float = 0.8, volume: float = 0.6) -> np.ndarray:
        """Bell sound"""
        
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Bell sound with inharmonic partials
        note = (np.sin(2 * np.pi * frequency * t) +
                0.6 * np.sin(2 * np.pi * frequency * 2.4 * t) +
                0.3 * np.sin(2 * np.pi * frequency * 3.8 * t))
        
        # Bell-shaped amplitude envelope (slow decay)
        envelope = self._create_smooth_envelope(
            samples,
            attack_ms=1,       # Instant attack
            decay_ms=200,      # Slow decay
            sustain_level=0.4, # Sustain low
            release_ms=400     # Super slow release for bell
        )
        
        return note * envelope * volume
    
    def soft_note(self, frequency: float, duration: float = 0.4, volume: float = 0.5) -> np.ndarray:
        """Soft sound"""
        
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Soft sine wave with slight modulation
        note = np.sin(2 * np.pi * frequency * t)
        vibrato = 1 + 0.02 * np.sin(2 * np.pi * 4 * t)  # Subtle vibrato
        
        # Smooth amplitude envelope with fade-in and fade-out
        envelope = self._create_smooth_envelope(
            samples,
            attack_ms=50,      # Soft attack
            decay_ms=20,       # Little decay
            sustain_level=0.8, # High sustain for smooth sound
            release_ms=80      # Normal release
        )
        
        return note * vibrato * envelope * volume
    
    def percussion_hit(self, frequency: float = 200, duration: float = 0.2, volume: float = 0.8) -> np.ndarray:
        """Percussion sound"""
        
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Percussive tone with added noise
        hit = (np.sin(2 * np.pi * frequency * t) +
            0.5 * np.random.normal(0, 0.2, samples))
        
        # Fast-decaying amplitude envelope (sharp attack)
        envelope = self._create_smooth_envelope(
            samples,
            attack_ms=1,       # Super fast attack
            decay_ms=30,       # Fast decay
            sustain_level=0.3, # Low sustain
            release_ms=100     # Normal release
        )
        
        return hit * envelope * volume

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
        
        # Configuration
        self.sound_types = ["piano", "bell", "soft", "percussion"]  # Types de sons disponibles
        self.current_sound = "piano"
        self.volume = 0.7
        self.max_simultaneous_notes = 4  # Avoid saturation
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
    
    def set_output_path(self, path: str) -> None:
        self.output_path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
    
    def set_duration(self, duration: float) -> None:
        self.duration = duration
    
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
                if event.event_type in ["collision", "particle_bounce", "circle_activation", "countdown_beep"]:

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
        """Génère un son selon le type configuré"""
        
        # Adjust the volume based on the event type
        volume = self.volume
        duration = 1.0
        if event.params:
            volume *= event.params.get("intensity", 1.0)
            volume *= event.params.get("volume", 1.0)
            duration *= event.params.get("duration", 1.0)
      
        
        # Generate the sound
        if self.current_sound == "piano":
            return self.sound_gen.piano_note(frequency, duration, volume)
        elif self.current_sound == "bell":
            return self.sound_gen.bell_note(frequency, duration, volume)
        elif self.current_sound == "soft":
            return self.sound_gen.soft_note(frequency, duration, volume)
        else:
            return self.sound_gen.piano_note(frequency, duration, volume)
    
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
