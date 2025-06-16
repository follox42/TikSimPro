# src/audio_generators/trend_audio_generator.py
"""
Générateur audio simple pour TikSimPro
Génère des sons synthétisés basés sur les événements vidéo
"""

import os
import wave
import math
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

from src.audio_generators.base_audio_generator import IAudioGenerator
from src.core.data_pipeline import TrendData, AudioEvent

logger = logging.getLogger("TikSimPro")

class TrendAudioGenerator(IAudioGenerator):
    """
    Générateur audio simple qui crée des sons synthétisés
    Idéal pour les vidéos de simulation physique TikTok
    """
    
    def __init__(self, 
                 note_volume: float = 0.5,
                 explosion_volume: float = 0.3,
                 activation_volume: float = 0.4,
                 passage_volume: float = 0.2):
        """
        Initialise le générateur audio
        
        Args:
            note_volume: Volume des notes musicales (0-1)
            explosion_volume: Volume des effets d'explosion
            activation_volume: Volume des sons d'activation
            passage_volume: Volume des sons de passage
        """
        # Configuration audio
        self.sample_rate = 44100  # Hz
        self.bit_depth = 16
        self.channels = 1  # Mono
        
        # Paramètres de volume
        self.note_volume = note_volume
        self.explosion_volume = explosion_volume
        self.activation_volume = activation_volume
        self.passage_volume = passage_volume
        
        # État du générateur
        self.output_path = "output/audio.wav"
        self.duration = 30.0
        self.trend_data = None
        self.audio_events = []
        
        # Données audio générées
        self.audio_data = None
        
        logger.info(f"TrendAudioGenerator initialisé - {self.sample_rate}Hz, volumes: note={note_volume}, explosion={explosion_volume}")
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure le générateur avec des paramètres spécifiques
        
        Args:
            config: Dictionnaire de configuration
            
        Returns:
            True si la configuration a réussi
        """
        try:
            if "note_volume" in config:
                self.note_volume = max(0.0, min(1.0, config["note_volume"]))
            if "explosion_volume" in config:
                self.explosion_volume = max(0.0, min(1.0, config["explosion_volume"]))
            if "activation_volume" in config:
                self.activation_volume = max(0.0, min(1.0, config["activation_volume"]))
            if "passage_volume" in config:
                self.passage_volume = max(0.0, min(1.0, config["passage_volume"]))
            
            if "sample_rate" in config:
                self.sample_rate = config["sample_rate"]
            
            logger.info(f"Audio generator configuré avec volumes: note={self.note_volume}, explosion={self.explosion_volume}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur de configuration audio: {e}")
            return False
    
    def set_output_path(self, path: str) -> None:
        """Définit le chemin de sortie pour l'audio"""
        self.output_path = path
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(path), exist_ok=True)
    
    def set_duration(self, duration: float) -> None:
        """Définit la durée de l'audio"""
        self.duration = duration
        logger.debug(f"Durée audio définie: {duration}s")
    
    def apply_trend_data(self, trend_data: TrendData) -> None:
        """
        Applique les données de tendance au générateur
        
        Args:
            trend_data: Données de tendance à appliquer
        """
        self.trend_data = trend_data
        
        if trend_data and hasattr(trend_data, 'recommended_settings'):
            audio_settings = trend_data.recommended_settings.get('audio', {})
            if audio_settings:
                if 'note_volume' in audio_settings:
                    self.note_volume = audio_settings['note_volume']
                if 'explosion_volume' in audio_settings:
                    self.explosion_volume = audio_settings['explosion_volume']
                
                logger.info(f"Paramètres audio des tendances appliqués: {audio_settings}")
    
    def add_events(self, events: List[AudioEvent]) -> None:
        """
        Ajoute des événements audio à la timeline
        
        Args:
            events: Liste des événements audio
        """
        self.audio_events.extend(events)
        logger.debug(f"Ajouté {len(events)} événements audio")
    
    def generate(self) -> Optional[str]:
        """
        Génère la piste audio complète
        
        Returns:
            Chemin du fichier audio généré, ou None en cas d'échec
        """
        try:
            logger.info(f"Génération audio: {self.duration}s, {len(self.audio_events)} événements")
            
            # Créer le buffer audio principal
            total_samples = int(self.sample_rate * self.duration)
            self.audio_data = np.zeros(total_samples, dtype=np.float32)
            
            # Ajouter un drone de fond ambient
            self._add_ambient_background()
            
            # Traiter tous les événements audio
            for event in self.audio_events:
                self._process_audio_event(event)
            
            # Ajouter une mélodie de fond basée sur les tendances
            if self.trend_data:
                self._add_trend_melody()
            
            # Normaliser et convertir pour l'export
            self._normalize_audio()
            
            # Exporter le fichier audio
            if self._export_wav():
                logger.info(f"Audio généré avec succès: {self.output_path}")
                return self.output_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération audio: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _add_ambient_background(self):
        """Ajoute un fond sonore ambient subtil"""
        try:
            # Drone de fond très subtil (basse fréquence)
            duration_samples = len(self.audio_data)
            t = np.linspace(0, self.duration, duration_samples)
            
            # Combinaison de plusieurs fréquences basses
            freq1 = 60  # Note grave
            freq2 = 120  # Harmonique
            
            drone = (
                0.02 * np.sin(2 * np.pi * freq1 * t) +
                0.01 * np.sin(2 * np.pi * freq2 * t)
            )
            
            # Enveloppe pour fade in/out
            fade_samples = int(self.sample_rate * 2)  # 2 secondes de fade
            envelope = np.ones_like(drone)
            envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
            
            self.audio_data += drone * envelope
            
        except Exception as e:
            logger.warning(f"Erreur drone de fond: {e}")
    
    def _process_audio_event(self, event: AudioEvent):
        """
        Traite un événement audio individuel
        
        Args:
            event: Événement audio à traiter
        """
        try:
            start_sample = int(event.time * self.sample_rate)
            
            if event.event_type == "circle_pulse":
                self._add_pulse_sound(start_sample, event)
            elif event.event_type == "collision":
                self._add_collision_sound(start_sample, event)
            elif event.event_type == "activation":
                self._add_activation_sound(start_sample, event)
            elif event.event_type == "passage":
                self._add_passage_sound(start_sample, event)
            else:
                # Son générique
                self._add_generic_note(start_sample, event)
                
        except Exception as e:
            logger.warning(f"Erreur événement audio {event.event_type}: {e}")
    
    def _add_pulse_sound(self, start_sample: int, event: AudioEvent):
        """Ajoute un son de pulsation pour les cercles"""
        try:
            # Paramètres du son
            frequency = 440 + (event.params.get("intensity", 0.5) * 220)  # 440-660 Hz
            duration = 0.2  # 200ms
            volume = self.note_volume * event.params.get("intensity", 0.5)
            
            # Générer le son
            sound = self._generate_tone(frequency, duration, volume, wave_type="sine")
            
            # Ajouter à la timeline
            end_sample = min(start_sample + len(sound), len(self.audio_data))
            if start_sample < len(self.audio_data):
                length = end_sample - start_sample
                self.audio_data[start_sample:end_sample] += sound[:length]
                
        except Exception as e:
            logger.warning(f"Erreur pulse sound: {e}")
    
    def _add_collision_sound(self, start_sample: int, event: AudioEvent):
        """Ajoute un son de collision/impact"""
        try:
            # Son percussif avec harmoniques
            base_freq = 200
            duration = 0.15
            volume = self.explosion_volume
            
            # Combinaison de plusieurs fréquences
            sound1 = self._generate_tone(base_freq, duration, volume * 0.6, "triangle")
            sound2 = self._generate_tone(base_freq * 2, duration * 0.5, volume * 0.3, "square")
            sound3 = self._generate_noise(duration * 0.1, volume * 0.2)
            
            # Combiner les sons
            max_len = max(len(sound1), len(sound2), len(sound3))
            combined = np.zeros(max_len)
            combined[:len(sound1)] += sound1
            combined[:len(sound2)] += sound2
            combined[:len(sound3)] += sound3
            
            # Ajouter à la timeline
            end_sample = min(start_sample + len(combined), len(self.audio_data))
            if start_sample < len(self.audio_data):
                length = end_sample - start_sample
                self.audio_data[start_sample:end_sample] += combined[:length]
                
        except Exception as e:
            logger.warning(f"Erreur collision sound: {e}")
    
    def _add_activation_sound(self, start_sample: int, event: AudioEvent):
        """Ajoute un son d'activation"""
        try:
            # Son montant rapide
            start_freq = 220
            end_freq = 880
            duration = 0.3
            volume = self.activation_volume
            
            sound = self._generate_sweep(start_freq, end_freq, duration, volume)
            
            # Ajouter à la timeline
            end_sample = min(start_sample + len(sound), len(self.audio_data))
            if start_sample < len(self.audio_data):
                length = end_sample - start_sample
                self.audio_data[start_sample:end_sample] += sound[:length]
                
        except Exception as e:
            logger.warning(f"Erreur activation sound: {e}")
    
    def _add_passage_sound(self, start_sample: int, event: AudioEvent):
        """Ajoute un son de passage"""
        try:
            # Son whoosh subtil
            frequency = 150
            duration = 0.4
            volume = self.passage_volume
            
            # Moduler la fréquence
            sound = self._generate_modulated_tone(frequency, duration, volume, mod_freq=5)
            
            # Ajouter à la timeline
            end_sample = min(start_sample + len(sound), len(self.audio_data))
            if start_sample < len(self.audio_data):
                length = end_sample - start_sample
                self.audio_data[start_sample:end_sample] += sound[:length]
                
        except Exception as e:
            logger.warning(f"Erreur passage sound: {e}")
    
    def _add_generic_note(self, start_sample: int, event: AudioEvent):
        """Ajoute une note générique"""
        try:
            frequency = 440
            duration = 0.25
            volume = self.note_volume * 0.7
            
            sound = self._generate_tone(frequency, duration, volume)
            
            # Ajouter à la timeline
            end_sample = min(start_sample + len(sound), len(self.audio_data))
            if start_sample < len(self.audio_data):
                length = end_sample - start_sample
                self.audio_data[start_sample:end_sample] += sound[:length]
                
        except Exception as e:
            logger.warning(f"Erreur generic note: {e}")
    
    def _add_trend_melody(self):
        """Ajoute une mélodie basée sur les tendances"""
        try:
            if not self.trend_data or not hasattr(self.trend_data, 'color_trends'):
                return
            
            # Convertir les couleurs en fréquences
            colors = self.trend_data.get_recommended_colors()
            if not colors:
                return
            
            # Mapper les couleurs vers des notes
            notes = []
            for color_hex in colors[:8]:  # Première 8 couleurs
                # Convertir hex en valeur numérique
                try:
                    color_val = int(color_hex.lstrip('#'), 16)
                    # Mapper sur une gamme pentatonique (sons agréables)
                    scale = [261.63, 293.66, 329.63, 392.00, 440.00]  # C, D, E, G, A
                    note_idx = (color_val % len(scale))
                    notes.append(scale[note_idx])
                except:
                    continue
            
            if not notes:
                return
            
            # Jouer la mélodie en arrière-plan
            note_duration = 0.8
            pause_duration = 0.2
            volume = self.note_volume * 0.3  # Volume faible pour l'arrière-plan
            
            current_time = 2.0  # Commencer à 2 secondes
            
            for note_freq in notes:
                if current_time >= self.duration - 1:
                    break
                
                start_sample = int(current_time * self.sample_rate)
                sound = self._generate_tone(note_freq, note_duration, volume, "sine")
                
                # Appliquer une enveloppe douce
                envelope = self._create_envelope(len(sound), attack=0.1, decay=0.2, sustain=0.6, release=0.3)
                sound *= envelope
                
                # Ajouter à la timeline
                end_sample = min(start_sample + len(sound), len(self.audio_data))
                if start_sample < len(self.audio_data):
                    length = end_sample - start_sample
                    self.audio_data[start_sample:end_sample] += sound[:length]
                
                current_time += note_duration + pause_duration
            
            logger.debug(f"Mélodie de tendance ajoutée avec {len(notes)} notes")
            
        except Exception as e:
            logger.warning(f"Erreur mélodie de tendance: {e}")
    
    # === GÉNÉRATEURS DE SONS ===
    
    def _generate_tone(self, frequency: float, duration: float, volume: float, 
                      wave_type: str = "sine") -> np.ndarray:
        """Génère une tonalité pure"""
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples)
        
        if wave_type == "sine":
            wave = np.sin(2 * np.pi * frequency * t)
        elif wave_type == "square":
            wave = np.sign(np.sin(2 * np.pi * frequency * t))
        elif wave_type == "triangle":
            wave = 2 * np.arcsin(np.sin(2 * np.pi * frequency * t)) / np.pi
        elif wave_type == "sawtooth":
            wave = 2 * (t * frequency - np.floor(t * frequency + 0.5))
        else:
            wave = np.sin(2 * np.pi * frequency * t)
        
        return wave * volume
    
    def _generate_sweep(self, start_freq: float, end_freq: float, 
                       duration: float, volume: float) -> np.ndarray:
        """Génère un sweep de fréquence"""
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples)
        
        # Fréquence qui change linéairement
        freq_sweep = start_freq + (end_freq - start_freq) * t / duration
        
        # Intégrer pour obtenir la phase
        phase = 2 * np.pi * np.cumsum(freq_sweep) / self.sample_rate
        
        wave = np.sin(phase) * volume
        return wave
    
    def _generate_modulated_tone(self, frequency: float, duration: float, 
                                volume: float, mod_freq: float = 5) -> np.ndarray:
        """Génère une tonalité modulée"""
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples)
        
        # Modulation d'amplitude
        modulation = 1 + 0.3 * np.sin(2 * np.pi * mod_freq * t)
        carrier = np.sin(2 * np.pi * frequency * t)
        
        wave = carrier * modulation * volume
        return wave
    
    def _generate_noise(self, duration: float, volume: float) -> np.ndarray:
        """Génère du bruit blanc"""
        samples = int(duration * self.sample_rate)
        noise = np.random.uniform(-1, 1, samples) * volume
        return noise
    
    def _create_envelope(self, length: int, attack: float = 0.1, decay: float = 0.1, 
                        sustain: float = 0.7, release: float = 0.2) -> np.ndarray:
        """Crée une enveloppe ADSR"""
        envelope = np.ones(length)
        
        attack_samples = int(attack * length)
        decay_samples = int(decay * length)
        release_samples = int(release * length)
        
        # Attack
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Decay
        if decay_samples > 0:
            start = attack_samples
            end = start + decay_samples
            envelope[start:end] = np.linspace(1, sustain, decay_samples)
        
        # Release
        if release_samples > 0:
            envelope[-release_samples:] = np.linspace(sustain, 0, release_samples)
        
        return envelope
    
    def _normalize_audio(self):
        """Normalise l'audio pour éviter la saturation"""
        max_val = np.max(np.abs(self.audio_data))
        if max_val > 0:
            # Normaliser à 90% pour éviter la saturation
            self.audio_data = self.audio_data * (0.9 / max_val)
    
    def _export_wav(self) -> bool:
        """Exporte l'audio en format WAV"""
        try:
            # Convertir en entiers 16-bit
            audio_int = (self.audio_data * 32767).astype(np.int16)
            
            # Créer le fichier WAV
            with wave.open(self.output_path, 'w') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_int.tobytes())
            
            logger.info(f"Fichier WAV exporté: {self.output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur export WAV: {e}")
            return False


# === UTILITAIRES ===

def create_simple_audio_generator() -> TrendAudioGenerator:
    """Crée une instance simple du générateur audio"""
    return TrendAudioGenerator(
        note_volume=0.5,
        explosion_volume=0.3,
        activation_volume=0.4,
        passage_volume=0.2
    )