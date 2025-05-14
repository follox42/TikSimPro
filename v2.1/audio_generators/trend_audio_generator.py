# audio_generators/trend_audio_generator.py
"""
Générateur audio basé sur les tendances musicales
Génère une piste audio à partir de tendances et d'événements
"""

import os
import time
import logging
import numpy as np
import librosa
import soundfile as sf
from scipy.io import wavfile
from typing import Dict, List, Any, Optional, Tuple, Union
import random
import requests
from pathlib import Path

from core.interfaces import IAudioGenerator, TrendData, AudioEvent

logger = logging.getLogger("TikSimPro")

class TrendAudioGenerator(IAudioGenerator):
    """
    Générateur de pistes audio basées sur les tendances et les événements
    """
    
    def __init__(self, note_volume = 1.0, explosion_volume = 1.0, activation_volume = 1.0, passage_volume = 1.0):
        """Initialise le générateur audio"""
        # Paramètres par défaut
        self.sample_rate = 44100
        self.duration = 30.0
        self.output_path = "output/audio.wav"
        self.sounds_dir = "temp/sounds"
        
        # Volume
        self.note_volume = note_volume
        self.explosion_volume = explosion_volume
        self.activation_volume = activation_volume
        self.passage_volume = passage_volume

        # Créer le répertoire de sons
        os.makedirs(self.sounds_dir, exist_ok=True)
        
        # Événements audio
        self.events = []
        
        # Données de tendances
        self.trend_data = None
        
        # Sons de base
        self.notes = []  # (note_idx, octave, path)
        self.effect_sounds = {}  # {type_effect: {param: path}}
        self.background_music = None
        
        # Palette sonore
        self.current_melody = [0, 2, 4, 5, 4, 2, 0, 2]  # Do majeur par défaut
        self.beat_frequency = 1.0  # 1 beat par seconde (60 BPM)

        logger.info("TrendAudioGenerator initialisé")
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure le générateur avec des paramètres spécifiques
        
        Args:
            config: Paramètres de configuration
            
        Returns:
            True si la configuration a réussi, False sinon
        """
        try:
            # Appliquer les paramètres fournis
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            # Créer les répertoires nécessaires
            os.makedirs(self.sounds_dir, exist_ok=True)
            
            # Créer le répertoire de sortie
            output_dir = os.path.dirname(self.output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            logger.info(f"Générateur audio configuré: {self.sample_rate} Hz, {self.duration}s")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du générateur audio: {e}")
            return False
    
    def set_output_path(self, path: str) -> None:
        """
        Définit le chemin de sortie pour l'audio
        
        Args:
            path: Chemin du fichier de sortie
        """
        self.output_path = path
        # Créer le répertoire de sortie si nécessaire
        output_dir = os.path.dirname(path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    def set_duration(self, duration: float) -> None:
        """
        Définit la durée de l'audio
        
        Args:
            duration: Durée en secondes
        """
        self.duration = duration
    
    def apply_trend_data(self, trend_data: TrendData) -> None:
        """
        Applique les données de tendances au générateur
        
        Args:
            trend_data: Données de tendances à appliquer
        """
        self.trend_data = trend_data
        
        # Extraire le BPM/beat frequency
        if 'beat_frequency' in trend_data.timing_trends:
            self.beat_frequency = trend_data.timing_trends['beat_frequency']
            logger.info(f"BPM appliqué: {60.0/self.beat_frequency} BPM")
        
        # Télécharger une musique populaire si disponible
        if trend_data.popular_music:
            for music in trend_data.popular_music:
                if isinstance(music, dict) and 'url' in music and music['url']:
                    music_path = self._download_music(music['url'])
                    if music_path:
                        self.background_music = music_path
                        logger.info(f"Musique populaire téléchargée: {music_path}")
                        
                        # Extraire la mélodie
                        try:
                            self.current_melody = self._extract_melody_from_file(music_path)
                            logger.info(f"Mélodie extraite: {self.current_melody}")
                        except Exception as e:
                            logger.error(f"Erreur lors de l'extraction de la mélodie: {e}")
                        
                        break
    
    def _download_music(self, url: str) -> Optional[str]:
        """
        Télécharge une musique depuis une URL
        
        Args:
            url: URL de la musique à télécharger
            
        Returns:
            Chemin du fichier téléchargé, ou None en cas d'échec
        """
        try:
            # Créer un nom de fichier unique
            filename = os.path.join(self.sounds_dir, f"trend_music_{int(time.time())}.mp3")
            
            # Télécharger le fichier
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Musique téléchargée: {filename}")
                return filename
            else:
                logger.error(f"Erreur lors du téléchargement de la musique: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement de la musique: {e}")
            return None
    
    def _extract_melody_from_file(self, file_path: str) -> List[int]:
        """
        Extrait une mélodie à partir d'un fichier audio
        
        Args:
            file_path: Chemin du fichier audio
            
        Returns:
            Liste d'indices de notes (0-6 pour Do-Si)
        """
        try:
            # Charger le fichier audio
            y, sr = librosa.load(file_path, sr=None, duration=30)  # Limiter à 30s pour performance
            
            # Extraire les pics d'énergie
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            peaks = librosa.util.peak_pick(onset_env, 
                                          pre_max=3, post_max=3, 
                                          pre_avg=3, post_avg=5, 
                                          delta=0.5, wait=10)
            
            if len(peaks) == 0:
                return self.current_melody  # Garder la mélodie par défaut
            
            # Extraire les hauteurs (pitches)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            
            # Sélectionner les hauteurs dominantes aux pics d'énergie
            melody = []
            for i in range(min(8, len(peaks))):
                peak_idx = peaks[i]
                peak_pitches = pitches[:, peak_idx]
                peak_mags = magnitudes[:, peak_idx]
                
                # Trouver l'indice de la hauteur la plus forte
                if np.sum(peak_mags) == 0:
                    # Si pas de hauteur détectable, utiliser une note moyenne
                    melody.append(3)  # Fa (milieu de la gamme)
                else:
                    strongest_pitch_idx = np.argmax(peak_mags)
                    pitch_hz = peak_pitches[strongest_pitch_idx]
                    
                    # Convertir la fréquence en indice de note (Do-Si)
                    # Note: C4 (Do4) est à environ 261.63 Hz
                    if pitch_hz > 0:
                        # Convertir en échelle logarithmique (MIDI note)
                        midi_note = 12 * np.log2(pitch_hz / 440) + 69
                        
                        # Convertir en indice de note (0-6)
                        note_idx = int(midi_note % 12)
                        
                        # Mapper de 0-11 (chromatique) à 0-6 (diatonique Do majeur)
                        # C=0, D=2, E=4, F=5, G=7, A=9, B=11
                        diatonic_map = {0: 0, 2: 1, 4: 2, 5: 3, 7: 4, 9: 5, 11: 6}
                        closest_diatonic = min(diatonic_map.keys(), key=lambda x: abs(x - note_idx))
                        melody.append(diatonic_map[closest_diatonic])
                    else:
                        melody.append(3)  # Fa par défaut
            
            # Si pas assez de notes, répéter la séquence
            while len(melody) < 8:
                if len(melody) == 0:
                    melody = [0, 2, 4, 5, 4, 2, 0, 2]  # Mélodie par défaut
                else:
                    melody.append(melody[len(melody) % len(melody)])
            
            return melody
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de la mélodie: {e}")
            return self.current_melody  # Garder la mélodie par défaut
    
    def add_events(self, events: List[AudioEvent]) -> None:
        """
        Ajoute des événements audio à la timeline
        
        Args:
            events: Liste d'événements audio
        """
        self.events.extend(events)
        logger.info(f"{len(events)} événements audio ajoutés, total: {len(self.events)}")
    
    def _generate_basic_sounds(self) -> None:
        """Génère les sons de base (notes, effets, etc.)"""
        # Réinitialiser les listes
        self.notes = []
        self.effect_sounds = {}
        
        # Fréquences de base des notes (gamme de Do majeur)
        note_freqs = {
            0: 262,  # Do
            1: 294,  # Ré
            2: 330,  # Mi
            3: 349,  # Fa
            4: 392,  # Sol
            5: 440,  # La
            6: 494,  # Si
        }
        
        # Générer les notes pour différentes octaves
        logger.info("Génération des sons de notes...")
        for note_idx, freq in note_freqs.items():
            for octave, factor in enumerate([0.5, 1.0, 2.0]):
                note_freq = freq * factor
                note_path = os.path.join(self.sounds_dir, f"note_{note_idx}_oct{octave}.wav")
                
                # Vérifier si la note existe déjà
                if os.path.exists(note_path) and os.path.getsize(note_path) > 0:
                    self.notes.append((note_idx, octave, note_path))
                    continue
                
                # Générer la note
                self._generate_note(note_freq, note_path, note_idx, octave)
        
        # Générer les sons d'effets
        logger.info("Génération des sons d'effets...")
        self._generate_effect_sounds()
    
    def _generate_note(self, frequency: float, output_path: str, note_idx: int, octave: int) -> None:
        """
        Génère un son de note
        
        Args:
            frequency: Fréquence de la note en Hz
            output_path: Chemin du fichier de sortie
            note_idx: Indice de la note (0-6)
            octave: Octave (0-2)
        """
        try:
            # Paramètres
            duration = 0.5  # secondes
            sample_rate = self.sample_rate
            
            # Générer le signal
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            
            # Enveloppe ADSR
            attack = 0.1
            decay = 0.1
            sustain = 0.5
            release = 0.3
            
            # Générer l'enveloppe
            attack_samples = int(attack * sample_rate)
            decay_samples = int(decay * sample_rate)
            release_samples = int(release * sample_rate)
            sustain_samples = int(sample_rate * duration) - attack_samples - decay_samples - release_samples
            
            env = np.zeros(len(t))
            env[:attack_samples] = np.linspace(0, 1, attack_samples)
            env[attack_samples:attack_samples+decay_samples] = np.linspace(1, sustain, decay_samples)
            env[attack_samples+decay_samples:attack_samples+decay_samples+sustain_samples] = sustain
            env[attack_samples+decay_samples+sustain_samples:] = np.linspace(sustain, 0, release_samples)
            
            # Générer le son (sinusoïde avec harmoniques)
            signal = 0.7 * np.sin(2 * np.pi * frequency * t)  # Fondamentale
            signal += 0.2 * np.sin(2 * np.pi * frequency * 2 * t)  # 1ère harmonique
            signal += 0.1 * np.sin(2 * np.pi * frequency * 3 * t)  # 2ème harmonique
            
            # Appliquer l'enveloppe
            signal *= env
            
            # Normaliser
            signal = signal / np.max(np.abs(signal)) * 0.9
            
            # Convertir en stéréo
            stereo_signal = np.column_stack((signal, signal))
            
            # Sauvegarder en format WAV
            sf.write(output_path, stereo_signal, sample_rate)
            
            # Ajouter à la liste des notes
            self.notes.append((note_idx, octave, output_path))
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la note {note_idx} octave {octave}: {e}")
    
    def _generate_effect_sounds(self) -> None:
        """Génère les sons d'effets (explosion, activation, passage, etc.)"""
        # Sons d'explosion
        for size in ["small", "medium", "large"]:
            output_path = os.path.join(self.sounds_dir, f"explosion_{size}.wav")
            
            # Vérifier si le son existe déjà
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                if "explosion" not in self.effect_sounds:
                    self.effect_sounds["explosion"] = {}
                self.effect_sounds["explosion"][size] = output_path
                continue
            
            # Générer le son d'explosion
            try:
                # Paramètres selon la taille
                if size == "small":
                    duration = 0.5
                    base_freq = 100
                elif size == "medium":
                    duration = 0.7
                    base_freq = 80
                else:  # large
                    duration = 1.0
                    base_freq = 60
                
                sample_rate = self.sample_rate
                t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
                
                # Enveloppe rapide pour l'attaque, longue pour la décroissance
                env = np.ones(len(t))
                attack = int(0.05 * sample_rate)
                env[:attack] = np.linspace(0, 1, attack)
                env[int(0.2*len(t)):] = np.linspace(1, 0, len(t)-int(0.2*len(t)))
                
                # Bruit + sinusoïde grave
                noise = np.random.uniform(-1, 1, len(t))
                sine = np.sin(2 * np.pi * base_freq * t)
                
                # Mélanger bruit et sinusoïde
                signal = (0.7 * sine + 0.3 * noise) * env
                
                # Normaliser
                signal = signal / np.max(np.abs(signal)) * 0.9
                
                # Convertir en stéréo
                stereo_signal = np.column_stack((signal, signal))
                
                # Sauvegarder en format WAV
                sf.write(output_path, stereo_signal, sample_rate)
                
                # Ajouter au dictionnaire
                if "explosion" not in self.effect_sounds:
                    self.effect_sounds["explosion"] = {}
                self.effect_sounds["explosion"][size] = output_path
                
            except Exception as e:
                logger.error(f"Erreur lors de la génération du son d'explosion {size}: {e}")
        
        # Son d'activation
        activation_path = os.path.join(self.sounds_dir, "activation.wav")
        if not os.path.exists(activation_path) or os.path.getsize(activation_path) == 0:
            try:
                # Paramètres
                duration = 0.7
                sample_rate = self.sample_rate
                
                # Générer une rampe de fréquence ascendante
                t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
                freq = np.linspace(300, 1000, len(t))
                
                # Générer le signal
                phase = 2 * np.pi * np.cumsum(freq) / sample_rate
                signal = 0.8 * np.sin(phase)
                
                # Enveloppe
                env = np.ones(len(t))
                attack = int(0.1 * sample_rate)
                release = int(0.2 * sample_rate)
                env[:attack] = np.linspace(0, 1, attack)
                env[-release:] = np.linspace(1, 0, release)
                
                # Appliquer l'enveloppe
                signal *= env
                
                # Normaliser
                signal = signal / np.max(np.abs(signal)) * 0.9
                
                # Convertir en stéréo
                stereo_signal = np.column_stack((signal, signal))
                
                # Sauvegarder en format WAV
                sf.write(activation_path, stereo_signal, sample_rate)
                
                # Ajouter au dictionnaire
                self.effect_sounds["activation"] = {"default": activation_path}
                
            except Exception as e:
                logger.error(f"Erreur lors de la génération du son d'activation: {e}")
        else:
            self.effect_sounds["activation"] = {"default": activation_path}
        
        # Son de passage
        passage_path = os.path.join(self.sounds_dir, "passage.wav")
        if not os.path.exists(passage_path) or os.path.getsize(passage_path) == 0:
            try:
                # Paramètres
                duration = 0.3
                sample_rate = self.sample_rate
                
                # Générer un son bref avec une fréquence élevée
                t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
                freq = 1200
                
                # Générer le signal avec un vibrato
                vibrato_freq = 20
                vibrato_depth = 100
                freq_mod = freq + vibrato_depth * np.sin(2 * np.pi * vibrato_freq * t)
                phase = 2 * np.pi * np.cumsum(freq_mod) / sample_rate
                signal = 0.8 * np.sin(phase)
                
                # Enveloppe rapide
                env = np.ones(len(t))
                attack = int(0.05 * sample_rate)
                release = int(0.1 * sample_rate)
                env[:attack] = np.linspace(0, 1, attack)
                env[-release:] = np.linspace(1, 0, release)
                
                # Appliquer l'enveloppe
                signal *= env
                
                # Normaliser
                signal = signal / np.max(np.abs(signal)) * 0.9
                
                # Convertir en stéréo
                stereo_signal = np.column_stack((signal, signal))
                
                # Sauvegarder en format WAV
                sf.write(passage_path, stereo_signal, sample_rate)
                
                # Ajouter au dictionnaire
                self.effect_sounds["passage"] = {"default": passage_path}
                
            except Exception as e:
                logger.error(f"Erreur lors de la génération du son de passage: {e}")
        else:
            self.effect_sounds["passage"] = {"default": passage_path}
    
    def _get_sound_path(self, event: AudioEvent) -> Optional[str]:
        """
        Récupère le chemin du fichier son correspondant à un événement
        
        Args:
            event: Événement audio
            
        Returns:
            Chemin du fichier son, ou None si non trouvé
        """
        event_type = event.event_type
        params = event.params or {}
        
        if event_type == "note":
            note_idx = params.get("note", 0)
            octave = params.get("octave", 1)
            return os.path.join(self.sounds_dir, f"note_{note_idx}_oct{octave}.wav")
            
        elif event_type == "explosion":
            size = params.get("size", "medium")
            if "explosion" in self.effect_sounds and size in self.effect_sounds["explosion"]:
                return self.effect_sounds["explosion"][size]
            return os.path.join(self.sounds_dir, f"explosion_{size}.wav")
            
        elif event_type == "activation":
            if "activation" in self.effect_sounds:
                return self.effect_sounds["activation"]["default"]
            return os.path.join(self.sounds_dir, "activation.wav")
            
        elif event_type == "passage":
            if "passage" in self.effect_sounds:
                return self.effect_sounds["passage"]["default"]
            return os.path.join(self.sounds_dir, "passage.wav")
        
        # Type d'événement non géré
        logger.warning(f"Type d'événement audio non géré: {event_type}")
        return None
    
    def _add_beats_from_music(self) -> None:
        """Génère des événements beat à partir de la musique de fond"""
        if not self.background_music or not os.path.exists(self.background_music):
            return
        
        try:
            # Charger la musique
            y, sr = librosa.load(self.background_music, sr=None, duration=self.duration)
            
            # Détecter les beats
            _, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            
            # Créer des événements beat
            beat_events = []
            for i, beat_time in enumerate(beat_times):
                if beat_time <= self.duration:
                    # Alternance des notes sur les temps forts/faibles
                    note_idx = self.current_melody[i % len(self.current_melody)]
                    octave = 1 if i % 4 == 0 else 0  # Temps fort = octave plus haute
                    
                    event = AudioEvent(
                        event_type="note",
                        time=beat_time,
                        position=None,  # Pas de position spatiale pour les beats
                        params={"note": note_idx, "octave": octave}
                    )
                    beat_events.append(event)
            
            # Ajouter les événements
            self.events.extend(beat_events)
            logger.info(f"{len(beat_events)} événements beat extraits de la musique")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des beats: {e}")
    
    def generate(self) -> Optional[str]:
        """
        Génère la piste audio finale
        
        Returns:
            Chemin de la piste audio générée, ou None en cas d'échec
        """
        try:
            # Générer les sons de base
            self._generate_basic_sounds()
            
            # Si pas d'événements mais musique de fond, extraire les beats
            if not self.events and self.background_music:
                self._add_beats_from_music()
            
            logger.info(f"Génération de la piste audio à partir de {len(self.events)} événements...")
            
            # Si aucun événement et pas de musique de fond, créer un fichier audio silencieux
            if not self.events and not self.background_music:
                logger.warning("Aucun événement audio et pas de musique de fond, création d'un fichier audio silencieux")
                return self._create_silent_audio()
            
            # Si musique de fond mais pas d'événements, utiliser directement la musique
            if self.background_music and not self.events:
                logger.info("Utilisation directe de la musique de fond")
                return self._use_background_music()
            
            # Créer la timeline audio
            timeline = np.zeros((int(self.sample_rate * self.duration), 2), dtype=np.float32)
            
            # Ajouter les événements sonores
            events_processed = 0
            for event in self.events:
                # Ignorer les événements hors de la durée
                if event.time >= self.duration:
                    continue
                
                # Récupérer le fichier son
                sound_path = self._get_sound_path(event)
                if not sound_path or not os.path.exists(sound_path):
                    continue
                
                try:
                    # Charger le son
                    if sound_path.endswith('.wav'):
                        data, sr = sf.read(sound_path)
                    else:
                        # Utiliser librosa pour d'autres formats
                        data, sr = librosa.load(sound_path, sr=self.sample_rate, mono=False)
                        if data.ndim == 1:  # Mono → stéréo
                            data = np.column_stack((data, data))
                    
                    # Vérifier que le son est bien en stéréo
                    if data.ndim == 1:  # Mono → stéréo
                        data = np.column_stack((data, data))
                    
                    # Calcul des indices dans la timeline
                    start_idx = int(event.time * self.sample_rate)
                    end_idx = min(start_idx + len(data), len(timeline))
                    data_len = end_idx - start_idx
                    
                    # Appliquer le volume selon le type d'événement
                    volume = 1.0
                    if event.event_type == "note":
                        volume = self.note_volume
                    elif event.event_type == "explosion":
                        volume = self.explosion_volume
                    elif event.event_type == "activation":
                        volume = self.activation_volume
                    elif event.event_type == "passage":
                        volume = self.passage_volume
                    
                    # Ajouter à la timeline
                    timeline[start_idx:end_idx] += data[:data_len] * volume
                    events_processed += 1
                    
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de l'événement audio {event.event_type}: {e}")
            
            # Mélanger avec la musique de fond si disponible
            if self.background_music and os.path.exists(self.background_music):
                timeline = self._mix_background_music(timeline)
            
            # Normaliser la timeline
            max_val = np.max(np.abs(timeline))
            if max_val > 1.0:
                timeline = timeline / max_val * 0.95  # Laisser une marge
            
            # Convertir en int16 pour le fichier WAV
            audio_data = (timeline * 32767).astype(np.int16)
            
            # Sauvegarder en format WAV
            wavfile.write(self.output_path, self.sample_rate, audio_data)
            
            logger.info(f"Piste audio générée avec succès: {self.output_path} ({events_processed}/{len(self.events)} événements traités)")
            return self.output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la piste audio: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_silent_audio(self) -> str:
        """
        Crée un fichier audio silencieux
        
        Returns:
            Chemin du fichier audio créé
        """
        # Créer un signal silencieux
        silence = np.zeros((int(self.sample_rate * self.duration), 2), dtype=np.float32)
        
        # Convertir en int16
        silence_int16 = (silence * 32767).astype(np.int16)
        
        # Sauvegarder en format WAV
        wavfile.write(self.output_path, self.sample_rate, silence_int16)
        
        return self.output_path
    
    def _use_background_music(self) -> str:
        """
        Utilise directement la musique de fond comme sortie
        
        Returns:
            Chemin du fichier audio créé
        """
        try:
            # Charger la musique
            if self.background_music.endswith('.wav'):
                data, sr = sf.read(self.background_music)
            else:
                # Utiliser librosa pour d'autres formats
                data, sr = librosa.load(self.background_music, sr=self.sample_rate, mono=False)
            
            # Vérifier que c'est bien en stéréo
            if data.ndim == 1:  # Mono → stéréo
                data = np.column_stack((data, data))
            
            # Ajuster la durée
            if len(data) / sr > self.duration:
                # Couper si trop long
                data = data[:int(self.duration * sr)]
            elif len(data) / sr < self.duration:
                # Ajouter du silence si trop court
                padding = np.zeros((int(self.duration * sr) - len(data), 2), dtype=data.dtype)
                data = np.vstack((data, padding))
            
            # Normaliser
            if data.dtype == np.float32 or data.dtype == np.float64:
                max_val = np.max(np.abs(data))
                if max_val > 0:
                    data = data / max_val * 0.95
                
                # Convertir en int16
                data = (data * 32767).astype(np.int16)
            
            # Sauvegarder en format WAV
            wavfile.write(self.output_path, self.sample_rate, data)
            
            return self.output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de l'utilisation directe de la musique de fond: {e}")
            return self._create_silent_audio()
    
    def _mix_background_music(self, timeline: np.ndarray) -> np.ndarray:
        """
        Mélange la musique de fond avec la timeline existante
        
        Args:
            timeline: Timeline audio existante
            
        Returns:
            Timeline mixée
        """
        try:
            # Charger la musique
            if self.background_music.endswith('.wav'):
                data, sr = sf.read(self.background_music)
            else:
                # Utiliser librosa pour d'autres formats
                data, sr = librosa.load(self.background_music, sr=self.sample_rate, mono=False)
            
            # Vérifier que c'est bien en stéréo
            if data.ndim == 1:  # Mono → stéréo
                data = np.column_stack((data, data))
            
            # Convertir en float32 si nécessaire
            if data.dtype == np.int16:
                data = data.astype(np.float32) / 32767.0
            
            # Resample si nécessaire
            if sr != self.sample_rate:
                data = librosa.resample(data.T, orig_sr=sr, target_sr=self.sample_rate).T
            
            # Ajuster la durée
            if len(data) > len(timeline):
                # Couper si trop long
                data = data[:len(timeline)]
            elif len(data) < len(timeline):
                # Ajouter du silence si trop court ou boucler
                if len(data) > len(timeline) / 2:
                    # Ajouter du silence
                    padding = np.zeros((len(timeline) - len(data), 2), dtype=data.dtype)
                    data = np.vstack((data, padding))
                else:
                    # Boucler
                    repeats = int(np.ceil(len(timeline) / len(data)))
                    data = np.tile(data, (repeats, 1))[:len(timeline)]
            
            # Mélanger avec la timeline (70% musique, 100% effets)
            mixed_timeline = timeline + data * 0.7
            
            return mixed_timeline
            
        except Exception as e:
            logger.error(f"Erreur lors du mixage de la musique de fond: {e}")
            return timeline