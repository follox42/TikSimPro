#!/usr/bin/env python3
"""
🎵 Custom Sound Generator
Générateur de sons utilisant les presets créés avec le Sound Designer
"""

import json
import os
import random
import numpy as np
import wave
from typing import Dict, List, Any, Optional
import logging

from .simple_midi_audio_generator import SimpleSoundGenerator, SimpleMidiExtractor
from .base_audio_generator import IAudioGenerator
from ..core.data_pipeline import TrendData, AudioEvent

logger = logging.getLogger(__name__)

class CustomSoundGenerator:
    """Générateur de sons utilisant les configurations personnalisées"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.sound_generator = SimpleSoundGenerator(sample_rate=sample_rate)
        self.custom_configs = []
        self.load_custom_sounds()
        
    def load_custom_sounds(self):
        """Charge les sons personnalisés depuis le fichier JSON"""
        config_file = "sound_presets/custom_sounds.json"
        
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    self.custom_configs = json.load(f)
                logger.info(f"✅ {len(self.custom_configs)} sons personnalisés chargés")
            except Exception as e:
                logger.error(f"❌ Erreur lors du chargement des sons personnalisés: {e}")
                self.custom_configs = []
        else:
            logger.warning("⚠️ Aucun fichier de sons personnalisés trouvé, utilisation des sons par défaut")
            self.custom_configs = self._get_default_configs()
            
    def _get_default_configs(self) -> List[Dict[str, Any]]:
        """Retourne des configurations par défaut si aucun preset n'est trouvé"""
        return [
            {
                "name": "Bounce Satisfaisant",
                "type": "satisfying_bounce",
                "frequency_range": [200, 600],
                "duration": 0.4,
                "volume": 0.6,
                "envelope": {"attack_ms": 3.0, "decay_ms": 40.0, "sustain_level": 0.8, "release_ms": 80.0}
            },
            {
                "name": "Pop ASMR",
                "type": "asmr_pop",
                "frequency_range": [300, 800],
                "duration": 0.3,
                "volume": 0.5,
                "envelope": {"attack_ms": 1.0, "decay_ms": 20.0, "sustain_level": 0.7, "release_ms": 60.0}
            },
            {
                "name": "Carillon Doux",
                "type": "soft_chime",
                "frequency_range": [400, 1200],
                "duration": 0.8,
                "volume": 0.4,
                "envelope": {"attack_ms": 5.0, "decay_ms": 80.0, "sustain_level": 0.6, "release_ms": 200.0}
            },
            {
                "name": "Goutte d'Eau",
                "type": "water_drop",
                "frequency_range": [250, 500],
                "duration": 0.6,
                "volume": 0.5,
                "envelope": {"attack_ms": 2.0, "decay_ms": 30.0, "sustain_level": 0.9, "release_ms": 100.0}
            },
            {
                "name": "Corde Pincée",
                "type": "gentle_pluck",
                "frequency_range": [150, 400],
                "duration": 0.7,
                "volume": 0.6,
                "envelope": {"attack_ms": 1.0, "decay_ms": 50.0, "sustain_level": 0.5, "release_ms": 150.0}
            },
            {
                "name": "Cristal Ting",
                "type": "crystal_ting",
                "frequency_range": [800, 2000],
                "duration": 0.5,
                "volume": 0.4,
                "envelope": {"attack_ms": 0.5, "decay_ms": 25.0, "sustain_level": 0.8, "release_ms": 120.0}
            }
        ]
        
    def get_random_config(self) -> Dict[str, Any]:
        """Retourne une configuration aléatoire"""
        if not self.custom_configs:
            self.load_custom_sounds()
            
        if self.custom_configs:
            return random.choice(self.custom_configs)
        else:
            return self._get_default_configs()[0]
            
    def get_config_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Retourne une configuration par nom"""
        for config in self.custom_configs:
            if config["name"] == name:
                return config
        return None
            
    def generate_sound_from_config(self, config: Dict[str, Any], frequency: Optional[float] = None) -> np.ndarray:
        """Génère un son à partir d'une configuration"""
        
        # Utilise une fréquence spécifique ou en génère une aléatoire dans la plage
        if frequency is None:
            freq_min, freq_max = config["frequency_range"]
            frequency = random.uniform(freq_min, freq_max)
        
        sound_type = config["type"]
        duration = config["duration"]
        volume = config["volume"]
        
        # Génère le son selon le type
        if sound_type == "satisfying_bounce":
            return self.sound_generator.satisfying_bounce(frequency, duration, volume)
        elif sound_type == "asmr_pop":
            return self.sound_generator.asmr_pop(frequency, duration, volume)
        elif sound_type == "soft_chime":
            return self.sound_generator.soft_chime(frequency, duration, volume)
        elif sound_type == "water_drop":
            return self.sound_generator.water_drop(frequency, duration, volume)
        elif sound_type == "gentle_pluck":
            return self.sound_generator.gentle_pluck(frequency, duration, volume)
        elif sound_type == "crystal_ting":
            return self.sound_generator.crystal_ting(frequency, duration, volume)
        else:
            # Fallback vers satisfying_bounce
            return self.sound_generator.satisfying_bounce(frequency, duration, volume)
            
    def generate_random_sound(self, frequency: Optional[float] = None) -> np.ndarray:
        """Génère un son aléatoire à partir des presets"""
        config = self.get_random_config()
        return self.generate_sound_from_config(config, frequency)
        
    def generate_sound_by_name(self, name: str, frequency: Optional[float] = None) -> Optional[np.ndarray]:
        """Génère un son en utilisant un preset spécifique par nom"""
        config = self.get_config_by_name(name)
        if config:
            return self.generate_sound_from_config(config, frequency)
        
        logger.warning(f"⚠️ Preset '{name}' non trouvé, utilisation d'un son aléatoire")
        return self.generate_random_sound(frequency)
        
    def list_available_sounds(self) -> List[str]:
        """Retourne la liste des noms de sons disponibles"""
        return [config["name"] for config in self.custom_configs]
        
    def get_sound_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Retourne les informations d'un son spécifique"""
        return self.get_config_by_name(name)

# Classe principale compatible avec l'interface IAudioGenerator
class CustomMidiAudioGenerator(IAudioGenerator):
    """Générateur audio personnalisé basé sur SimpleMidiAudioGenerator avec les presets du Sound Designer"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.output_path = "output/custom_audio.wav"
        self.duration = 30.0
        
        # Composants - similaire à SimpleMidiAudioGenerator
        self.midi_extractor = SimpleMidiExtractor()
        self.custom_sound_gen = CustomSoundGenerator(sample_rate)
        
        # État
        self.melody_notes = []
        self.events = []
        self.audio_data = None
        self.trend_data = None
        
        # Configuration avec les presets personnalisés
        self.available_presets = self.custom_sound_gen.list_available_sounds()
        self.current_preset = None
        self.volume = 0.5  # Volume plus doux pour les sons ASMR
        self.max_simultaneous_notes = 3  # Moins de superposition pour plus de clarté
        self.auto_volume_adjust = True    # Auto adjust volume
        
        logger.info(f"🎵 Custom MIDI Audio Generator initialisé avec {len(self.available_presets)} presets")
        
    def configure(self, config: Dict[str, Any]) -> bool:
        """Configuration du générateur personnalisé"""
        try:
            # Preset spécifique ou aléatoire
            preset_name = config.get("preset_name")
            if preset_name and preset_name in self.available_presets:
                self.current_preset = preset_name
            else:
                self.current_preset = random.choice(self.available_presets) if self.available_presets else None
            
            self.volume = config.get("volume", 0.6)
            self.max_simultaneous_notes = config.get("max_simultaneous_notes", 3)
            self.auto_volume_adjust = config.get("auto_volume_adjust", True)
            
            logger.info(f"Configuration: preset={self.current_preset}, volume={self.volume}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur de configuration: {e}")
            return False
    
    def set_output_path(self, path: str) -> None:
        """Définit le chemin de sortie pour l'audio"""
        self.output_path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
    
    def set_duration(self, duration: float) -> None:
        """Définit la durée de l'audio"""
        self.duration = duration
    
    def select_music(self, musics: list):
        """Sélection aléatoire de musique - identique à SimpleMidiAudioGenerator"""
        if not musics:
            return None
        index = random.randint(0, len(musics) - 1)
        return musics[index]

    def apply_trend_data(self, trend_data: TrendData) -> None:
        """Applique les données de tendance - identique à SimpleMidiAudioGenerator"""
        self.trend_data = trend_data
        
        midi_files = []
        # Recherche de fichiers MIDI
        if trend_data and trend_data.popular_music:
            for music in trend_data.popular_music:
                if 'file_path' in music:
                    file_path = music['file_path']
                    if file_path.endswith(('.mid', '.midi')):
                        midi_files.append(file_path)
        
        # Sélectionne la musique
        if midi_files:
            music_path = self.select_music(midi_files)
            if music_path:  # Vérification que music_path n'est pas None
                self.melody_notes = self.midi_extractor.extract_notes(music_path)
                logger.info(f"Mélodie chargée depuis {music_path}")
            else:
                # Fichier MIDI non trouvé, utilise la mélodie par défaut
                self.melody_notes = self.midi_extractor.get_default_melody()
                logger.warning("Mélodie par défaut utilisée - sélection musicale échouée")
        else:
            # Fichier MIDI non trouvé, utilise la mélodie par défaut
            self.melody_notes = self.midi_extractor.get_default_melody()
            logger.warning("Mélodie par défaut utilisée - aucun fichier MIDI trouvé")
    
    def add_events(self, events: List[AudioEvent]) -> None:
        """Ajoute des événements audio à la timeline"""
        self.events.extend(events)
        logger.debug(f"Ajout de {len(events)} événements")
    
    def generate(self) -> Optional[str]:
        """Génère la piste audio avec les sons personnalisés - structure identique à SimpleMidiAudioGenerator"""
        try:
            logger.info("🎵 Démarrage de la génération audio personnalisée...")
            
            # Buffer audio
            total_samples = int(self.sample_rate * self.duration)
            self.audio_data = np.zeros(total_samples, dtype=np.float32)
            
            # Sélectionne un preset s'il n'y en a pas déjà un
            if not self.current_preset and self.available_presets:
                self.current_preset = random.choice(self.available_presets)
            
            logger.info(f"Preset utilisé: {self.current_preset}")

            # Traite les événements
            self._process_events()
            
            # Normalise et sauvegarde
            self._normalize_and_save()
            
            logger.info(f"Audio généré: {self.output_path}")
            return self.output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            return None
    
    def _process_events(self):
        """Traite les événements et joue les notes - identique à SimpleMidiAudioGenerator"""
        if not self.melody_notes:
            logger.warning("Mélodie indisponible")
            return

        if self.audio_data is None or len(self.audio_data) == 0:
            logger.warning("Buffer audio indisponible")
            return

        note_index = 0

        for event in self.events:
            try:
                # Joue une note sur tous les événements intéressants
                if event.event_type in ["collision", "particle_bounce", "circle_activation", "countdown_beep"]:

                    # Passe à la note suivante
                    frequency = self.melody_notes[note_index % len(self.melody_notes)]
                    note_index += 1
                    
                    # Calcul intelligent du volume
                    start_sample = int(event.time * self.sample_rate)
                    
                    # Génère le son pour cette note
                    sound = self._generate_sound(frequency, event)
                    
                    # Gère les sons superposés
                    end_sample = min(start_sample + len(sound), len(self.audio_data))

                    if start_sample < len(self.audio_data):
                        length = end_sample - start_sample
                        
                        # Compte les notes actives simultanément
                        if self.auto_volume_adjust:
                            region_activity = np.mean(np.abs(self.audio_data[start_sample:end_sample]))
                            volume_reduction = 1.0 / (1.0 + region_activity * 2)  # Réduction progressive
                            sound = sound * volume_reduction
                        
                        # Superposition naturelle
                        self.audio_data[start_sample:end_sample] += sound[:length]

            except Exception as e:
                logger.warning(f"Erreur événement: {e}")

    def _generate_sound(self, frequency: float, event: AudioEvent) -> np.ndarray:
        """Génère un son personnalisé organique et ASMR"""
        
        # Volume de base adaptatif selon l'événement
        base_volume = self.volume
        
        if event.params:
            intensity = event.params.get("intensity", 1.0)
            base_volume *= intensity
            base_volume *= event.params.get("volume", 1.0)
        
        # Limitation du volume pour éviter la saturation
        base_volume = min(base_volume, 0.8)
        
        # Variation de fréquence organique pour plus de naturel
        frequency_variation = random.uniform(0.95, 1.05)
        organic_frequency = frequency * frequency_variation
        
        # Génère le son selon le preset sélectionné ou aléatoire
        if self.current_preset:
            config = self.custom_sound_gen.get_config_by_name(self.current_preset)
            if config:
                # Crée une copie pour ne pas modifier l'original
                config_copy = config.copy()
                config_copy["volume"] = base_volume
                sound = self.custom_sound_gen.generate_sound_from_config(config_copy, organic_frequency)
                return sound
        
        # Fallback : génère un son aléatoire avec fréquence organique
        return self.custom_sound_gen.generate_random_sound(organic_frequency)
    
    def _normalize_and_save(self):
        """Normalise et sauvegarde la sortie audio - identique à SimpleMidiAudioGenerator"""
        
        if self.audio_data is None:
            logger.error("Aucune donnée audio à normaliser")
            return
        
        # Étape 1: Normalisation
        max_val = np.max(np.abs(self.audio_data))

        if max_val > 1.0:
            # Compression douce pour éviter l'écrêtage
            compression_ratio = 0.8 / max_val
            self.audio_data = self.audio_data * compression_ratio
            logger.info(f"Compression appliquée: {compression_ratio:.3f}")
        else:
            # Amplification douce si le signal est trop faible
            if 0 < max_val < 0.3:
                amplification = 0.7 / max_val
                self.audio_data = self.audio_data * amplification
                logger.info(f"Amplification appliquée: {amplification:.3f}")
        
        # Étape 2: Applique un fade in/out doux (50 ms)
        fade_samples = int(0.05 * self.sample_rate)  # 50 ms de durée de fade
        if len(self.audio_data) > fade_samples * 2:
            # Fade-in doux (sinusoïdal)
            fade_in = np.sin(np.linspace(0, np.pi / 2, fade_samples)) ** 2
            self.audio_data[:fade_samples] *= fade_in

            # Fade-out doux (basé sur cosinus)
            fade_out = np.cos(np.linspace(0, np.pi / 2, fade_samples)) ** 2
            self.audio_data[-fade_samples:] *= fade_out

        # Étape 3: Exporte en fichier WAV
        self._save_to_wav()

    def _save_to_wav(self):
        """Sauvegarde le buffer audio dans un fichier WAV"""
        
        if self.audio_data is None:
            logger.error("Aucune donnée audio à sauvegarder")
            return
        
        try:
            # Convertit float32 en PCM 16-bit
            audio_int16 = (self.audio_data * 32767).astype(np.int16)

            with wave.open(self.output_path, 'w') as wav_file:
                wav_file.setnchannels(1)         # Mono
                wav_file.setsampwidth(2)         # échantillons 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            logger.info(f"Fichier WAV sauvegardé: {self.output_path}")
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde WAV: {e}")
            raise 