# audio_generators/trend_audio_generator.py
"""
Générateur audio amélioré avec sons satisfaisants et extraction de mélodie pure
Version focalisée sur la beauté sonore et la mélodie principale
"""

import os
import time
import logging
import numpy as np
import librosa
import soundfile as sf
from scipy.io import wavfile
from scipy import signal
from typing import Dict, List, Any, Optional, Tuple, Union
import random
import requests
from pathlib import Path
import json
import re
from urllib.parse import urljoin, urlparse, quote
import mido  # Pour les fichiers MIDI
from bs4 import BeautifulSoup
import math

from core.interfaces import IAudioGenerator, TrendData, AudioEvent

logger = logging.getLogger("TikSimPro")

class TrendAudioGenerator(IAudioGenerator):
    """
    Générateur audio amélioré avec sons satisfaisants et mélodie pure
    Focus sur la beauté sonore et l'extraction de mélodie principale
    """
    
    def __init__(self, note_volume = 0.8, explosion_volume = 0.6, activation_volume = 0.7, passage_volume = 0.5):
        """Initialise le générateur audio amélioré"""
        # Paramètres par défaut
        self.sample_rate = 44100
        self.duration = 30.0
        self.output_path = "output/audio.wav"
        self.sounds_dir = "temp/sounds"
        self.midi_dir = "temp/midi"
        
        # Volume optimisé pour des sons agréables
        self.note_volume = note_volume
        self.explosion_volume = explosion_volume
        self.activation_volume = activation_volume
        self.passage_volume = passage_volume

        # Créer les répertoires nécessaires
        os.makedirs(self.sounds_dir, exist_ok=True)
        os.makedirs(self.midi_dir, exist_ok=True)
        
        # Événements audio
        self.events = []
        
        # Données de tendances
        self.trend_data = None
        
        # Sons de base améliorés
        self.notes = []  # (note_idx, octave, path)
        self.effect_sounds = {}  # {type_effect: {param: path}}
        self.background_music = None
        
        # Palette sonore améliorée
        self.current_melody = [0, 2, 4, 5, 4, 2, 0, 2]  # Do majeur par défaut
        self.beat_frequency = 1.0
        
        # NOUVEAU : Paramètres pour sons satisfaisants
        self.harmonic_richness = 0.7  # Richesse harmonique
        self.reverb_amount = 0.3      # Quantité de reverb
        self.attack_time = 0.05       # Temps d'attaque rapide
        self.release_time = 1.2       # Temps de release plus long
        self.stereo_width = 0.6       # Largeur stéréo
        
        # NOUVEAU : Gammes satisfaisantes
        self.satisfying_scales = {
            "pentatonic": [0, 2, 4, 7, 9],           # Pentatonique (très satisfaisant)
            "major": [0, 2, 4, 5, 7, 9, 11],        # Majeur classique
            "dorian": [0, 2, 3, 5, 7, 9, 10],       # Dorien (moderne)
            "lydian": [0, 2, 4, 6, 7, 9, 11],       # Lydien (dreamy)
            "mixolydian": [0, 2, 4, 5, 7, 9, 10]    # Mixolydien (blues)
        }
        self.current_scale = "pentatonic"  # Commencer avec la plus satisfaisante
        
        # Base de données de musiques populaires
        self.popular_songs_db = self._load_popular_songs_db()
        
        # Cache des téléchargements
        self.download_cache = {}

        logger.info("TrendAudioGenerator amélioré initialisé - Sons satisfaisants et mélodie pure")
    
    def _load_popular_songs_db(self) -> Dict[str, List]:
        """Charge la base de données des musiques populaires (version simplifiée pour focus mélodie)"""
        try:
            # Version focalisée sur des mélodies connues et satisfaisantes
            return {
                "trending": [
                    {"title": "Shape of You", "artist": "Ed Sheeran", "keywords": ["shape", "you"], "musescore_search": "Shape of You Ed Sheeran", "genre": "pop", "melodic_rating": 9},
                    {"title": "Blinding Lights", "artist": "The Weeknd", "keywords": ["blinding", "lights"], "musescore_search": "Blinding Lights Weeknd", "genre": "synthpop", "melodic_rating": 8},
                    {"title": "Watermelon Sugar", "artist": "Harry Styles", "keywords": ["watermelon", "sugar"], "musescore_search": "Watermelon Sugar Harry Styles", "genre": "pop", "melodic_rating": 8},
                    {"title": "Levitating", "artist": "Dua Lipa", "keywords": ["levitating"], "musescore_search": "Levitating Dua Lipa", "genre": "disco", "melodic_rating": 9},
                    {"title": "Anti-Hero", "artist": "Taylor Swift", "keywords": ["anti", "hero"], "musescore_search": "Anti Hero Taylor Swift", "genre": "pop", "melodic_rating": 8}
                ],
                "classical": [
                    {"title": "Für Elise", "artist": "Beethoven", "keywords": ["fur", "elise"], "musescore_search": "Fur Elise Beethoven", "genre": "classical", "melodic_rating": 10},
                    {"title": "Canon in D", "artist": "Pachelbel", "keywords": ["canon"], "musescore_search": "Canon in D Pachelbel", "genre": "classical", "melodic_rating": 9},
                    {"title": "Moonlight Sonata", "artist": "Beethoven", "keywords": ["moonlight"], "musescore_search": "Moonlight Sonata Beethoven", "genre": "classical", "melodic_rating": 10},
                    {"title": "Claire de Lune", "artist": "Debussy", "keywords": ["claire", "lune"], "musescore_search": "Claire de Lune Debussy", "genre": "classical", "melodic_rating": 9}
                ],
                "gaming": [
                    {"title": "Sweden", "artist": "C418", "keywords": ["minecraft", "sweden"], "musescore_search": "Minecraft Sweden C418", "genre": "ambient", "melodic_rating": 8},
                    {"title": "Zelda Main Theme", "artist": "Nintendo", "keywords": ["zelda", "theme"], "musescore_search": "Zelda Main Theme", "genre": "game", "melodic_rating": 9},
                    {"title": "Tetris Theme", "artist": "Hirokazu Tanaka", "keywords": ["tetris"], "musescore_search": "Tetris Theme", "genre": "chiptune", "melodic_rating": 8}
                ],
                "viral_tiktok": []
            }
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la base de données: {e}")
            return {"trending": [], "classical": [], "gaming": [], "viral_tiktok": []}
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure le générateur avec des paramètres spécifiques"""
        try:
            # Appliquer les paramètres fournis
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            # Créer les répertoires nécessaires
            os.makedirs(self.sounds_dir, exist_ok=True)
            os.makedirs(self.midi_dir, exist_ok=True)
            
            # Créer le répertoire de sortie
            output_dir = os.path.dirname(self.output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            logger.info(f"Générateur audio amélioré configuré: {self.sample_rate} Hz, {self.duration}s")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration: {e}")
            return False
    
    def set_output_path(self, path: str) -> None:
        """Définit le chemin de sortie pour l'audio"""
        self.output_path = path
        output_dir = os.path.dirname(path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    def set_duration(self, duration: float) -> None:
        """Définit la durée de l'audio"""
        self.duration = duration
    
    def apply_trend_data(self, trend_data: TrendData) -> None:
        """Applique les données de tendances au générateur"""
        self.trend_data = trend_data
        
        # Extraire le BPM/beat frequency
        if 'beat_frequency' in trend_data.timing_trends:
            self.beat_frequency = trend_data.timing_trends['beat_frequency']
            logger.info(f"BPM appliqué: {60.0/self.beat_frequency} BPM")
        
        # Rechercher et télécharger automatiquement des musiques populaires
        self._auto_download_trending_music(trend_data)
    
    def _auto_download_trending_music(self, trend_data: TrendData) -> None:
        """Télécharge automatiquement des musiques tendance avec focus mélodie"""
        try:
            songs_to_download = []
            
            # Prioriser les musiques avec un rating mélodique élevé
            all_songs = []
            for category, songs in self.popular_songs_db.items():
                all_songs.extend(songs)
            
            # Trier par rating mélodique
            all_songs.sort(key=lambda x: x.get('melodic_rating', 5), reverse=True)
            songs_to_download = all_songs[:3]  # Top 3 mélodiques
            
            # Télécharger les musiques
            for song in songs_to_download:
                midi_path = self._download_midi_from_song_info(song)
                if midi_path:
                    self.background_music = midi_path
                    # Extraire UNIQUEMENT la mélodie principale
                    try:
                        self.current_melody = self._extract_pure_melody_from_midi(midi_path)
                        logger.info(f"Mélodie pure extraite: {self.current_melody}")
                        break
                    except Exception as e:
                        logger.error(f"Erreur extraction mélodie: {e}")
                        
        except Exception as e:
            logger.error(f"Erreur téléchargement automatique: {e}")
    
    def _download_midi_from_song_info(self, song_info: Dict) -> Optional[str]:
        """Télécharge un fichier MIDI (version simplifiée pour focus mélodie)"""
        try:
            cache_key = f"{song_info['title']}_{song_info['artist']}".replace(" ", "_")
            cached_path = os.path.join(self.midi_dir, f"{cache_key}.mid")
            
            # Vérifier le cache
            if os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
                logger.info(f"MIDI trouvé dans le cache: {cached_path}")
                return cached_path
            
            # Pour le moment, utiliser des MIDIs de test ou synthétiques
            # En production, on implémenterait le téléchargement réel
            return self._create_synthetic_melody_midi(song_info, cached_path)
            
        except Exception as e:
            logger.error(f"Erreur téléchargement MIDI: {e}")
            return None
    
    def _create_synthetic_melody_midi(self, song_info: Dict, output_path: str) -> Optional[str]:
        """Crée un MIDI synthétique avec une mélodie satisfaisante"""
        try:
            # Créer un fichier MIDI simple avec une mélodie basée sur le genre
            mid = mido.MidiFile()
            track = mido.MidiTrack()
            mid.tracks.append(track)
            
            # Paramètres selon le genre
            genre = song_info.get('genre', 'pop')
            if genre == 'classical':
                scale = self.satisfying_scales['major']
                tempo = 480  # Plus lent
                note_duration = 960
            elif genre == 'pop':
                scale = self.satisfying_scales['pentatonic']
                tempo = 480
                note_duration = 480
            elif genre == 'ambient':
                scale = self.satisfying_scales['dorian']
                tempo = 960  # Très lent
                note_duration = 1920
            else:
                scale = self.satisfying_scales['pentatonic']
                tempo = 480
                note_duration = 480
            
            # Ajouter les événements MIDI
            track.append(mido.MetaMessage('set_tempo', tempo=tempo))
            
            # Créer une mélodie satisfaisante basée sur la gamme
            base_note = 60  # C4
            melody_pattern = self._generate_satisfying_melody_pattern(scale)
            
            time_pos = 0
            for i, note_offset in enumerate(melody_pattern):
                note = base_note + note_offset
                
                # Note on
                track.append(mido.Message('note_on', channel=0, note=note, velocity=80, time=time_pos))
                # Note off
                track.append(mido.Message('note_off', channel=0, note=note, velocity=0, time=note_duration))
                
                time_pos = 0  # Le timing est dans les messages précédents
            
            # Sauvegarder le MIDI
            mid.save(output_path)
            logger.info(f"MIDI synthétique créé: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur création MIDI synthétique: {e}")
            return None
    
    def _generate_satisfying_melody_pattern(self, scale: List[int]) -> List[int]:
        """Génère un motif mélodique satisfaisant"""
        # Motifs mélodiques populaires et satisfaisants
        patterns = [
            # Montée puis descente (très satisfaisant)
            [0, 1, 2, 3, 4, 3, 2, 1, 0],
            # Arpège majeur
            [0, 2, 4, 7, 4, 2, 0],
            # Motif pentatonique
            [0, 2, 4, 7, 9, 7, 4, 2],
            # Progression romantique
            [0, 4, 7, 9, 7, 4, 2, 0]
        ]
        
        # Choisir un motif et l'adapter à la gamme
        base_pattern = random.choice(patterns)
        melody = []
        
        for step in base_pattern:
            if step < len(scale):
                melody.append(scale[step])
            else:
                melody.append(scale[step % len(scale)] + 12)  # Octave supérieure
        
        return melody
    
    def _extract_pure_melody_from_midi(self, midi_path: str) -> List[int]:
        """
        NOUVEAU: Extrait UNIQUEMENT la mélodie principale (main droite) d'un MIDI
        """
        try:
            mid = mido.MidiFile(midi_path)
            
            # Analyser toutes les pistes pour trouver la mélodie principale
            melody_candidates = []
            
            for track_idx, track in enumerate(mid.tracks):
                track_notes = []
                current_time = 0
                
                for msg in track:
                    if hasattr(msg, 'time'):
                        current_time += msg.time
                    
                    # Ignorer la piste de batterie (channel 9)
                    if hasattr(msg, 'channel') and msg.channel == 9:
                        continue
                    
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Se concentrer sur les notes aiguës (main droite)
                        if msg.note >= 60:  # C4 et plus (main droite)
                            track_notes.append({
                                'note': msg.note,
                                'time': current_time,
                                'velocity': msg.velocity
                            })
                
                if track_notes:
                    # Évaluer la "mélodicité" de cette piste
                    melodic_score = self._evaluate_melodic_quality(track_notes)
                    melody_candidates.append({
                        'track_idx': track_idx,
                        'notes': track_notes,
                        'score': melodic_score
                    })
            
            if not melody_candidates:
                logger.warning("Aucune mélodie trouvée, utilisation de la mélodie par défaut")
                return self.current_melody
            
            # Prendre la meilleure piste mélodique
            best_melody = max(melody_candidates, key=lambda x: x['score'])
            melody_notes = best_melody['notes']
            
            # Extraire uniquement la ligne mélodique (note la plus aiguë à chaque moment)
            pure_melody = self._extract_top_line_melody(melody_notes)
            
            # Convertir en indices diatoniques satisfaisants
            diatonic_melody = self._convert_to_satisfying_scale(pure_melody)
            
            logger.info(f"Mélodie pure extraite de la piste {best_melody['track_idx']}: {diatonic_melody}")
            return diatonic_melody
            
        except Exception as e:
            logger.error(f"Erreur extraction mélodie pure: {e}")
            return self.current_melody
    
    def _evaluate_melodic_quality(self, notes: List[Dict]) -> float:
        """Évalue la qualité mélodique d'une séquence de notes"""
        if len(notes) < 2:
            return 0.0
        
        score = 0.0
        
        # 1. Nombre de notes (plus = mieux pour mélodie)
        score += min(len(notes) / 20, 1.0) * 0.3
        
        # 2. Registre (notes aiguës = mélodie principale)
        avg_pitch = sum(note['note'] for note in notes) / len(notes)
        if avg_pitch >= 72:  # C5+
            score += 0.4
        elif avg_pitch >= 60:  # C4-C5
            score += 0.3
        else:
            score += 0.1
        
        # 3. Mouvement mélodique (intervalles variés mais pas trop grands)
        intervals = []
        for i in range(1, len(notes)):
            interval = abs(notes[i]['note'] - notes[i-1]['note'])
            intervals.append(interval)
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            # Mouvement idéal: 1-5 demi-tons
            if 1 <= avg_interval <= 5:
                score += 0.3
            elif avg_interval <= 8:
                score += 0.2
        
        return score
    
    def _extract_top_line_melody(self, notes: List[Dict]) -> List[int]:
        """Extrait la ligne mélodique supérieure (note la plus aiguë à chaque moment)"""
        if not notes:
            return []
        
        # Grouper les notes par tranches de temps
        time_groups = {}
        time_resolution = 100  # Résolution temporelle
        
        for note in notes:
            time_slot = int(note['time'] / time_resolution) * time_resolution
            if time_slot not in time_groups:
                time_groups[time_slot] = []
            time_groups[time_slot].append(note['note'])
        
        # Extraire la note la plus aiguë de chaque tranche
        melody_line = []
        for time_slot in sorted(time_groups.keys()):
            highest_note = max(time_groups[time_slot])
            melody_line.append(highest_note)
        
        return melody_line[:16]  # Limiter à 16 notes pour la mélodie
    
    def _convert_to_satisfying_scale(self, midi_notes: List[int]) -> List[int]:
        """Convertit des notes MIDI en indices de gamme satisfaisante"""
        scale = self.satisfying_scales[self.current_scale]
        diatonic_melody = []
        
        for midi_note in midi_notes:
            # Convertir en classe de hauteur (0-11)
            pitch_class = midi_note % 12
            
            # Trouver la note la plus proche dans la gamme satisfaisante
            closest_scale_note = min(scale, key=lambda x: abs(x - pitch_class))
            scale_index = scale.index(closest_scale_note)
            
            diatonic_melody.append(scale_index)
        
        return diatonic_melody[:8]  # Limiter à 8 notes
    
    def add_events(self, events: List[AudioEvent]) -> None:
        """Ajoute des événements audio à la timeline"""
        self.events.extend(events)
        logger.info(f"{len(events)} événements audio ajoutés, total: {len(self.events)}")
    
    def _generate_basic_sounds(self) -> None:
        """Génère les sons de base AMÉLIORÉS (plus satisfaisants)"""
        self.notes = []
        self.effect_sounds = {}
        
        # Fréquences de base de la gamme satisfaisante actuelle
        scale = self.satisfying_scales[self.current_scale]
        base_freq = 261.63  # C4
        
        logger.info(f"Génération de sons satisfaisants avec la gamme {self.current_scale}...")
        
        # Générer les notes satisfaisantes
        for scale_idx, semitone_offset in enumerate(scale):
            for octave, octave_factor in enumerate([0.5, 1.0, 2.0]):
                note_freq = base_freq * (2 ** (semitone_offset / 12)) * octave_factor
                note_path = os.path.join(self.sounds_dir, f"satisfying_note_{scale_idx}_oct{octave}.wav")
                
                if os.path.exists(note_path) and os.path.getsize(note_path) > 0:
                    self.notes.append((scale_idx, octave, note_path))
                    continue
                
                # Générer la note satisfaisante
                self._generate_satisfying_note(note_freq, note_path, scale_idx, octave)
        
        # Générer les effets améliorés
        logger.info("Génération d'effets sonores satisfaisants...")
        self._generate_satisfying_effects()
    
    def _generate_satisfying_note(self, frequency: float, output_path: str, note_idx: int, octave: int) -> None:
        """
        NOUVEAU: Génère une note avec un son beaucoup plus satisfaisant
        """
        try:
            duration = 1.5  # Plus long pour plus de satisfaction
            sample_rate = self.sample_rate
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            
            # Enveloppe ADSR satisfaisante
            attack_samples = int(self.attack_time * sample_rate)
            decay_samples = int(0.3 * sample_rate)
            release_samples = int(self.release_time * sample_rate)
            sustain_samples = len(t) - attack_samples - decay_samples - release_samples
            
            env = np.zeros(len(t))
            
            # Attaque rapide et douce
            env[:attack_samples] = 1 - np.exp(-np.linspace(0, 5, attack_samples))
            
            # Decay vers sustain
            sustain_level = 0.7
            env[attack_samples:attack_samples+decay_samples] = np.linspace(1, sustain_level, decay_samples)
            
            # Sustain
            if sustain_samples > 0:
                env[attack_samples+decay_samples:attack_samples+decay_samples+sustain_samples] = sustain_level
            
            # Release exponentiel
            env[attack_samples+decay_samples+sustain_samples:] = sustain_level * np.exp(-np.linspace(0, 5, release_samples))
            
            # Génération du signal RICHE EN HARMONIQUES
            signal = np.zeros(len(t))
            
            # Fondamentale (60%)
            signal += 0.6 * np.sin(2 * np.pi * frequency * t)
            
            # Harmoniques satisfaisantes
            signal += 0.25 * np.sin(2 * np.pi * frequency * 2 * t)  # Octave
            signal += 0.15 * np.sin(2 * np.pi * frequency * 3 * t)  # Quinte
            signal += 0.1 * np.sin(2 * np.pi * frequency * 4 * t)   # Double octave
            signal += 0.05 * np.sin(2 * np.pi * frequency * 5 * t)  # Tierce majeure haute
            
            # Modulation FM légère pour la richesse
            mod_freq = frequency * 0.01
            mod_depth = 0.1
            fm_mod = mod_depth * np.sin(2 * np.pi * mod_freq * t)
            signal = signal * (1 + fm_mod)
            
            # Appliquer l'enveloppe
            signal *= env
            
            # Ajouter de la réverb artificielle
            signal = self._add_artificial_reverb(signal, sample_rate)
            
            # Créer un effet stéréo satisfaisant
            left_channel = signal
            right_channel = signal * 0.95  # Légère différence pour la largeur stéréo
            
            # Delay stéréo pour largeur
            delay_samples = int(0.02 * sample_rate)  # 20ms
            right_delayed = np.zeros_like(right_channel)
            right_delayed[delay_samples:] = right_channel[:-delay_samples]
            right_channel = 0.7 * right_channel + 0.3 * right_delayed
            
            # Combiner en stéréo
            stereo_signal = np.column_stack((left_channel, right_channel))
            
            # Normaliser avec headroom
            max_val = np.max(np.abs(stereo_signal))
            if max_val > 0:
                stereo_signal = stereo_signal / max_val * 0.85
            
            # Sauvegarder
            sf.write(output_path, stereo_signal, sample_rate)
            self.notes.append((note_idx, octave, output_path))
            
        except Exception as e:
            logger.error(f"Erreur génération note satisfaisante {note_idx}: {e}")
    
    def _add_artificial_reverb(self, signal: np.ndarray, sample_rate: int) -> np.ndarray:
        """Ajoute une réverb artificielle simple mais efficace"""
        try:
            # Paramètres de réverb
            reverb_decay = 0.3
            reverb_delay = int(0.05 * sample_rate)  # 50ms
            
            # Créer le signal de réverb
            reverb_signal = np.zeros_like(signal)
            
            # Plusieurs échos avec décroissance
            for i, delay in enumerate([reverb_delay, reverb_delay*2, reverb_delay*3]):
                if delay < len(signal):
                    decay_factor = reverb_decay * (0.6 ** i)
                    reverb_signal[delay:] += signal[:-delay] * decay_factor
            
            # Mélanger avec le signal original
            return signal + reverb_signal * self.reverb_amount
            
        except Exception as e:
            logger.error(f"Erreur ajout réverb: {e}")
            return signal
    
    def _generate_satisfying_effects(self) -> None:
        """Génère des effets sonores plus satisfaisants"""
        # Explosion satisfaisante (moins agressive)
        for size in ["small", "medium", "large"]:
            output_path = os.path.join(self.sounds_dir, f"satisfying_explosion_{size}.wav")
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                if "explosion" not in self.effect_sounds:
                    self.effect_sounds["explosion"] = {}
                self.effect_sounds["explosion"][size] = output_path
                continue
            
            try:
                if size == "small":
                    duration, base_freq, intensity = 0.8, 150, 0.6
                elif size == "medium":
                    duration, base_freq, intensity = 1.2, 120, 0.7
                else:  # large
                    duration, base_freq, intensity = 1.8, 100, 0.8
                
                sample_rate = self.sample_rate
                t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
                
                # Enveloppe douce
                env = np.exp(-t * 3)  # Décroissance exponentielle
                
                # Son moins agressif - mélange de fréquences harmoniques
                signal = np.zeros(len(t))
                signal += 0.4 * np.sin(2 * np.pi * base_freq * t)
                signal += 0.3 * np.sin(2 * np.pi * base_freq * 1.5 * t)
                signal += 0.2 * np.sin(2 * np.pi * base_freq * 2 * t)
                
                # Bruit filtré au lieu de bruit blanc pur
                noise = np.random.uniform(-1, 1, len(t))
                # Filtre passe-bas pour adoucir le bruit
                b, a = signal.butter(3, 0.3)
                filtered_noise = signal.filtfilt(b, a, noise)
                
                # Mélanger harmoniques et bruit filtré
                signal = (0.7 * signal + 0.3 * filtered_noise) * env * intensity
                
                # Ajouter réverb
                signal = self._add_artificial_reverb(signal, sample_rate)
                
                # Normaliser
                signal = signal / np.max(np.abs(signal)) * 0.8
                
                # Stéréo
                stereo_signal = np.column_stack((signal, signal))
                sf.write(output_path, stereo_signal, sample_rate)
                
                if "explosion" not in self.effect_sounds:
                    self.effect_sounds["explosion"] = {}
                self.effect_sounds["explosion"][size] = output_path
                
            except Exception as e:
                logger.error(f"Erreur génération explosion satisfaisante {size}: {e}")
        
        # Activation satisfaisante (son montant doux)
        activation_path = os.path.join(self.sounds_dir, "satisfying_activation.wav")
        if not os.path.exists(activation_path):
            try:
                duration = 1.0
                sample_rate = self.sample_rate
                t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
                
                # Fréquence montante douce
                freq_start, freq_end = 300, 800
                freq = np.linspace(freq_start, freq_end, len(t))
                
                # Signal harmonique riche
                phase = 2 * np.pi * np.cumsum(freq) / sample_rate
                signal = 0.6 * np.sin(phase)
                signal += 0.3 * np.sin(2 * phase)  # Harmonique
                signal += 0.1 * np.sin(3 * phase)  # Harmonique supérieure
                
                # Enveloppe douce
                env = np.sin(np.pi * t / duration) ** 2  # Enveloppe en cloche
                signal *= env
                
                # Ajouter réverb
                signal = self._add_artificial_reverb(signal, sample_rate)
                
                # Normaliser
                signal = signal / np.max(np.abs(signal)) * 0.8
                
                stereo_signal = np.column_stack((signal, signal))
                sf.write(activation_path, stereo_signal, sample_rate)
                
                self.effect_sounds["activation"] = {"default": activation_path}
                
            except Exception as e:
                logger.error(f"Erreur génération activation satisfaisante: {e}")
        else:
            self.effect_sounds["activation"] = {"default": activation_path}
        
        # Passage satisfaisant (son cristallin)
        passage_path = os.path.join(self.sounds_dir, "satisfying_passage.wav")
        if not os.path.exists(passage_path):
            try:
                duration = 0.6
                sample_rate = self.sample_rate
                t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
                
                # Son cristallin avec harmoniques
                freq = 1000
                signal = 0.5 * np.sin(2 * np.pi * freq * t)
                signal += 0.3 * np.sin(2 * np.pi * freq * 2 * t)  # Octave
                signal += 0.2 * np.sin(2 * np.pi * freq * 3 * t)  # Quinte
                
                # Enveloppe rapide mais douce
                env = np.exp(-t * 8) * np.sin(np.pi * t / duration)
                signal *= env
                
                # Ajouter réverb
                signal = self._add_artificial_reverb(signal, sample_rate)
                
                # Normaliser
                signal = signal / np.max(np.abs(signal)) * 0.8
                
                stereo_signal = np.column_stack((signal, signal))
                sf.write(passage_path, stereo_signal, sample_rate)
                
                self.effect_sounds["passage"] = {"default": passage_path}
                
            except Exception as e:
                logger.error(f"Erreur génération passage satisfaisant: {e}")
        else:
            self.effect_sounds["passage"] = {"default": passage_path}
    
    def _get_sound_path(self, event: AudioEvent) -> Optional[str]:
        """Récupère le chemin du fichier son pour un événement"""
        event_type = event.event_type
        params = event.params or {}
        
        if event_type == "note":
            note_idx = params.get("note", 0) % len(self.satisfying_scales[self.current_scale])
            octave = params.get("octave", 1)
            return os.path.join(self.sounds_dir, f"satisfying_note_{note_idx}_oct{octave}.wav")
            
        elif event_type == "explosion":
            size = params.get("size", "medium")
            if "explosion" in self.effect_sounds and size in self.effect_sounds["explosion"]:
                return self.effect_sounds["explosion"][size]
                
        elif event_type == "activation":
            if "activation" in self.effect_sounds:
                return self.effect_sounds["activation"]["default"]
                
        elif event_type == "passage":
            if "passage" in self.effect_sounds:
                return self.effect_sounds["passage"]["default"]
        
        return None
    
    def _add_melody_from_background_music(self) -> None:
        """NOUVEAU: Ajoute UNIQUEMENT la mélodie principale depuis la musique de fond"""
        if not self.background_music or not os.path.exists(self.background_music):
            return
        
        try:
            if self.background_music.endswith('.mid') or self.background_music.endswith('.midi'):
                # Extraire la mélodie pure du MIDI
                melody_notes = self._extract_pure_melody_with_timing(self.background_music)
                
                # Créer des événements mélodiques
                melody_events = []
                for note_data in melody_notes:
                    if note_data['time'] <= self.duration:
                        # Utiliser la gamme satisfaisante
                        note_idx = note_data['scale_index']
                        octave = 1 if note_data['midi_note'] >= 72 else 0
                        
                        event = AudioEvent(
                            event_type="note",
                            time=note_data['time'],
                            position=None,
                            params={"note": note_idx, "octave": octave}
                        )
                        melody_events.append(event)
                
                self.events.extend(melody_events)
                logger.info(f"{len(melody_events)} notes de mélodie pure extraites")
            
        except Exception as e:
            logger.error(f"Erreur extraction mélodie: {e}")
    
    def _extract_pure_melody_with_timing(self, midi_path: str) -> List[Dict]:
        """Extrait la mélodie avec timing précis"""
        try:
            mid = mido.MidiFile(midi_path)
            
            # Analyser toutes les pistes
            all_notes = []
            for track in mid.tracks:
                current_time = 0
                for msg in track:
                    if hasattr(msg, 'time'):
                        current_time += mido.tick2second(msg.time, mid.ticks_per_beat, 500000)
                    
                    if (msg.type == 'note_on' and msg.velocity > 0 and 
                        hasattr(msg, 'channel') and msg.channel != 9 and  # Pas de batterie
                        msg.note >= 60):  # Main droite seulement
                        
                        all_notes.append({
                            'time': current_time,
                            'midi_note': msg.note,
                            'velocity': msg.velocity
                        })
            
            # Trier par temps et extraire la ligne supérieure
            all_notes.sort(key=lambda x: x['time'])
            
            # Grouper par tranches de temps et prendre la note la plus aiguë
            melody_line = []
            time_resolution = 0.1  # 100ms de résolution
            current_time_slot = 0
            highest_in_slot = None
            
            for note in all_notes:
                time_slot = int(note['time'] / time_resolution)
                
                if time_slot != current_time_slot:
                    # Nouvelle tranche de temps
                    if highest_in_slot:
                        # Convertir en gamme satisfaisante
                        scale_index = self._midi_to_scale_index(highest_in_slot['midi_note'])
                        melody_line.append({
                            'time': highest_in_slot['time'],
                            'midi_note': highest_in_slot['midi_note'],
                            'scale_index': scale_index
                        })
                    
                    current_time_slot = time_slot
                    highest_in_slot = note
                else:
                    # Même tranche, garder la note la plus aiguë
                    if not highest_in_slot or note['midi_note'] > highest_in_slot['midi_note']:
                        highest_in_slot = note
            
            # Ajouter la dernière note
            if highest_in_slot:
                scale_index = self._midi_to_scale_index(highest_in_slot['midi_note'])
                melody_line.append({
                    'time': highest_in_slot['time'],
                    'midi_note': highest_in_slot['midi_note'],
                    'scale_index': scale_index
                })
            
            return melody_line[:32]  # Limiter pour performance
            
        except Exception as e:
            logger.error(f"Erreur extraction mélodie avec timing: {e}")
            return []
    
    def _midi_to_scale_index(self, midi_note: int) -> int:
        """Convertit une note MIDI en index de gamme satisfaisante"""
        scale = self.satisfying_scales[self.current_scale]
        pitch_class = midi_note % 12
        
        # Trouver la note la plus proche dans la gamme
        closest = min(scale, key=lambda x: abs(x - pitch_class))
        return scale.index(closest)
    
    def generate(self) -> Optional[str]:
        """Génère la piste audio finale avec sons satisfaisants"""
        try:
            # Choisir une gamme satisfaisante aléatoire
            self.current_scale = random.choice(list(self.satisfying_scales.keys()))
            logger.info(f"Utilisation de la gamme {self.current_scale} pour des sons satisfaisants")
            
            # Générer les sons satisfaisants
            self._generate_basic_sounds()
            
            # Ajouter la mélodie pure depuis la musique de fond
            if self.background_music:
                self._add_melody_from_background_music()
            
            logger.info(f"Génération audio satisfaisante à partir de {len(self.events)} événements...")
            
            # Si pas d'événements, créer une mélodie douce aléatoire
            if not self.events:
                self._create_random_satisfying_melody()
            
            # Créer la timeline audio
            timeline = np.zeros((int(self.sample_rate * self.duration), 2), dtype=np.float32)
            
            # Traiter les événements
            events_processed = 0
            for event in self.events:
                if event.time >= self.duration:
                    continue
                
                sound_path = self._get_sound_path(event)
                if not sound_path or not os.path.exists(sound_path):
                    continue
                
                try:
                    data, sr = sf.read(sound_path)
                    
                    if data.ndim == 1:
                        data = np.column_stack((data, data))
                    
                    start_idx = int(event.time * self.sample_rate)
                    end_idx = min(start_idx + len(data), len(timeline))
                    data_len = end_idx - start_idx
                    
                    # Volume selon le type
                    volume = self.note_volume
                    if event.event_type == "explosion":
                        volume = self.explosion_volume
                    elif event.event_type == "activation":
                        volume = self.activation_volume
                    elif event.event_type == "passage":
                        volume = self.passage_volume
                    
                    timeline[start_idx:end_idx] += data[:data_len] * volume
                    events_processed += 1
                    
                except Exception as e:
                    logger.error(f"Erreur traitement événement {event.event_type}: {e}")
            
            # Normalisation douce
            max_val = np.max(np.abs(timeline))
            if max_val > 0:
                timeline = timeline / max_val * 0.9  # Plus de headroom
            
            # Conversion finale
            audio_data = (timeline * 32767).astype(np.int16)
            wavfile.write(self.output_path, self.sample_rate, audio_data)
            
            logger.info(f"Audio satisfaisant généré: {self.output_path} ({events_processed} événements)")
            return self.output_path
            
        except Exception as e:
            logger.error(f"Erreur génération audio satisfaisant: {e}")
            return None
    
    def _create_random_satisfying_melody(self) -> None:
        """Crée une mélodie aléatoire satisfaisante"""
        scale = self.satisfying_scales[self.current_scale]
        melody_events = []
        
        # Paramètres de la mélodie
        note_duration = 0.8
        num_notes = min(16, int(self.duration / note_duration))
        
        for i in range(num_notes):
            time_pos = i * note_duration
            
            # Choisir une note de la gamme avec une logique mélodique
            if i == 0:
                note_idx = 0  # Commencer par la tonique
            else:
                # Mouvement mélodique naturel
                prev_note = melody_events[-1].params['note']
                possible_notes = []
                
                # Favoriser les mouvements par degrés conjoints
                for j, _ in enumerate(scale):
                    interval = abs(j - prev_note)
                    if interval <= 2:  # Mouvement conjoint
                        possible_notes.extend([j] * 3)  # Plus de chance
                    elif interval <= 4:  # Saut modéré
                        possible_notes.append(j)
                
                note_idx = random.choice(possible_notes) if possible_notes else random.randint(0, len(scale)-1)
            
            # Octave plus aiguë pour les notes importantes
            octave = 1 if i % 4 == 0 else 0
            
            event = AudioEvent(
                event_type="note",
                time=time_pos,
                position=None,
                params={"note": note_idx, "octave": octave}
            )
            melody_events.append(event)
        
        self.events.extend(melody_events)
        logger.info(f"Mélodie satisfaisante aléatoire créée: {len(melody_events)} notes")