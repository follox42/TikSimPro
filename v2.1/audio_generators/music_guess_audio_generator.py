#!/usr/bin/env python
# melody_guess_game_compare.py
"""
Jeu de devinettes musicales avec extraction mélodique améliorée,
génération de sons plus naturels et comparaison audio finale
"""

import os
import time
import logging
import numpy as np
import pygame
import requests
import json
import random
import threading
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import urllib.parse

# Bibliothèques pour l'analyse audio et la synthèse
try:
    import librosa
    import librosa.display
    import soundfile as sf
    from scipy import signal
    from scipy.signal import find_peaks, butter, filtfilt
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("Librosa non disponible, veuillez l'installer avec 'pip install librosa'")

# Essayer d'importer Vamp pour Melodia
try:
    import vamp
    VAMP_AVAILABLE = True
except ImportError:
    VAMP_AVAILABLE = False
    print("Vamp non disponible - l'extraction Melodia ne sera pas utilisée")

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MelodyGuessGame")

class MelodyGuessGame:
    """
    Jeu de devinettes musicales avec extraction mélodique améliorée
    et génération de sons plus naturels et agréables
    """
    
    # Sources musicales possibles (APIs ou listes prédéfinies)
    MUSIC_SOURCES = {
        "deezer": "https://api.deezer.com/chart/0/tracks?limit=50",
    }
    
    # Liste de secours si les APIs ne fonctionnent pas
    BACKUP_MUSIC_LIST = [
        {
            "title": "Shape of You",
            "artist": "Ed Sheeran",
            "preview_url": "https://cdns-preview-0.dzcdn.net/stream/c-0f7432517a94b98e2f9ff36cf97d8a0c-4.mp3"
        },
        {
            "title": "Dance Monkey",
            "artist": "Tones and I",
            "preview_url": "https://cdns-preview-1.dzcdn.net/stream/c-156e72d2ea8a6e13f8c354c1468a3bed-4.mp3"
        },
        {
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "preview_url": "https://cdns-preview-c.dzcdn.net/stream/c-cb72a3672d1b13f9658e0cd304ed48eb-4.mp3"
        },
        {
            "title": "Bad Guy",
            "artist": "Billie Eilish",
            "preview_url": "https://cdns-preview-0.dzcdn.net/stream/c-01091577a540ac82d47fec735ad5a365-5.mp3"
        },
        {
            "title": "Someone You Loved",
            "artist": "Lewis Capaldi",
            "preview_url": "https://cdns-preview-e.dzcdn.net/stream/c-e77d23e0c8ed7567a507a6d1b6a9ca1b-9.mp3"
        },
        {
            "title": "Happy",
            "artist": "Pharrell Williams",
            "preview_url": "https://cdns-preview-6.dzcdn.net/stream/c-674147ab16b4d609d65f618a7a0ae16a-7.mp3"
        },
        {
            "title": "Watermelon Sugar",
            "artist": "Harry Styles",
            "preview_url": "https://cdns-preview-3.dzcdn.net/stream/c-3e9eed8c99c58a5e1c963a9e2914aecf-4.mp3"
        },
        {
            "title": "Believer",
            "artist": "Imagine Dragons",
            "preview_url": "https://cdns-preview-3.dzcdn.net/stream/c-33d58d5f0d9919b3cf585fe6c944bc52-6.mp3"
        },
        {
            "title": "Perfect",
            "artist": "Ed Sheeran",
            "preview_url": "https://cdns-preview-c.dzcdn.net/stream/c-c38c627ca74c30e58b7064ed896ecf3c-6.mp3"
        }
    ]
    
    # Fréquences des notes musicales (Do3 à Si4)
    NOTE_FREQUENCIES = {
        "C3": 130.81, "C#3": 138.59, "D3": 146.83, "D#3": 155.56, "E3": 164.81, "F3": 174.61,
        "F#3": 185.00, "G3": 196.00, "G#3": 207.65, "A3": 220.00, "A#3": 233.08, "B3": 246.94,
        "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13, "E4": 329.63, "F4": 349.23,
        "F#4": 369.99, "G4": 392.00, "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,
        "C5": 523.25, "C#5": 554.37, "D5": 587.33, "D#5": 622.25, "E5": 659.26
    }
    
    # Types d'instruments pour les sons (simulation simple)
    INSTRUMENT_TYPES = ["piano", "guitar", "synth", "marimba", "bell"]
    
    def __init__(self, 
                 cache_dir: str = "melody_cache", 
                 api_keys: Optional[Dict[str, str]] = None,
                 difficulty: str = "medium",
                 instrument: Optional[str] = None):
        """
        Initialise le jeu de devinettes mélodiques amélioré
        
        Args:
            cache_dir: Répertoire pour stocker les musiques et mélodies
            api_keys: Clés API pour différentes sources de musique
            difficulty: Difficulté du jeu ("easy", "medium", "hard")
            instrument: Type d'instrument à utiliser pour jouer la mélodie
                       (si None, choisi aléatoirement)
        """
        # Vérifier si librosa est disponible
        if not LIBROSA_AVAILABLE:
            print("Librosa est requis pour extraire les mélodies. Installez-le avec 'pip install librosa'")
            print("Le programme va essayer de continuer avec des fonctionnalités limitées.")
        
        # Initialisation des attributs principaux
        self.cache_dir = cache_dir
        self.music_dir = os.path.join(cache_dir, "music")
        self.melody_dir = os.path.join(cache_dir, "melodies")
        self.instrument_dir = os.path.join(cache_dir, "instruments")
        self.api_keys = api_keys or {}
        self.difficulty = difficulty
        
        # Initialisation explicite de l'attribut instrument_sounds
        self.instrument_sounds = {}
        self._stop_playing = False
        
        # Choisir un instrument ou en sélectionner un aléatoirement
        self.instrument = instrument or random.choice(self.INSTRUMENT_TYPES)
        
        # Créer les répertoires de cache
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.music_dir, exist_ok=True)
        os.makedirs(self.melody_dir, exist_ok=True)
        os.makedirs(self.instrument_dir, exist_ok=True)
        
        # Liste des musiques disponibles
        self.music_list = []
        
        # Musique en cours
        self.current_music = None
        self.current_melody = []
        
        # Initialiser pygame pour l'audio
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            time.sleep(0.5)  # Donner le temps à pygame de s'initialiser
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de pygame: {e}")
            print(f"Erreur d'initialisation audio: {e}")
        
        # Réglages selon la difficulté
        self.melody_length = {
            "easy": 16,     # 16 notes pour une reconnaissance facile
            "medium": 12,   # 12 notes
            "hard": 8       # 8 notes pour rendre la reconnaissance difficile
        }.get(difficulty, 12)
        
        # Temps entre les notes en secondes
        self.note_duration = {
            "easy": 0.6,    # Plus lent pour plus de facilité
            "medium": 0.4,  # Vitesse moyenne
            "hard": 0.3     # Plus rapide pour augmenter la difficulté
        }.get(difficulty, 0.4)
        
        # Effets sonores à appliquer
        self.apply_reverb = True
        self.apply_chorus = difficulty != "hard"  # Pas de chorus en mode difficile pour plus de clarté
        
        # Taux de tempo variation pour rendre le jeu plus organique
        self.tempo_variation = {
            "easy": 0.1,    # Variation de tempo de 10% (plus régulier)
            "medium": 0.15, # Variation de tempo de 15%
            "hard": 0.05    # Variation de tempo de 5% (plus mécanique, mais difficile)
        }.get(difficulty, 0.15)
        
        # Générer des sons d'instruments
        try:
            self.instrument_sounds = self._generate_instrument_sounds()
        except Exception as e:
            logger.error(f"Erreur lors de la génération des sons d'instruments: {e}")
            print(f"Erreur de génération des sons: {e}")
            # Initialiser au moins comme un dictionnaire vide
            self.instrument_sounds = {}
        
        logger.info(f"MelodyGuessGame amélioré initialisé: difficulté {difficulty}, {self.melody_length} notes, instrument: {self.instrument}")
    
    def _generate_instrument_sounds(self) -> Dict[str, pygame.mixer.Sound]:
        """
        Génère des sons d'instruments plus naturels pour chaque note musicale
        
        Returns:
            Dictionnaire de sons pour chaque note
        """
        instrument_sounds = {}
        
        for note, freq in self.NOTE_FREQUENCIES.items():
            # Créer le chemin du fichier cache
            filepath = os.path.join(self.instrument_dir, f"{self.instrument}_{note}.wav")
            
            # Vérifier si le fichier existe déjà
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                try:
                    instrument_sounds[note] = pygame.mixer.Sound(filepath)
                    continue
                except Exception as e:
                    logger.warning(f"Erreur lors du chargement du son {note}: {e}")
                    # Si le chargement échoue, regénérer le son
            
            # Générer le son de l'instrument
            self._generate_instrument_sound(freq, note, filepath)
            
            # Charger le son généré
            try:
                instrument_sounds[note] = pygame.mixer.Sound(filepath)
            except Exception as e:
                logger.error(f"Erreur lors du chargement du son {note}: {e}")
        
        return instrument_sounds
    
    def _generate_instrument_sound(self, frequency: float, note: str, filepath: str) -> None:
        """
        Génère un son d'instrument plus naturel et agréable
        
        Args:
            frequency: Fréquence de la note en Hz
            note: Nom de la note
            filepath: Chemin du fichier à créer
        """
        try:
            # Paramètres audio
            sample_rate = 44100
            duration = 1.5  # Durée suffisante pour les effets sans être trop longue
            
            # Générer la forme d'onde selon l'instrument
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            
            # Forme d'onde de base
            if self.instrument == "piano":
                # Son de piano (mélange d'harmoniques et déclin exponentiel)
                signal_base = 0.7 * np.sin(2 * np.pi * frequency * t)
                signal_base += 0.2 * np.sin(2 * np.pi * frequency * 2 * t)
                signal_base += 0.1 * np.sin(2 * np.pi * frequency * 3 * t)
                
                # Déclin exponentiel pour simuler la mécanique du piano
                decay = np.exp(-t * 3)
                
            elif self.instrument == "guitar":
                # Son de guitare (plus d'harmoniques, déclin plus lent)
                signal_base = 0.6 * np.sin(2 * np.pi * frequency * t)
                signal_base += 0.3 * np.sin(2 * np.pi * frequency * 2 * t)
                signal_base += 0.2 * np.sin(2 * np.pi * frequency * 3 * t)
                
                # Déclin plus lent pour la guitare
                decay = np.exp(-t * 2)
                
            elif self.instrument == "synth":
                # Son de synthétiseur (onde carrée + sinusoïdale)
                # Onde carrée adoucie pour éviter les artefacts audio
                square = 0.2 * np.sign(np.sin(2 * np.pi * frequency * t))
                # Onde sinusoïdale
                sine = 0.3 * np.sin(2 * np.pi * frequency * t)
                signal_base = square + sine
                
                # Déclin plus lent pour le synthé
                decay = np.exp(-t * 1.5)
                
            elif self.instrument == "marimba":
                # Son de marimba (riche en harmoniques, déclin rapide)
                signal_base = 0.7 * np.sin(2 * np.pi * frequency * t)
                signal_base += 0.15 * np.sin(2 * np.pi * frequency * 3 * t)
                signal_base += 0.1 * np.sin(2 * np.pi * frequency * 6 * t)
                
                # Déclin très rapide pour le marimba
                decay = np.exp(-t * 5)
                
            elif self.instrument == "bell":
                # Son de cloche (inharmonique, longue résonance)
                signal_base = 0.6 * np.sin(2 * np.pi * frequency * t)
                signal_base += 0.3 * np.sin(2 * np.pi * frequency * 2.01 * t)  # Légèrement désaccordé
                
                # Déclin lent pour la cloche
                decay = np.exp(-t * 1)
                
            else:
                # Instrument par défaut (hybride)
                signal_base = 0.7 * np.sin(2 * np.pi * frequency * t)
                signal_base += 0.2 * np.sin(2 * np.pi * frequency * 2 * t)
                decay = np.exp(-t * 2)
            
            # Générer l'enveloppe ADSR (Attack, Decay, Sustain, Release)
            # Paramètres d'enveloppe simplifiés
            attack_samples = int(0.02 * sample_rate)
            decay_samples = int(0.1 * sample_rate)
            release_samples = int(0.3 * sample_rate)
            
            # Générer l'enveloppe
            envelope = np.ones_like(t)
            
            # Phase d'attaque
            if attack_samples > 0:
                envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
            
            # Phase de release
            if release_samples > 0 and len(t) > release_samples:
                envelope[-release_samples:] = np.linspace(1, 0, release_samples)
            
            # Multiplier par le decay naturel de l'instrument
            envelope = envelope * decay
            
            # Appliquer l'enveloppe
            audio_signal = signal_base * envelope
            
            # Ajouter une réverbération si demandé
            if self.apply_reverb:
                audio_signal = self._add_reverb(audio_signal, sample_rate)
            
            # Normaliser
            audio_signal = audio_signal / np.max(np.abs(audio_signal) + 1e-9) * 0.9
            
            # Convertir en stéréo
            stereo_signal = np.column_stack((audio_signal, audio_signal))
            
            # Sauvegarder en format WAV
            sf.write(filepath, stereo_signal, sample_rate)
            
            logger.info(f"Son d'instrument généré: {self.instrument}_{note}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du son {note}: {e}")
            
            # En cas d'échec, générer un son très basique
            try:
                # Paramètres audio
                sample_rate = 44100
                duration = 0.5
                t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
                simple_signal = 0.5 * np.sin(2 * np.pi * frequency * t)
                env = np.exp(-t * 3)
                simple_signal = simple_signal * env
                simple_signal = simple_signal / np.max(np.abs(simple_signal) + 1e-9) * 0.9
                stereo_signal = np.column_stack((simple_signal, simple_signal))
                sf.write(filepath, stereo_signal, sample_rate)
                logger.info(f"Son de secours généré pour {note}")
            except Exception as backup_err:
                logger.error(f"Échec également de la génération du son de secours: {backup_err}")
    
    def _add_reverb(self, signal, sample_rate):
        """
        Ajoute un effet de réverbération à un signal audio (version simplifiée)
        
        Args:
            signal: Signal audio à traiter
            sample_rate: Fréquence d'échantillonnage
            
        Returns:
            Signal avec réverbération
        """
        try:
            # Paramètres de réverbération
            reverb_time = 0.3  # Secondes (plus court pour éviter les problèmes)
            num_reflections = 3  # Moins de réflexions pour plus de stabilité
            max_delay = int(reverb_time * sample_rate)
            
            # Créer le signal avec réverbération
            reverb_signal = np.copy(signal)
            
            # Ajouter des réflexions avec délai et atténuation
            for i in range(1, num_reflections + 1):
                delay = int(max_delay * (i / num_reflections))
                attenuation = 0.3 * (1 - i / (num_reflections + 1))
                
                # Créer une version retardée du signal
                delayed = np.zeros_like(signal)
                if delay < len(signal):
                    delayed[delay:] = signal[:-delay]
                    
                    # Ajouter au signal de réverbération
                    reverb_signal += attenuation * delayed
            
            # Normaliser
            max_val = np.max(np.abs(reverb_signal))
            if max_val > 0:
                reverb_signal = reverb_signal / max_val * np.max(np.abs(signal))
            
            return reverb_signal
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de réverbération: {e}")
            return signal  # Retourner le signal original en cas d'erreur
    
    def fetch_music_list(self, source: Optional[str] = None) -> bool:
        """
        Récupère une liste de musiques depuis une source en ligne
        
        Args:
            source: Source de musique à utiliser (si None, essaie toutes les sources)
            
        Returns:
            True si la récupération a réussi, False sinon
        """
        # Réinitialiser la liste
        self.music_list = []
        
        # Si une source spécifique est demandée, essayer seulement celle-là
        if source and source in self.MUSIC_SOURCES:
            success = self._fetch_from_source(source)
            if success and len(self.music_list) > 0:
                return True
        else:
            # Sinon, essayer toutes les sources jusqu'à en trouver une qui fonctionne
            for src in self.MUSIC_SOURCES:
                success = self._fetch_from_source(src)
                if success and len(self.music_list) > 0:
                    return True
        
        # Si aucune source ne fonctionne, utiliser la liste de secours
        logger.warning("Aucune source en ligne disponible, utilisation de la liste de secours")
        self.music_list = self.BACKUP_MUSIC_LIST.copy()
        return len(self.music_list) > 0
    
    def _fetch_from_source(self, source: str) -> bool:
        """
        Récupère une liste de musiques depuis une source spécifique
        
        Args:
            source: Source de musique à utiliser
            
        Returns:
            True si la récupération a réussi, False sinon
        """
        try:
            url = self.MUSIC_SOURCES[source]
            
            # Remplacer les placeholders d'API key si nécessaire
            if "{api_key}" in url and source in self.api_keys:
                url = url.format(api_key=self.api_keys[source])
            
            # Requête HTTP
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Erreur lors de la récupération depuis {source}: {response.status_code}")
                return False
            
            # Parser la réponse selon la source
            if source == "deezer":
                data = response.json()
                tracks = data.get("data", [])
                
                for track in tracks:
                    if "preview" in track and track["preview"]:
                        self.music_list.append({
                            "title": track.get("title", "Unknown"),
                            "artist": track.get("artist", {}).get("name", "Unknown"),
                            "preview_url": track["preview"],
                            "source": "deezer"
                        })
            
            # Vérifier si des musiques ont été trouvées
            if not self.music_list:
                logger.warning(f"Aucune musique trouvée depuis {source}")
                return False
            
            logger.info(f"{len(self.music_list)} musiques récupérées depuis {source}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération depuis {source}: {e}")
            return False
    
    def download_music(self, music_info: Dict[str, Any]) -> Optional[str]:
        """
        Télécharge une musique et la sauvegarde dans le cache
        
        Args:
            music_info: Informations sur la musique à télécharger
            
        Returns:
            Chemin du fichier téléchargé, ou None en cas d'échec
        """
        try:
            url = music_info["preview_url"]
            
            # Créer un nom de fichier unique basé sur le titre et l'artiste
            safe_title = urllib.parse.quote(music_info["title"], safe='')
            safe_artist = urllib.parse.quote(music_info["artist"], safe='')
            filename = f"{safe_artist}_{safe_title}.mp3"
            filepath = os.path.join(self.music_dir, filename)
            
            # Vérifier si le fichier existe déjà dans le cache
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                logger.info(f"Utilisation du fichier en cache: {filepath}")
                return filepath
            
            # Télécharger le fichier
            logger.info(f"Téléchargement de {music_info['title']} par {music_info['artist']}...")
            response = requests.get(url, stream=True, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Erreur lors du téléchargement: {response.status_code}")
                return None
            
            # Sauvegarder le fichier
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Téléchargement terminé: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement: {e}")
            return None

    def extract_melody(self, filepath: str) -> List[str]:
        """
        Extrait la mélodie d'une musique en utilisant des algorithmes avancés
        
        Args:
            filepath: Chemin du fichier audio
            
        Returns:
            Liste des notes de la mélodie extraite
        """
        notes, _ = self.extract_melody_and_rhythm(filepath)
        return notes
    
    def _hz2midi(self, hz):
        """
        Convertit des fréquences en Hz en notes MIDI
        
        Args:
            hz: Tableau de fréquences en Hz
            
        Returns:
            Tableau de notes MIDI
        """
        # Convertir de Hz en notes MIDI
        hz_nonneg = hz.copy()
        idx = hz_nonneg <= 0
        hz_nonneg[idx] = 1
        midi = 69 + 12*np.log2(hz_nonneg/440.)
        midi[idx] = 0
        
        # Arrondir
        midi = np.round(midi)
        
        return midi

    def _midi_to_note(self, midi_number):
        """
        Convertit un numéro MIDI en nom de note
        
        Args:
            midi_number: Numéro de note MIDI
            
        Returns:
            Nom de la note (ex: "C4")
        """
        if midi_number <= 0:
            return None
            
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_number // 12) - 1
        note = notes[midi_number % 12]
        return f"{note}{octave}"
    
    def extract_melody_and_rhythm(self, filepath: str) -> Tuple[List[str], List[float]]:
        """
        Extrait la mélodie et le rythme d'un fichier audio en utilisant l'algorithme Melodia
        et des techniques avancées de traitement du signal
        
        Args:
            filepath: Chemin du fichier audio
            
        Returns:
            Tuple contenant la liste des notes et la liste des durées
        """
        try:
            if not LIBROSA_AVAILABLE:
                raise ImportError("Librosa n'est pas disponible")
            
            # Vérifier si vamp et melodia sont disponibles
            has_vamp = 'vamp' in globals() and VAMP_AVAILABLE
            
            # Charger le fichier audio
            fs = 44100  # Fréquence d'échantillonnage standard
            hop = 128   # Taille de hop pour Melodia
            
            logger.info(f"Chargement de l'audio {filepath}")
            data, sr = librosa.load(filepath, sr=fs, mono=True)
            
            # Extraction de mélodie: utiliser Melodia si disponible, sinon méthode alternative
            if has_vamp:
                # Extraction via Melodia (meilleure qualité)
                logger.info("Extraction de mélodie avec Melodia...")
                try:
                    melody = vamp.collect(data, fs, "mtg-melodia:melodia", parameters={"voicing": 0.2})
                    pitch = melody['vector'][1]
                    
                    # Imputer les 0 manquants au début
                    pitch = np.insert(pitch, 0, [0]*8)
                    
                    # Convertir les fréquences en notes MIDI
                    midi_pitch = self._hz2midi(pitch)
                    
                    # Segmenter en notes individuelles avec filtrage médian
                    smooth_duration = 0.25  # secondes
                    min_note_duration = 0.1  # secondes
                    
                    # Lisser les notes MIDI
                    filter_size = int(smooth_duration * fs / hop)
                    if filter_size % 2 == 0:
                        filter_size += 1
                    midi_smooth = signal.medfilt(midi_pitch, filter_size)
                    
                    # Extraire les notes et leurs durées
                    notes = []
                    durations = []
                    
                    p_prev = None
                    duration = 0
                    onset = 0
                    
                    for n, p in enumerate(midi_smooth):
                        if p == p_prev:
                            duration += 1
                        else:
                            # Traiter 0 comme silence
                            if p_prev is not None and p_prev > 0:
                                # Ajouter la note
                                duration_sec = duration * hop / float(fs)
                                
                                # Ajouter uniquement les notes assez longues
                                if duration_sec >= min_note_duration:
                                    # Convertir MIDI en nom de note
                                    note_name = self._midi_to_note(int(p_prev))
                                    notes.append(note_name)
                                    durations.append(duration_sec)
                            
                            # Commencer une nouvelle note
                            onset = n
                            duration = 1
                            p_prev = p
                    
                    # Ajouter la dernière note
                    if p_prev is not None and p_prev > 0:
                        duration_sec = duration * hop / float(fs)
                        if duration_sec >= min_note_duration:
                            note_name = self._midi_to_note(int(p_prev))
                            notes.append(note_name)
                            durations.append(duration_sec)
                    
                    logger.info(f"Extraction Melodia réussie: {len(notes)} notes")
                    
                except Exception as e:
                    logger.error(f"Erreur avec Melodia: {e}")
                    has_vamp = False  # Passer à la méthode alternative
            
            # Si Melodia échoue ou n'est pas disponible, utiliser une méthode alternative
            if not has_vamp or not notes:
                logger.info("Utilisation de la méthode alternative d'extraction...")
                
                # Prétraiter l'audio avec des filtres pour améliorer la détection
                y_harmonic, y_percussive = librosa.effects.hpss(data)
                
                # Détecter le BPM (tempo) pour le timing des notes
                tempo, _ = librosa.beat.beat_track(y=y_percussive, sr=fs)
                logger.info(f"Tempo détecté: {tempo} BPM")
                
                # Estimation de la fréquence fondamentale avec des paramètres améliorés
                f0, voiced_flag, voiced_probs = librosa.pyin(
                    y_harmonic,
                    fmin=librosa.note_to_hz('C2'),
                    fmax=librosa.note_to_hz('C6'),
                    sr=fs,
                    frame_length=4096,
                    hop_length=512,
                    fill_na=None
                )
                
                # Seuils améliorés pour la détection de notes
                min_note_confidence = 0.7  # Seuil de confiance pour les notes
                min_note_duration_frames = int(0.1 * fs / 512)  # Minimum ~0.1s
                
                # Détecter les onsets (débuts de notes) pour calculer les durées
                # Combiner plusieurs méthodes pour une meilleure robustesse
                onset_env = librosa.onset.onset_strength(
                    y=y_harmonic, 
                    sr=fs,
                    hop_length=512,
                    aggregate=np.median
                )
                
                onsets = librosa.onset.onset_detect(
                    onset_envelope=onset_env,
                    sr=fs,
                    hop_length=512,
                    backtrack=True,
                    delta=0.1
                )
                
                onset_times = librosa.frames_to_time(onsets, sr=fs, hop_length=512)
                
                # Extraire les notes avec confiance élevée
                notes = []
                current_note = None
                note_start_idx = None
                note_duration = 0
                
                for i, (f, flag, prob) in enumerate(zip(f0, voiced_flag, voiced_probs)):
                    if flag and f > 0 and prob >= min_note_confidence:
                        # Convertir la fréquence en note MIDI puis en nom de note
                        midi_note = int(round(69 + 12 * np.log2(f/440.0)))
                        note = self._midi_to_note(midi_note)
                        
                        if note == current_note:
                            note_duration += 1
                        else:
                            # Ajouter la note précédente si assez longue
                            if current_note and note_duration >= min_note_duration_frames:
                                notes.append(current_note)
                            
                            # Commencer une nouvelle note
                            current_note = note
                            note_start_idx = i
                            note_duration = 1
                    else:
                        # Si voicing=False, considérer comme la fin d'une note
                        if current_note and note_duration >= min_note_duration_frames:
                            notes.append(current_note)
                            current_note = None
                            note_duration = 0
                
                # Ajouter la dernière note si nécessaire
                if current_note and note_duration >= min_note_duration_frames:
                    notes.append(current_note)
                
                # Calculer les durées basées sur les onsets détectés
                durations = []
                
                if len(onset_times) > 1:
                    # Utiliser les différences entre onsets consécutifs
                    for i in range(len(onset_times) - 1):
                        durations.append(onset_times[i+1] - onset_times[i])
                    
                    # Pour la dernière note, utiliser la durée moyenne des autres
                    if durations:
                        durations.append(np.median(durations))
                
                # Si pas assez d'onsets détectés, créer des durées basées sur le tempo
                if len(durations) < len(notes):
                    beat_duration = 60.0 / tempo
                    
                    # Durées typiques: 1/4 note, 1/2 note, note entière
                    typical_durations = [beat_duration * m for m in [0.5, 1, 1.5, 2]]
                    
                    # Générer des durées basées sur le tempo détecté
                    while len(durations) < len(notes):
                        durations.append(random.choice(typical_durations))
            
            # Harmoniser les longueurs des listes
            min_length = min(len(notes), len(durations))
            notes = notes[:min_length]
            durations = durations[:min_length]
            
            # Limiter au nombre de notes souhaité
            if len(notes) > self.melody_length:
                notes = notes[:self.melody_length]
                durations = durations[:self.melody_length]
            
            # Si pas assez de notes, ce qui est peu probable avec cette méthode améliorée
            if len(notes) < self.melody_length // 2:
                logger.warning(f"Extraction insuffisante: seulement {len(notes)} notes")
            
            logger.info(f"Mélodie et rythme extraits: {len(notes)} notes")
            return notes, durations
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction: {e}", exc_info=True)
            return [], []

    def select_random_music(self) -> Optional[Dict[str, Any]]:
        """
        Sélectionne une musique aléatoire de la liste
        
        Returns:
            Informations sur la musique sélectionnée, ou None si la liste est vide
        """
        if not self.music_list:
            if not self.fetch_music_list():
                logger.error("Impossible de récupérer une liste de musiques")
                return None
        
        # Sélectionner une musique aléatoire
        music = random.choice(self.music_list)
        
        # Stocker la musique en cours
        self.current_music = music
        
        return music
    
    def reload_audio(self):
        """Réinitialise pygame mixer pour éviter les problèmes audio"""
        try:
            pygame.mixer.quit()
            time.sleep(0.2)
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            time.sleep(0.2)
            
            # Recharger les sons
            self._reload_instrument_sounds()
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation audio: {e}")
    
    def _reload_instrument_sounds(self):
        """Recharge les sons d'instruments"""
        logger.info("Rechargement des sons d'instruments")
        for note in self.NOTE_FREQUENCIES.keys():
            filepath = os.path.join(self.instrument_dir, f"{self.instrument}_{note}.wav")
            if os.path.exists(filepath):
                try:
                    self.instrument_sounds[note] = pygame.mixer.Sound(filepath)
                except Exception as e:
                    logger.error(f"Erreur lors du rechargement du son {note}: {e}")
    
    def play_melody(self, music_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Extrait et joue la mélodie d'une musique
        
        Args:
            music_info: Informations sur la musique à jouer (optionnel)
            
        Returns:
            True si la lecture a commencée, False sinon
        """
        # Arrêter la lecture précédente
        self.stop_melody()
        
        # Réinitialiser pygame.mixer pour éviter les problèmes
        self.reload_audio()
        
        # Utiliser la musique fournie ou en sélectionner une aléatoire
        if music_info is None:
            music_info = self.select_random_music()
        
        if not music_info:
            logger.error("Aucune musique disponible")
            return False
        
        try:
            # Télécharger la musique
            filepath = self.download_music(music_info)
            if not filepath:
                logger.error(f"Impossible de télécharger {music_info['title']}")
                return False
            
            # Extraire la mélodie
            melody, durations = self.extract_melody_and_rhythm(filepath)
            if not melody:
                logger.error(f"Impossible d'extraire la mélodie pour {music_info['title']}")
                return False
            
            # Stocker la mélodie courante
            self.current_melody = melody
            
            # Lancer la lecture de la mélodie dans un thread séparé
            self._stop_playing = False
            threading.Thread(target=self._play_melody_thread, args=(melody, durations), daemon=True).start()
            
            logger.info(f"Lecture de la mélodie de {music_info['title']} par {music_info['artist']}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la mélodie: {e}")
            return False
    
    def _play_melody_thread(self, melody: List[str], durations: Optional[List[float]] = None) -> None:
        """
        Joue une mélodie dans un thread séparé
        
        Args:
            melody: Liste des notes à jouer
            durations: Liste des durées des notes (optionnel)
        """
        try:
            logger.info(f"Début de la lecture de la mélodie ({len(melody)} notes)")
            
            # Utiliser les durées fournies ou la durée par défaut
            use_extracted_durations = durations is not None and len(durations) == len(melody)
            
            for i, note in enumerate(melody):
                # Arrêter si demandé
                if self._stop_playing:
                    logger.info("Arrêt demandé, fin de la lecture")
                    break
                
                logger.info(f"Lecture note {i+1}/{len(melody)}: {note}")
                
                # Récupérer le son de la note (simplifier pour ne garder que la base + octave 4)
                note_base = note[0]
                if len(note) >= 2 and note[1] == '#':
                    note_base = note[:2]  # Inclure les dièses
                
                # Utiliser l'octave d'origine si présente, sinon utiliser l'octave 4
                if len(note) >= 2 and note[-1].isdigit():
                    playable_note = note
                else:
                    playable_note = f"{note_base}4"
                
                # Si la note n'est pas disponible, prendre la plus proche
                if playable_note not in self.instrument_sounds:
                    # Trouver la note la plus proche
                    closest_notes = [n for n in self.instrument_sounds.keys() if n.startswith(note_base)]
                    if closest_notes:
                        playable_note = closest_notes[0]
                    else:
                        # Si aucune note proche n'est trouvée, utiliser une note par défaut
                        if "C4" in self.instrument_sounds:
                            playable_note = "C4"
                        elif len(self.instrument_sounds) > 0:
                            playable_note = list(self.instrument_sounds.keys())[0]
                        else:
                            logger.error("Aucune note disponible!")
                            break
                
                # Jouer la note
                try:
                    self.instrument_sounds[playable_note].play()
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture de la note {playable_note}: {e}")
                
                # Déterminer la durée de la note
                if use_extracted_durations:
                    # Utiliser la durée extraite avec une petite variation
                    note_duration = durations[i] * random.uniform(0.9, 1.1)
                else:
                    # Variation de tempo pour un jeu plus naturel
                    tempo_factor = 1.0 + random.uniform(-self.tempo_variation, self.tempo_variation)
                    note_duration = self.note_duration * tempo_factor
                
                # Attendre la durée de la note
                time.sleep(note_duration)
                
                # Petit silence entre les notes pour les séparer
                time.sleep(0.05)
            
            logger.info("Fin de la lecture de la mélodie")
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la mélodie: {e}")
    
    def stop_melody(self) -> None:
        """Arrête la lecture de la mélodie en cours"""
        logger.info("Arrêt de la mélodie")
        self._stop_playing = True
        
        try:
            pygame.mixer.stop()
            
            # Arrêter tous les canaux individuellement
            for i in range(pygame.mixer.get_num_channels()):
                try:
                    pygame.mixer.Channel(i).stop()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt de la mélodie: {e}")
    
    def get_current_music_info(self) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations sur la musique en cours
        
        Returns:
            Informations sur la musique en cours, ou None si aucune
        """
        return self.current_music
    
    def check_guess(self, title_guess: str, artist_guess: Optional[str] = None) -> Dict[str, Any]:
        """
        Vérifie si la devinette est correcte
        
        Args:
            title_guess: Titre deviné
            artist_guess: Artiste deviné (optionnel)
            
        Returns:
            Dictionnaire avec les résultats
        """
        if not self.current_music:
            return {
                "title_correct": False,
                "artist_correct": False,
                "correct_title": None,
                "correct_artist": None,
                "score": 0
            }
        
        # Normaliser les chaînes pour la comparaison
        def normalize(s):
            if not s:
                return ""
            return s.lower().strip()
        
        title_guess = normalize(title_guess)
        artist_guess = normalize(artist_guess) if artist_guess else ""
        correct_title = normalize(self.current_music["title"])
        correct_artist = normalize(self.current_music["artist"])
        
        # Vérifier le titre
        title_correct = title_guess == correct_title
        
        # Vérifier l'artiste
        artist_correct = False
        if artist_guess:
            artist_correct = artist_guess == correct_artist
        
        # Calculer un score simple
        score = 0
        if title_correct:
            score += 70  # 70% du score pour le titre
        if artist_correct:
            score += 30  # 30% du score pour l'artiste
        
        # Si le titre est partiellement correct (contient ou est contenu)
        if not title_correct and (title_guess in correct_title or correct_title in title_guess):
            score += 35  # Moitié du score pour le titre
        
        # Si l'artiste est partiellement correct
        if not artist_correct and artist_guess and (artist_guess in correct_artist or correct_artist in artist_guess):
            score += 15  # Moitié du score pour l'artiste
        
        return {
            "title_correct": title_correct,
            "artist_correct": artist_correct,
            "correct_title": self.current_music["title"],
            "correct_artist": self.current_music["artist"],
            "score": score
        }
    
    def play_comparison(self, music_info: Dict[str, Any]) -> bool:
        """
        Joue simultanément la musique originale et la mélodie extraite pour comparer
        
        Args:
            music_info: Informations sur la musique à jouer
            
        Returns:
            True si la lecture a commencé, False sinon
        """
        # Vérifier si on a une mélodie extraite
        if not self.current_melody:
            logger.error("Aucune mélodie extraite disponible pour la comparaison")
            return False
        
        # Vérifier si on a un fichier audio
        filepath = os.path.join(self.music_dir, f"{urllib.parse.quote(music_info['artist'], safe='')}_{urllib.parse.quote(music_info['title'], safe='')}.mp3")
        if not os.path.exists(filepath):
            logger.error(f"Fichier audio original non trouvé: {filepath}")
            return False
        
        try:
            # Réinitialiser pygame.mixer pour éviter les problèmes
            self.reload_audio()
            
            # Charger et jouer la musique originale
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.set_volume(0.7)  # Volume légèrement réduit pour mieux entendre les notes
            pygame.mixer.music.play()
            
            # Attendre un court délai pour la synchronisation
            time.sleep(0.2)
            
            # Lancer la lecture de la mélodie dans un thread séparé
            self._stop_playing = False
            threading.Thread(target=self._play_melody_comparison, args=(self.current_melody,), daemon=True).start()
            
            logger.info(f"Lecture comparative démarrée pour {music_info['title']}")
            print("\nJoue la musique originale et la mélodie extraite simultanément...")
            print("Écoutez attentivement pour comparer si l'extraction est correcte")
            print("Appuyez sur Entrée pour arrêter")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture comparative: {e}")
            return False
    
    def _play_melody_comparison(self, melody: List[str]) -> None:
        """
        Joue la mélodie pour la comparaison (volume plus fort, tempo régulier)
        
        Args:
            melody: Liste des notes à jouer
        """
        try:
            # Attendre que la musique commence
            time.sleep(1.0)
            
            for note in melody:
                # Arrêter si demandé
                if self._stop_playing:
                    break
                
                # Récupérer la note jouable
                note_base = note[0]
                if len(note) >= 2 and note[1] == '#':
                    note_base = note[:2]
                
                if len(note) >= 2 and note[-1].isdigit():
                    playable_note = note
                else:
                    playable_note = f"{note_base}4"
                
                # Si la note n'est pas disponible, prendre la plus proche
                if playable_note not in self.instrument_sounds:
                    closest_notes = [n for n in self.instrument_sounds.keys() if n.startswith(note_base)]
                    if closest_notes:
                        playable_note = closest_notes[0]
                    elif "C4" in self.instrument_sounds:
                        playable_note = "C4"
                    elif len(self.instrument_sounds) > 0:
                        playable_note = list(self.instrument_sounds.keys())[0]
                    else:
                        break
                
                # Jouer la note avec un volume plus élevé
                sound = self.instrument_sounds[playable_note]
                sound.set_volume(1.0)  # Volume maximum pour bien entendre par-dessus la musique
                sound.play()
                
                # Tempo régulier pour la comparaison
                time.sleep(self.note_duration)
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture comparative de la mélodie: {e}")
    
    def stop_comparison(self) -> None:
        """Arrête la lecture comparative"""
        self._stop_playing = True
        pygame.mixer.stop()
        pygame.mixer.music.stop()
    
    def run_game_cli(self, num_rounds: int = 3) -> None:
        """
        Lance le jeu en mode CLI pour un nombre défini de rounds
        
        Args:
            num_rounds: Nombre de rounds à jouer
        """
        print(f"\n{'=' * 60}")
        print(f"{'JEU DE DEVINETTES MÉLODIQUES':^60}")
        print(f"{'Difficulté: ' + self.difficulty + ' | Instrument: ' + self.instrument:^60}")
        print(f"{'=' * 60}\n")
        
        total_score = 0
        
        # Récupérer la liste de musiques
        if not self.fetch_music_list():
            print("Impossible de récupérer des musiques. Fin du jeu.")
            return
        
        for round_num in range(1, num_rounds + 1):
            print(f"\nRound {round_num}/{num_rounds}")
            print("-" * 60)
            
            # Sélectionner et jouer une mélodie aléatoire
            if not self.play_melody():
                print("Impossible de jouer la mélodie. Passage au round suivant.")
                continue
            
            # Attendre que l'utilisateur veuille répondre
            print(f"\nÉcoute de la mélodie ({self.melody_length} notes)...")
            print("Appuyez sur Entrée pour arrêter la mélodie et répondre")
            
            input()  # Attendre l'appui sur Entrée
            self.stop_melody()
            
            # Demander la réponse
            print("\nVotre réponse:")
            title_guess = input("Titre: ")
            artist_guess = input("Artiste: ")
            
            # Vérifier la réponse
            result = self.check_guess(title_guess, artist_guess)
            
            # Afficher le résultat
            print("\nRésultat:")
            print(f"- Titre correct: {result['correct_title']}")
            print(f"- Artiste correct: {result['correct_artist']}")
            print(f"- Score pour ce round: {result['score']}/100")
            
            # Proposer d'écouter les différentes versions
            print("\nOptions d'écoute:")
            print("1. Écouter la version originale")
            print("2. Réécouter la mélodie extraite")
            print("3. Écouter la version originale AVEC la mélodie extraite par dessus")
            print("4. Continuer au prochain round")
            
            choice = input("\nVotre choix (1-4): ")
            
            if choice == "1":
                # Jouer l'extrait original
                filepath = os.path.join(self.music_dir, f"{urllib.parse.quote(result['correct_artist'], safe='')}_{urllib.parse.quote(result['correct_title'], safe='')}.mp3")
                if os.path.exists(filepath):
                    print("\nLecture de l'extrait original...")
                    pygame.mixer.music.load(filepath)
                    pygame.mixer.music.play()
                    
                    print("Appuyez sur Entrée pour arrêter")
                    input()
                    pygame.mixer.music.stop()
            
            elif choice == "2":
                # Rejouer la mélodie extraite
                print("\nRelecture de la mélodie extraite...")
                self.play_melody(self.current_music)
                
                print("Appuyez sur Entrée pour arrêter")
                input()
                self.stop_melody()
            
            elif choice == "3":
                # Jouer les deux ensemble pour comparer
                print("\nComparaison de la mélodie extraite avec l'originale...")
                self.play_comparison(self.current_music)
                
                input()  # Attendre l'appui sur Entrée pour arrêter
                self.stop_comparison()
            
            # Mettre à jour le score total
            total_score += result['score']
        
        # Afficher le score final
        average_score = total_score / num_rounds
        print(f"\n{'=' * 60}")
        print(f"{'FIN DU JEU':^60}")
        print(f"{'Score total: ' + str(total_score) + '/' + str(num_rounds * 100):^60}")
        print(f"{'Score moyen: ' + str(int(average_score)) + '/100':^60}")
        print(f"{'=' * 60}\n")


if __name__ == "__main__":
    # Exemple d'utilisation
    try:
        # Proposer différents instruments
        print("Choisissez un instrument:")
        for idx, instrument in enumerate(MelodyGuessGame.INSTRUMENT_TYPES):
            print(f"{idx+1}. {instrument.capitalize()}")
        
        # Demander le choix
        choice = input("\nVotre choix (1-5, ou Entrée pour aléatoire): ")
        
        # Interpréter le choix
        instrument = None
        if choice.isdigit() and 1 <= int(choice) <= len(MelodyGuessGame.INSTRUMENT_TYPES):
            instrument = MelodyGuessGame.INSTRUMENT_TYPES[int(choice) - 1]
        
        # Choisir la difficulté
        print("\nChoisissez une difficulté:")
        print("1. Facile (16 notes, tempo lent)")
        print("2. Moyen (12 notes, tempo moyen)")
        print("3. Difficile (8 notes, tempo rapide)")
        
        diff_choice = input("\nVotre choix (1-3, ou Entrée pour moyen): ")
        
        # Interpréter le choix de difficulté
        difficulty = "medium"
        if diff_choice == "1":
            difficulty = "easy"
        elif diff_choice == "3":
            difficulty = "hard"
        
        # Créer le jeu
        print("\nInitialisation du jeu...")
        game = MelodyGuessGame(difficulty=difficulty, instrument=instrument)
        
        # Lancer le jeu
        game.run_game_cli(num_rounds=3)
        
    except ImportError as e:
        print(f"Veuillez installer les bibliothèques manquantes: {e}")
    except Exception as e:
        print(f"Erreur lors de l'exécution du jeu: {e}")
        import traceback
        traceback.print_exc()