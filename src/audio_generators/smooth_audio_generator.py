#!/usr/bin/env python3
"""
🎵 GÉNÉRATEUR AUDIO AGRÉABLE 🎵
Créé des sons doux et mélodieux pour TikTok (fini les sons qui font mal aux oreilles!)

Features:
- Mélodies harmoniques inspirées de la musique actuelle
- Sons doux avec filtres professionnels
- Progressions d'accords modernes
- Instruments virtuels réalistes
- EQ et compression pour un son pro
- Enveloppes douces (pas de clics/pops)
"""

import numpy as np
import math
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
import wave
import struct

logger = logging.getLogger("TikSimPro")

from src.audio_generators.base_audio_generator import IAudioGenerator
from src.core.data_pipeline import TrendData, AudioEvent

class SmoothAudioGenerator(IAudioGenerator):
    """🎵 GÉNÉRATEUR AUDIO DOUX ET AGRÉABLE 🎵"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.output_path = "output/smooth_audio.wav"
        self.duration = 30.0
        
        # 🎼 PARAMÈTRES MUSICAUX AGRÉABLES
        self.bpm = 120  # Tempo relaxant
        self.key = "C"  # Tonalité douce
        self.mode = "major"  # Mode majeur = plus joyeux
        
        # 🎪 PHASES AUDIO DOUCES (synchronisées avec vidéo)
        self.phases = {
            "hook": (0, 3),           # Intro mélodieuse
            "build": (3, 12),         # Développement harmonique
            "hypnotic": (12, 22),     # Partie relaxante
            "climax": (22, 27),       # Finale en beauté
            "outro": (27, 30),        # Conclusion douce
        }
        
        # 🎹 GAMMES ET ACCORDS AGRÉABLES
        # Gamme de Do majeur (notes qui sonnent toujours bien ensemble)
        self.major_scale = {
            "C": 261.63, "D": 293.66, "E": 329.63, "F": 349.23,
            "G": 392.00, "A": 440.00, "B": 493.88, "C2": 523.25
        }
        
        # Progressions d'accords populaires (vi-IV-I-V = Am-F-C-G)
        self.chord_progressions = {
            "pop": ["Am", "F", "C", "G"],          # Progression ultra-populaire
            "chill": ["C", "Am", "F", "G"],        # Calme et relaxant
            "upbeat": ["C", "G", "Am", "F"],       # Énergique mais doux
            "dreamy": ["Am", "C", "F", "G"]        # Rêveur
        }
        
        # 🎼 DÉFINITION DES ACCORDS
        self.chords = {
            "C": [261.63, 329.63, 392.00],    # Do majeur (C-E-G)
            "Am": [220.00, 261.63, 329.63],   # La mineur (A-C-E)
            "F": [174.61, 220.00, 261.63],    # Fa majeur (F-A-C)
            "G": [196.00, 246.94, 293.66],    # Sol majeur (G-B-D)
            "Dm": [146.83, 174.61, 220.00],   # Ré mineur (D-F-A)
            "Em": [164.81, 196.00, 246.94]    # Mi mineur (E-G-B)
        }
        
        # 🔊 VOLUMES ÉQUILIBRÉS
        self.volumes = {
            "master": 0.6,      # Volume général modéré
            "melody": 0.4,      # Mélodie douce
            "harmony": 0.3,     # Harmonies en arrière-plan
            "bass": 0.5,        # Basse présente mais pas agressive
            "percussion": 0.2,  # Percussion très douce
            "effects": 0.1      # Effets subtils
        }
        
        # État audio
        self.audio_data = []
        self.events = []
        self.trend_data = None
        
        # Cache pour sons doux
        self.instrument_cache = {}
        self.precompute_smooth_sounds()
        
        logger.info(f"🎵 Générateur Audio Doux initialisé: {self.bpm} BPM")

    def precompute_smooth_sounds(self):
        """Pré-calcule des sons doux et agréables"""
        logger.info("🎵 Pré-calcul des instruments doux...")
        
        # 🎹 PIANO VIRTUEL DOUX
        for note_name, freq in self.major_scale.items():
            self.instrument_cache[f"piano_{note_name}"] = self._create_soft_piano(freq, 2.0)
            self.instrument_cache[f"pad_{note_name}"] = self._create_soft_pad(freq, 3.0)
            self.instrument_cache[f"bell_{note_name}"] = self._create_bell(freq, 1.5)
        
        # 🥁 PERCUSSION DOUCE
        self.instrument_cache["soft_kick"] = self._create_soft_kick()
        self.instrument_cache["soft_snare"] = self._create_soft_snare()
        self.instrument_cache["soft_hihat"] = self._create_soft_hihat()
        self.instrument_cache["chime"] = self._create_chime()
        
        logger.debug(f"Cache instruments: {len(self.instrument_cache)} sons doux")

    def _create_soft_piano(self, frequency: float, duration: float) -> np.ndarray:
        """Crée un son de piano virtuel doux"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Harmoniques de piano (plus doux)
        fundamental = np.sin(2 * np.pi * frequency * t)
        harmonic2 = 0.3 * np.sin(2 * np.pi * frequency * 2 * t)
        harmonic3 = 0.1 * np.sin(2 * np.pi * frequency * 3 * t)
        harmonic4 = 0.05 * np.sin(2 * np.pi * frequency * 4 * t)
        
        piano = fundamental + harmonic2 + harmonic3 + harmonic4
        
        # Enveloppe ADSR douce (piano)
        envelope = self._soft_piano_envelope(samples)
        
        # Filtre passe-bas pour adoucir
        piano = self._low_pass_filter(piano * envelope, 3000)
        
        return piano * 0.6  # Volume modéré

    def _create_soft_pad(self, frequency: float, duration: float) -> np.ndarray:
        """Crée un pad synthé doux (ambiance)"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Ondes multiples légèrement désaccordées pour richesse
        wave1 = np.sin(2 * np.pi * frequency * t)
        wave2 = np.sin(2 * np.pi * (frequency * 1.005) * t)  # +0.5% détune
        wave3 = np.sin(2 * np.pi * (frequency * 0.995) * t)  # -0.5% détune
        
        pad = (wave1 + wave2 + wave3) / 3
        
        # Modulation douce (vibrato)
        lfo = 1 + 0.02 * np.sin(2 * np.pi * 4 * t)  # LFO 4Hz, profondeur 2%
        pad *= lfo
        
        # Enveloppe très douce (montée/descente lentes)
        envelope = self._soft_pad_envelope(samples)
        
        # Filtre pour enlever les hautes fréquences agressives
        pad = self._low_pass_filter(pad * envelope, 2000)
        
        return pad * 0.3  # Volume ambiance

    def _create_bell(self, frequency: float, duration: float) -> np.ndarray:
        """Crée un son de cloche/chime doux"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Fréquences de cloche (harmoniques non-entières)
        bell = (np.sin(2 * np.pi * frequency * t) +
                0.6 * np.sin(2 * np.pi * frequency * 2.4 * t) +
                0.3 * np.sin(2 * np.pi * frequency * 3.8 * t) +
                0.1 * np.sin(2 * np.pi * frequency * 5.2 * t))
        
        # Enveloppe de cloche (attaque rapide, déclin lent)
        envelope = np.exp(-t * 2)  # Décroissance exponentielle
        
        return bell * envelope * 0.4

    def _create_soft_kick(self) -> np.ndarray:
        """Kick doux (pas agressif)"""
        duration = 0.8
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Fréquence qui descend (effet kick)
        freq_envelope = 80 * np.exp(-t * 8)  # 80Hz -> 20Hz
        kick = np.sin(2 * np.pi * freq_envelope * t)
        
        # Enveloppe douce
        envelope = np.exp(-t * 6)
        
        return kick * envelope * 0.6

    def _create_soft_snare(self) -> np.ndarray:
        """Snare doux (bruit filtré)"""
        duration = 0.3
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Bruit blanc filtré
        noise = np.random.normal(0, 0.3, samples)
        
        # Composante tonale douce
        tone = 0.4 * np.sin(2 * np.pi * 200 * t)
        
        snare = noise + tone
        
        # Enveloppe rapide
        envelope = np.exp(-t * 15)
        
        # Filtre pour adoucir
        snare = self._low_pass_filter(snare * envelope, 4000)
        
        return snare * 0.3

    def _create_soft_hihat(self) -> np.ndarray:
        """Hi-hat très doux"""
        duration = 0.1
        samples = int(self.sample_rate * duration)
        
        # Bruit blanc très filtré
        noise = np.random.normal(0, 0.1, samples)
        
        # Filtre passe-haut puis passe-bas pour "chh"
        hihat = self._high_pass_filter(noise, 8000)
        hihat = self._low_pass_filter(hihat, 12000)
        
        # Enveloppe très rapide
        envelope = np.exp(-np.linspace(0, 20, samples))
        
        return hihat * envelope * 0.2

    def _create_chime(self) -> np.ndarray:
        """Chime magique pour transitions"""
        duration = 2.0
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Accord de Do majeur en chimes
        chime = (np.sin(2 * np.pi * 523.25 * t) +    # C5
                0.8 * np.sin(2 * np.pi * 659.25 * t) + # E5
                0.6 * np.sin(2 * np.pi * 783.99 * t))   # G5
        
        # Enveloppe de chime
        envelope = np.exp(-t * 1.5)
        
        return chime * envelope * 0.3

    def _soft_piano_envelope(self, samples: int) -> np.ndarray:
        """Enveloppe ADSR pour piano doux"""
        envelope = np.ones(samples)
        
        # Attack (10% du son)
        attack_samples = int(samples * 0.1)
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Decay (20% du son)
        decay_samples = int(samples * 0.2)
        if decay_samples > 0:
            decay_start = attack_samples
            decay_end = attack_samples + decay_samples
            envelope[decay_start:decay_end] = np.linspace(1, 0.7, decay_samples)
        
        # Sustain (50% du son à 70%)
        sustain_start = attack_samples + decay_samples
        sustain_end = int(samples * 0.8)
        envelope[sustain_start:sustain_end] = 0.7
        
        # Release (20% du son)
        release_start = sustain_end
        envelope[release_start:] = np.linspace(0.7, 0, samples - release_start)
        
        return envelope

    def _soft_pad_envelope(self, samples: int) -> np.ndarray:
        """Enveloppe très douce pour pads"""
        envelope = np.ones(samples)
        
        # Montée très douce (30%)
        attack_samples = int(samples * 0.3)
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Sustain (40%)
        sustain_end = int(samples * 0.7)
        envelope[attack_samples:sustain_end] = 1.0
        
        # Descente très douce (30%)
        release_start = sustain_end
        envelope[release_start:] = np.linspace(1, 0, samples - release_start)
        
        return envelope

    def _low_pass_filter(self, signal: np.ndarray, cutoff: float) -> np.ndarray:
        """Filtre passe-bas simple pour adoucir le son"""
        # Filtre simple RC
        rc = 1.0 / (cutoff * 2 * math.pi)
        dt = 1.0 / self.sample_rate
        alpha = dt / (rc + dt)
        
        filtered = np.zeros_like(signal)
        filtered[0] = signal[0]
        
        for i in range(1, len(signal)):
            filtered[i] = alpha * signal[i] + (1 - alpha) * filtered[i-1]
        
        return filtered

    def _high_pass_filter(self, signal: np.ndarray, cutoff: float) -> np.ndarray:
        """Filtre passe-haut simple"""
        rc = 1.0 / (cutoff * 2 * math.pi)
        dt = 1.0 / self.sample_rate
        alpha = rc / (rc + dt)
        
        filtered = np.zeros_like(signal)
        filtered[0] = signal[0]
        
        for i in range(1, len(signal)):
            filtered[i] = alpha * (filtered[i-1] + signal[i] - signal[i-1])
        
        return filtered

    def configure(self, config: Dict[str, Any]) -> bool:
        """Configuration audio douce"""
        try:
            self.bpm = config.get("bpm", 120)
            self.volumes["master"] = config.get("master_volume", 0.6)
            self.volumes["melody"] = config.get("melody_volume", 0.4)
            self.volumes["harmony"] = config.get("harmony_volume", 0.3)
            self.volumes["bass"] = config.get("bass_volume", 0.5)
            
            # Style musical
            self.style = config.get("style", "chill")  # chill, pop, upbeat, dreamy
            
            logger.info(f"🎵 Audio doux configuré: {self.bpm} BPM, style {self.style}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur config audio: {e}")
            return False

    def set_output_path(self, path: str) -> None:
        """Définit le chemin de sortie"""
        self.output_path = path

    def set_duration(self, duration: float) -> None:
        """Définit la durée"""
        self.duration = duration
        
        # Ajuster les phases
        ratio = duration / 30.0
        self.phases = {
            "hook": (0, 3 * ratio),
            "build": (3 * ratio, 12 * ratio), 
            "hypnotic": (12 * ratio, 22 * ratio),
            "climax": (22 * ratio, 27 * ratio),
            "outro": (27 * ratio, duration),
        }

    def apply_trend_data(self, trend_data: TrendData) -> None:
        """Applique les données de tendance audio"""
        self.trend_data = trend_data
        
        try:
            if trend_data and hasattr(trend_data, 'recommended_settings'):
                audio_settings = trend_data.recommended_settings.get('audio', {})
                if audio_settings:
                    if 'bpm' in audio_settings:
                        self.bpm = max(80, min(140, audio_settings['bpm']))  # Limite raisonnable
                    if 'style' in audio_settings:
                        self.style = audio_settings['style']
                    
                    logger.info(f"🎵 Tendances audio douces appliquées")
        except Exception as e:
            logger.error(f"Erreur tendances audio: {e}")

    def add_events(self, events: List[AudioEvent]) -> None:
        """Ajoute des événements audio"""
        self.events.extend(events)
        logger.info(f"🎵 {len(events)} événements audio ajoutés")

    def generate(self) -> Optional[str]:
        """🎵 GÉNÉRATION AUDIO DOUCE ET AGRÉABLE 🎵"""
        try:
            logger.info("🎵 Génération audio douce...")
            
            # Initialiser le buffer audio
            total_samples = int(self.sample_rate * self.duration)
            self.audio_data = np.zeros(total_samples, dtype=np.float32)
            
            # Générer par phases avec mélodies agréables
            self._generate_melodic_hook()
            self._generate_harmonic_build()
            self._generate_relaxing_hypnotic()
            self._generate_beautiful_climax()
            self._generate_gentle_outro()
            
            # Ajouter les événements synchronisés (version douce)
            self._add_gentle_synchronized_events()
            
            # Post-processing professionnel
            self._apply_professional_processing()
            
            # Sauvegarder
            self._save_to_wav()
            
            logger.info(f"🎵 Audio doux généré: {self.output_path}")
            return self.output_path
            
        except Exception as e:
            logger.error(f"Erreur génération audio: {e}")
            return None

    def _generate_melodic_hook(self):
        """Génère une mélodie accrocheuse mais douce pour le hook"""
        start_time, end_time = self.phases["hook"]
        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)
        
        # Mélodie simple et mémorable: C-E-G-C (arpège Do majeur)
        melody_notes = ["C", "E", "G", "C2"]
        note_duration = (end_time - start_time) / len(melody_notes)
        
        for i, note in enumerate(melody_notes):
            note_start = start_sample + int(i * note_duration * self.sample_rate)
            note_samples = int(note_duration * self.sample_rate)
            
            if f"piano_{note}" in self.instrument_cache:
                piano_sound = self.instrument_cache[f"piano_{note}"][:note_samples]
                end_pos = min(note_start + len(piano_sound), len(self.audio_data))
                self.audio_data[note_start:end_pos] += piano_sound[:end_pos - note_start] * self.volumes["melody"]
        
        # Pad doux en arrière-plan
        if "pad_C" in self.instrument_cache:
            pad_sound = self.instrument_cache["pad_C"]
            pad_samples = min(len(pad_sound), end_sample - start_sample)
            self.audio_data[start_sample:start_sample + pad_samples] += pad_sound[:pad_samples] * self.volumes["harmony"]

    def _generate_harmonic_build(self):
        """Build avec progression d'accords douce"""
        start_time, end_time = self.phases["build"]
        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)
        
        # Progression d'accords selon le style
        progression = self.chord_progressions.get(self.style, self.chord_progressions["chill"])
        chord_duration = (end_time - start_time) / len(progression)
        
        for i, chord_name in enumerate(progression):
            chord_start = start_sample + int(i * chord_duration * self.sample_rate)
            chord_samples = int(chord_duration * self.sample_rate)
            
            # Jouer l'accord avec des sons de pad
            if chord_name in self.chords:
                for note_freq in self.chords[chord_name]:
                    # Trouver la note la plus proche dans le cache
                    closest_note = self._find_closest_cached_note(note_freq)
                    if closest_note and f"pad_{closest_note}" in self.instrument_cache:
                        pad_sound = self.instrument_cache[f"pad_{closest_note}"][:chord_samples]
                        end_pos = min(chord_start + len(pad_sound), len(self.audio_data))
                        self.audio_data[chord_start:end_pos] += pad_sound[:end_pos - chord_start] * self.volumes["harmony"] * 0.3
        
        # Mélodie par-dessus
        self._add_simple_melody(start_sample, end_sample, progression)

    def _generate_relaxing_hypnotic(self):
        """Phase hypnotique relaxante"""
        start_time, end_time = self.phases["hypnotic"]
        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)
        
        # Boucle d'accord simple et relaxante
        chord_progression = ["C", "Am", "F", "G"]  # Très relaxant
        loop_duration = 4.0  # 4 secondes par boucle
        
        current_time = start_time
        while current_time < end_time:
            for chord_name in chord_progression:
                chord_start = int(current_time * self.sample_rate)
                chord_samples = int(1.0 * self.sample_rate)  # 1 seconde par accord
                
                if chord_start >= end_sample:
                    break
                
                # Pad doux pour l'accord
                if chord_name in self.chords:
                    for j, note_freq in enumerate(self.chords[chord_name]):
                        closest_note = self._find_closest_cached_note(note_freq)
                        if closest_note and f"pad_{closest_note}" in self.instrument_cache:
                            pad_sound = self.instrument_cache[f"pad_{closest_note}"][:chord_samples]
                            end_pos = min(chord_start + len(pad_sound), len(self.audio_data))
                            self.audio_data[chord_start:end_pos] += pad_sound[:end_pos - chord_start] * self.volumes["harmony"] * 0.4
                
                current_time += 1.0
            
            if current_time >= end_time:
                break

    def _generate_beautiful_climax(self):
        """Climax beau et émotionnel (pas agressif)"""
        start_time, end_time = self.phases["climax"]
        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)
        
        # Accord de Do majeur complet avec toutes les harmoniques
        climax_chord = self.chords["C"]
        
        for note_freq in climax_chord:
            closest_note = self._find_closest_cached_note(note_freq)
            if closest_note:
                # Piano pour la mélodie principale
                if f"piano_{closest_note}" in self.instrument_cache:
                    piano_sound = self.instrument_cache[f"piano_{closest_note}"]
                    piano_samples = min(len(piano_sound), end_sample - start_sample)
                    self.audio_data[start_sample:start_sample + piano_samples] += piano_sound[:piano_samples] * self.volumes["melody"] * 0.8
                
                # Pad pour l'ambiance
                if f"pad_{closest_note}" in self.instrument_cache:
                    pad_sound = self.instrument_cache[f"pad_{closest_note}"]
                    pad_samples = min(len(pad_sound), end_sample - start_sample)
                    self.audio_data[start_sample:start_sample + pad_samples] += pad_sound[:pad_samples] * self.volumes["harmony"] * 0.6
        
        # Chimes magiques pour la beauté
        if "chime" in self.instrument_cache:
            chime_sound = self.instrument_cache["chime"]
            chime_samples = min(len(chime_sound), end_sample - start_sample)
            self.audio_data[start_sample:start_sample + chime_samples] += chime_sound[:chime_samples] * 0.4

    def _generate_gentle_outro(self):
        """Outro doux et conclusif"""
        start_time, end_time = self.phases["outro"]
        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)
        
        # Mélodie descendante douce: C-G-F-C
        outro_notes = ["C2", "G", "F", "C"]
        note_duration = (end_time - start_time) / len(outro_notes)
        
        for i, note in enumerate(outro_notes):
            note_start = start_sample + int(i * note_duration * self.sample_rate)
            note_samples = int(note_duration * self.sample_rate)
            
            # Intensité décroissante
            fade_factor = 1.0 - (i / len(outro_notes)) * 0.5
            
            if f"bell_{note}" in self.instrument_cache:
                bell_sound = self.instrument_cache[f"bell_{note}"][:note_samples]
                end_pos = min(note_start + len(bell_sound), len(self.audio_data))
                self.audio_data[note_start:end_pos] += bell_sound[:end_pos - note_start] * self.volumes["melody"] * fade_factor

    def _find_closest_cached_note(self, frequency: float) -> Optional[str]:
        """Trouve la note en cache la plus proche d'une fréquence"""
        closest_note = None
        min_diff = float('inf')
        
        for note_name, note_freq in self.major_scale.items():
            diff = abs(frequency - note_freq)
            if diff < min_diff:
                min_diff = diff
                closest_note = note_name
        
        return closest_note

    def _add_simple_melody(self, start_sample: int, end_sample: int, chord_progression: List[str]):
        """Ajoute une mélodie simple par-dessus les accords"""
        try:
            # Mélodie simple basée sur les accords
            melody_notes = []
            for chord in chord_progression:
                if chord == "C":
                    melody_notes.extend(["C", "E"])
                elif chord == "Am":
                    melody_notes.extend(["A", "C"])
                elif chord == "F":
                    melody_notes.extend(["F", "A"])
                elif chord == "G":
                    melody_notes.extend(["G", "B"])
            
            note_duration = (end_sample - start_sample) / (len(melody_notes) * self.sample_rate)
            
            for i, note in enumerate(melody_notes):
                if note in self.major_scale:
                    note_start = start_sample + int(i * note_duration * self.sample_rate)
                    note_samples = int(note_duration * self.sample_rate)
                    
                    closest_note = self._find_closest_cached_note(self.major_scale[note])
                    if closest_note and f"bell_{closest_note}" in self.instrument_cache:
                        bell_sound = self.instrument_cache[f"bell_{closest_note}"][:note_samples]
                        end_pos = min(note_start + len(bell_sound), len(self.audio_data))
                        self.audio_data[note_start:end_pos] += bell_sound[:end_pos - note_start] * 0.2
        except Exception as e:
            logger.debug(f"Erreur mélodie simple: {e}")

    def _add_gentle_synchronized_events(self):
        """Ajoute des événements doux synchronisés"""
        for event in self.events:
            try:
                event_sample = int(event.time * self.sample_rate)
                
                if event.event_type == "countdown_beep":
                    self._add_gentle_chime(event_sample, event.params.get("volume", 0.3))
                
                elif event.event_type == "build_pulse":
                    self._add_soft_pulse(event_sample, event.params.get("volume", 0.2))
                
                elif event.event_type == "hypnotic_tone":
                    self._add_peaceful_tone(event_sample, event.params.get("volume", 0.2))
                
                elif event.event_type == "climax_hit":
                    self._add_beautiful_accent(event_sample, event.params.get("volume", 0.4))
                
                elif event.event_type == "explosion_particle":
                    self._add_sparkle_sound(event_sample, event.params.get("volume", 0.1))
                
            except Exception as e:
                logger.warning(f"Erreur événement audio doux: {e}")

    def _add_gentle_chime(self, start_sample: int, volume: float):
        """Ajoute un chime doux"""
        if "chime" in self.instrument_cache:
            chime = self.instrument_cache["chime"] * volume
            end_sample = min(start_sample + len(chime), len(self.audio_data))
            self.audio_data[start_sample:end_sample] += chime[:end_sample - start_sample]

    def _add_soft_pulse(self, start_sample: int, volume: float):
        """Ajoute un pulse doux"""
        if "soft_kick" in self.instrument_cache:
            pulse = self.instrument_cache["soft_kick"] * volume
            end_sample = min(start_sample + len(pulse), len(self.audio_data))
            self.audio_data[start_sample:end_sample] += pulse[:end_sample - start_sample]

    def _add_peaceful_tone(self, start_sample: int, volume: float):
        """Ajoute un ton paisible"""
        if "pad_C" in self.instrument_cache:
            tone = self.instrument_cache["pad_C"][:int(0.5 * self.sample_rate)] * volume * 0.5
            end_sample = min(start_sample + len(tone), len(self.audio_data))
            self.audio_data[start_sample:end_sample] += tone[:end_sample - start_sample]

    def _add_beautiful_accent(self, start_sample: int, volume: float):
        """Ajoute un accent beau"""
        if "bell_C" in self.instrument_cache:
            accent = self.instrument_cache["bell_C"] * volume
            end_sample = min(start_sample + len(accent), len(self.audio_data))
            self.audio_data[start_sample:end_sample] += accent[:end_sample - start_sample]

    def _add_sparkle_sound(self, start_sample: int, volume: float):
        """Ajoute un son de sparkle doux"""
        if "bell_E" in self.instrument_cache:
            sparkle = self.instrument_cache["bell_E"] * volume * 0.5
            end_sample = min(start_sample + len(sparkle), len(self.audio_data))
            self.audio_data[start_sample:end_sample] += sparkle[:end_sample - start_sample]

    def _apply_professional_processing(self):
        """Post-processing professionnel pour un son agréable"""
        # 1. Compression douce
        self._apply_gentle_compression()
        
        # 2. EQ pour enlever les fréquences désagréables
        self._apply_smooth_eq()
        
        # 3. Normalisation
        self._normalize_audio()
        
        # 4. Fade in/out
        self._apply_gentle_fades()

    def _apply_gentle_compression(self):
        """Compression très douce"""
        threshold = 0.7
        ratio = 2.0  # Compression légère
        
        compressed = np.where(
            np.abs(self.audio_data) > threshold,
            np.sign(self.audio_data) * (threshold + (np.abs(self.audio_data) - threshold) / ratio),
            self.audio_data
        )
        
        self.audio_data = compressed

    def _apply_smooth_eq(self):
        """EQ pour enlever les fréquences agressives"""
        # Filtre passe-bas pour enlever les hautes fréquences agressives
        self.audio_data = self._low_pass_filter(self.audio_data, 8000)
        
        # Filtre passe-haut pour enlever les très basses fréquences inutiles
        self.audio_data = self._high_pass_filter(self.audio_data, 40)

    def _normalize_audio(self):
        """Normalisation douce"""
        max_amplitude = np.max(np.abs(self.audio_data))
        if max_amplitude > 0:
            # Normaliser à 80% pour éviter la saturation
            self.audio_data = (self.audio_data / max_amplitude) * 0.8 * self.volumes["master"]

    def _apply_gentle_fades(self):
        """Fade in/out doux"""
        fade_samples = int(0.2 * self.sample_rate)  # 0.2s fade
        
        # Fade in
        if len(self.audio_data) > fade_samples:
            self.audio_data[:fade_samples] *= np.linspace(0, 1, fade_samples)
        
        # Fade out
        if len(self.audio_data) > fade_samples:
            self.audio_data[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    def _save_to_wav(self):
        """Sauvegarde en fichier WAV"""
        try:
            # Convertir en 16-bit integers
            audio_int16 = (self.audio_data * 32767).astype(np.int16)
            
            with wave.open(self.output_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            logger.info(f"🎵 Audio doux sauvegardé: {self.output_path}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde audio: {e}")
            raise


def main():
    """🎵 TEST DU GÉNÉRATEUR AUDIO DOUX 🎵"""
    print("🎵 SMOOTH AUDIO GENERATOR TEST 🎵")
    print("=" * 50)
    
    generator = SmoothAudioGenerator(sample_rate=44100)
    
    try:
        # Configuration douce
        config = {
            "bpm": 110,           # Tempo relaxant
            "style": "chill",     # Style paisible
            "master_volume": 0.6, # Volume modéré
            "melody_volume": 0.4, # Mélodie douce
            "harmony_volume": 0.3 # Harmonies subtiles
        }
        
        generator.configure(config)
        generator.set_duration(15.0)  # Test de 15s
        generator.set_output_path("output/smooth_audio_test.wav")
        
        print("🎵 Génération audio doux...")
        start_time = time.time()
        
        result = generator.generate()
        
        gen_time = time.time() - start_time
        
        if result:
            print(f"✅ Audio doux généré!")
            print(f"🎵 Fichier: {result}")
            print(f"⚡ Temps: {gen_time:.1f}s")
            print(f"🎼 Style: {config['style']}")
            print(f"🎯 BPM: {config['bpm']}")
            print(f"\n🎶 CARACTÉRISTIQUES:")
            print(f"   ✅ Sons doux et agréables")
            print(f"   ✅ Mélodies harmonieuses")
            print(f"   ✅ Pas de fréquences agressives")
            print(f"   ✅ Volume équilibré")
            print(f"   ✅ Progressions d'accords modernes")
            print(f"   ✅ Instruments virtuels réalistes")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")


if __name__ == "__main__":
    main()