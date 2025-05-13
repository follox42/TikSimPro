"""
Module pour jouer des mélodies populaires note par note à chaque rebond ou action.
Transforme la simulation en une performance musicale générée par la physique.
"""

import os
import pygame
import numpy as np
import random
import time
import requests
from io import BytesIO
import wave
from pydub import AudioSegment
import tempfile

class MelodyPlayer:
    """Joue des notes de mélodies populaires à chaque rebond ou action"""
    
    # Mélodies populaires de TikTok (avec séquences de notes)
    # Chaque mélodie est représentée par une liste d'indices de notes
    # 0=Do, 1=Ré, 2=Mi, 3=Fa, 4=Sol, 5=La, 6=Si
    POPULAR_MELODIES = {
        "Super Mario": [4, 4, 0, 4, 6, 5],  # Thème de Super Mario
        "Harry Potter": [6, 2, 5, 3, 4, 0],  # Hedwig's Theme
        "Game of Thrones": [4, 2, 0, 2, 4],  # Thème principal
        "Star Wars": [4, 4, 4, 0, 6, 4],  # La Force
        "Stranger Things": [2, 3, 4, 5, 4, 3, 2],  # Thème principal
        "La La Land": [0, 2, 4, 0, 2, 4, 6],  # City of Stars
        "Despacito": [6, 6, 5, 4, 4, 5, 6],  # Refrain
        "Dance Monkey": [4, 5, 6, 6, 5, 4, 2],  # Refrain
        "Sweet Child O' Mine": [6, 5, 4, 6, 5, 4, 6, 5, 6],  # Intro guitare
        "Squid Game": [4, 2, 4, 2, 0]  # Pink Soldiers
    }
    
    # Facteurs d'échelle d'octave pour générer des notes
    # Ces facteurs multiplient la fréquence de base pour obtenir différentes octaves
    OCTAVE_FACTORS = [0.5, 1.0, 2.0]  # Octave basse, moyenne, haute
    
    def __init__(self):
        """Initialise le lecteur de mélodies"""
        # Initialiser pygame pour l'audio
        if not pygame.mixer.get_init():
            pygame.mixer.init(44100, -16, 2, 512)
        
        # Répertoire de stockage des notes
        self.notes_dir = "melody_notes"
        if not os.path.exists(self.notes_dir):
            os.makedirs(self.notes_dir)
        
        # Dictionnaires pour stocker les notes chargées
        self.melodies = {}  # Dictionnaire des mélodies chargées
        self.current_melody = None  # Mélodie actuellement utilisée
        self.current_note_index = 0  # Position dans la mélodie
        
        # Fréquences de base des notes (gamme de Do majeur)
        self.note_freqs = {
            0: 261.63,  # Do
            1: 293.66,  # Ré
            2: 329.63,  # Mi
            3: 349.23,  # Fa
            4: 392.00,  # Sol
            5: 440.00,  # La
            6: 493.88,  # Si
        }
        
        # Charger les notes de toutes les mélodies
        self.load_all_melodies()
        
        # Canaux audio
        self.channels = [pygame.mixer.Channel(i) for i in range(16)]  # 16 canaux pour jouer plusieurs notes simultanément
        self.current_channel = 0
    
    def generate_note(self, frequency, duration=0.3, volume=0.7):
        """
        Génère un fichier audio pour une note de la fréquence donnée
        
        Args:
            frequency: Fréquence de la note en Hz
            duration: Durée de la note en secondes
            volume: Volume de la note (0.0 à 1.0)
            
        Returns:
            Le chemin du fichier audio généré
        """
        # Paramètres pour la génération de notes
        sample_rate = 44100
        
        # Générer le nom du fichier basé sur la fréquence
        filename = f"note_{int(frequency)}.wav"
        filepath = os.path.join(self.notes_dir, filename)
        
        # Ne générer que si le fichier n'existe pas déjà
        if not os.path.exists(filepath):
            try:
                # Nombre d'échantillons
                num_samples = int(sample_rate * duration)
                
                # Générer une onde sinusoïdale avec enveloppe ADSR
                samples = np.zeros(num_samples, dtype=np.float32)
                
                # Paramètres ADSR (en pourcentage de la durée totale)
                attack = 0.1
                decay = 0.1
                sustain_level = 0.7
                release = 0.3
                
                attack_samples = int(attack * num_samples)
                decay_samples = int(decay * num_samples)
                release_samples = int(release * num_samples)
                sustain_samples = num_samples - attack_samples - decay_samples - release_samples
                
                # Générer l'enveloppe ADSR
                envelope = np.zeros(num_samples)
                
                # Phase d'attaque
                envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
                
                # Phase de decay
                envelope[attack_samples:attack_samples+decay_samples] = np.linspace(1, sustain_level, decay_samples)
                
                # Phase de sustain
                envelope[attack_samples+decay_samples:attack_samples+decay_samples+sustain_samples] = sustain_level
                
                # Phase de release
                envelope[attack_samples+decay_samples+sustain_samples:] = np.linspace(sustain_level, 0, release_samples)
                
                # Générer la forme d'onde
                for i in range(num_samples):
                    # Ajouter une légère modulation pour un son plus riche
                    t = i / sample_rate
                    mod = 1.0 + 0.005 * np.sin(2 * np.pi * 5 * t)
                    samples[i] = volume * np.sin(2 * np.pi * frequency * mod * t) * envelope[i]
                
                # Ajouter quelques harmoniques
                for harmonic, factor in [(2, 0.3), (3, 0.2), (4, 0.1)]:
                    harmonic_freq = frequency * harmonic
                    for i in range(num_samples):
                        t = i / sample_rate
                        samples[i] += volume * factor * np.sin(2 * np.pi * harmonic_freq * t) * envelope[i]
                
                # Normaliser
                max_val = np.max(np.abs(samples))
                if max_val > 0:
                    samples = samples / max_val * 0.9
                
                # Convertir en 16 bits
                samples = (samples * 32767).astype(np.int16)
                
                # Créer un fichier WAV stéréo
                stereo_samples = np.column_stack((samples, samples))
                
                # Sauvegarder le fichier WAV
                with wave.open(filepath, 'wb') as wf:
                    wf.setnchannels(2)
                    wf.setsampwidth(2)  # 16 bits
                    wf.setframerate(sample_rate)
                    wf.writeframes(stereo_samples.tobytes())
                
                print(f"Note générée: {filepath}")
                
            except Exception as e:
                print(f"Erreur lors de la génération de la note {frequency}Hz: {e}")
                return None
        
        return filepath
    
    def load_melody(self, melody_name):
        """
        Charge une mélodie par son nom
        
        Args:
            melody_name: Nom de la mélodie à charger
            
        Returns:
            La liste des notes de la mélodie (objets pygame.mixer.Sound)
        """
        if melody_name in self.melodies:
            # Mélodie déjà chargée
            return self.melodies[melody_name]
        
        if melody_name not in self.POPULAR_MELODIES:
            print(f"Mélodie inconnue: {melody_name}")
            return None
        
        # Récupérer la séquence de notes
        note_sequence = self.POPULAR_MELODIES[melody_name]
        
        # Charger ou générer chaque note
        melody_notes = []
        
        for note_idx in note_sequence:
            # Obtenir la fréquence de base
            freq = self.note_freqs.get(note_idx, 261.63)  # Do par défaut
            
            # Choisir un facteur d'octave aléatoire
            octave_factor = random.choice(self.OCTAVE_FACTORS)
            actual_freq = freq * octave_factor
            
            # Générer ou récupérer le fichier audio
            note_path = self.generate_note(actual_freq)
            
            if note_path and os.path.exists(note_path):
                try:
                    # Charger la note
                    note_sound = pygame.mixer.Sound(note_path)
                    melody_notes.append(note_sound)
                except Exception as e:
                    print(f"Erreur lors du chargement de la note {note_path}: {e}")
        
        # Sauvegarder la mélodie chargée
        self.melodies[melody_name] = melody_notes
        
        return melody_notes
    
    def load_all_melodies(self):
        """Charge toutes les mélodies disponibles"""
        for melody_name in self.POPULAR_MELODIES:
            self.load_melody(melody_name)
    
    def set_current_melody(self, melody_name):
        """
        Définit la mélodie actuelle
        
        Args:
            melody_name: Nom de la mélodie à utiliser
            
        Returns:
            True si la mélodie a été définie, False sinon
        """
        if melody_name not in self.POPULAR_MELODIES:
            print(f"Mélodie inconnue: {melody_name}")
            return False
        
        # Charger la mélodie si nécessaire
        if melody_name not in self.melodies:
            self.load_melody(melody_name)
        
        # Définir la mélodie actuelle
        self.current_melody = melody_name
        self.current_note_index = 0
        
        print(f"Mélodie actuelle: {melody_name}")
        return True
    
    def play_next_note(self, velocity=1.0):
        """
        Joue la note suivante de la mélodie actuelle
        
        Args:
            velocity: Vélocité (volume) de la note (0.0 à 1.0)
            
        Returns:
            L'indice de la note jouée
        """
        if not self.current_melody or self.current_melody not in self.melodies:
            # Si aucune mélodie n'est définie, en choisir une aléatoirement
            self.set_current_melody(random.choice(list(self.POPULAR_MELODIES.keys())))
        
        # Récupérer les notes de la mélodie
        melody_notes = self.melodies[self.current_melody]
        
        if not melody_notes:
            return None
        
        # Récupérer la note suivante
        note_index = self.current_note_index % len(melody_notes)
        note = melody_notes[note_index]
        
        # Avancer dans la mélodie
        self.current_note_index = (self.current_note_index + 1) % len(melody_notes)
        
        # Définir le volume en fonction de la vélocité
        volume = min(1.0, max(0.1, velocity))
        note.set_volume(volume)
        
        # Jouer la note sur un canal disponible
        channel = self.channels[self.current_channel]
        self.current_channel = (self.current_channel + 1) % len(self.channels)
        channel.play(note)
        
        return note_index
    
    def play_random_note(self, velocity=1.0):
        """
        Joue une note aléatoire de la mélodie actuelle
        
        Args:
            velocity: Vélocité (volume) de la note (0.0 à 1.0)
            
        Returns:
            L'indice de la note jouée
        """
        if not self.current_melody or self.current_melody not in self.melodies:
            # Si aucune mélodie n'est définie, en choisir une aléatoirement
            self.set_current_melody(random.choice(list(self.POPULAR_MELODIES.keys())))
        
        # Récupérer les notes de la mélodie
        melody_notes = self.melodies[self.current_melody]
        
        if not melody_notes:
            return None
        
        # Choisir une note aléatoire
        note_index = random.randint(0, len(melody_notes) - 1)
        note = melody_notes[note_index]
        
        # Définir le volume en fonction de la vélocité
        volume = min(1.0, max(0.1, velocity))
        note.set_volume(volume)
        
        # Jouer la note sur un canal disponible
        channel = self.channels[self.current_channel]
        self.current_channel = (self.current_channel + 1) % len(self.channels)
        channel.play(note)
        
        return note_index
    
    def list_available_melodies(self):
        """Affiche la liste des mélodies disponibles"""
        print("\nMélodies disponibles:")
        print("-" * 50)
        
        for i, melody_name in enumerate(self.POPULAR_MELODIES.keys()):
            print(f"{i+1}. {melody_name}")
        
        print("-" * 50)
        return list(self.POPULAR_MELODIES.keys())
    
    def choose_melody(self):
        """
        Permet à l'utilisateur de choisir une mélodie
        
        Returns:
            Le nom de la mélodie choisie
        """
        melodies = self.list_available_melodies()
        
        while True:
            try:
                choice = input("\nChoisissez une mélodie (1-10) ou 'r' pour aléatoire: ")
                
                if choice.lower() == 'r':
                    selected = random.choice(melodies)
                    self.set_current_melody(selected)
                    return selected
                
                index = int(choice) - 1
                if 0 <= index < len(melodies):
                    selected = melodies[index]
                    self.set_current_melody(selected)
                    return selected
                else:
                    print(f"Veuillez entrer un nombre entre 1 et {len(melodies)}")
            except ValueError:
                print("Veuillez entrer un nombre valide")
    
    def demo_melody(self, melody_name):
        """Joue une démo de la mélodie"""
        if melody_name not in self.POPULAR_MELODIES:
            print(f"Mélodie inconnue: {melody_name}")
            return
        
        # Charger la mélodie si nécessaire
        if melody_name not in self.melodies:
            self.load_melody(melody_name)
        
        # Récupérer les notes de la mélodie
        melody_notes = self.melodies[melody_name]
        
        if not melody_notes:
            print(f"Aucune note disponible pour la mélodie: {melody_name}")
            return
        
        print(f"Démo de la mélodie: {melody_name}")
        
        # Jouer chaque note de la mélodie
        for i, note in enumerate(melody_notes):
            print(f"Note {i+1}/{len(melody_notes)}")
            note.play()
            time.sleep(0.5)  # Pause entre les notes


# Fonction pour intégrer le lecteur de mélodies dans la simulation
def integrate_melody_player(simulation):
    """
    Intègre le lecteur de mélodies dans une simulation existante.
    
    Args:
        simulation: L'instance de la classe Simulation existante
        
    Returns:
        Le lecteur de mélodies intégré
    """
    # Créer le lecteur de mélodies
    melody_player = MelodyPlayer()
    
    # Associer le lecteur de mélodies à la simulation
    simulation.melody_player = melody_player
    
    # Méthode pour jouer une note
    original_play_note = simulation.play_note if hasattr(simulation, 'play_note') else None
    
    def enhanced_play_note(note_index=None):
        # Utiliser le lecteur de mélodies pour jouer la note suivante
        try:
            if note_index is not None:
                # Si un indice est spécifié, jouer cette note
                return simulation.melody_player.play_random_note()
            else:
                # Sinon, jouer la note suivante dans la séquence
                return simulation.melody_player.play_next_note()
        except Exception as e:
            print(f"Erreur lors de la lecture de note: {e}")
            # Utiliser la méthode originale en cas d'erreur
            if original_play_note:
                return original_play_note(note_index)
            return None
    
    # Remplacer la méthode de jeu de note
    simulation.play_note = enhanced_play_note
    
    # Améliorer la méthode on_ball_hit_wall
    if hasattr(simulation, 'on_ball_hit_wall'):
        original_on_ball_hit_wall = simulation.on_ball_hit_wall
        
        def enhanced_on_ball_hit_wall(arbiter, space, data):
            result = original_on_ball_hit_wall(arbiter, space, data)
            
            # Ajouter un son de note basé sur la vitesse
            ball_shape = arbiter.shapes[0] if arbiter.shapes[0].collision_type == 1 else arbiter.shapes[1]
            for ball in simulation.balls:
                if ball.shape == ball_shape:
                    velocity_magnitude = np.linalg.norm(ball.body.velocity)
                    normalized_velocity = min(1.0, velocity_magnitude / 2000)
                    
                    # Jouer une note
                    try:
                        simulation.melody_player.play_next_note(normalized_velocity)
                    except Exception as e:
                        print(f"Erreur lors de la lecture de note (rebond): {e}")
                    
                    break
            
            return result
        
        simulation.on_ball_hit_wall = enhanced_on_ball_hit_wall
    
    # Améliorer la méthode on_ball_hit_ball
    if hasattr(simulation, 'on_ball_hit_ball'):
        original_on_ball_hit_ball = simulation.on_ball_hit_ball
        
        def enhanced_on_ball_hit_ball(arbiter, space, data):
            result = original_on_ball_hit_ball(arbiter, space, data)
            
            # Ajouter un son de note basé sur la vitesse combinée
            shapes = arbiter.shapes
            total_velocity = 0
            
            for shape in shapes:
                for ball in simulation.balls:
                    if ball.shape == shape:
                        velocity_magnitude = np.linalg.norm(ball.body.velocity)
                        total_velocity += velocity_magnitude
            
            # Normaliser la vitesse totale
            normalized_velocity = min(1.0, total_velocity / 4000)
            
            # Jouer une note
            try:
                simulation.melody_player.play_next_note(normalized_velocity)
            except Exception as e:
                print(f"Erreur lors de la lecture de note (collision): {e}")
            
            return result
        
        simulation.on_ball_hit_ball = enhanced_on_ball_hit_ball
    
    # Améliorer la méthode on_ball_hit_target
    if hasattr(simulation, 'on_ball_hit_target'):
        original_on_ball_hit_target = simulation.on_ball_hit_target
        
        def enhanced_on_ball_hit_target(arbiter, space, data):
            result = original_on_ball_hit_target(arbiter, space, data)
            
            # Ajouter un son de note pour l'explosion
            # Utiliser une vélocité plus élevée pour un son plus fort
            try:
                simulation.melody_player.play_next_note(1.0)  # Volume maximal
            except Exception as e:
                print(f"Erreur lors de la lecture de note (explosion): {e}")
            
            return result
        
        simulation.on_ball_hit_target = enhanced_on_ball_hit_target
    
    print("Lecteur de mélodies intégré avec succès dans la simulation")
    return melody_player


# Exemple d'utilisation
if __name__ == "__main__":
    # Exemple d'utilisation simple
    player = MelodyPlayer()
    
    # Afficher les mélodies disponibles
    player.list_available_melodies()
    
    # Demander à l'utilisateur de choisir une mélodie
    melody_name = player.choose_melody()
    
    # Jouer une démo de la mélodie
    player.demo_melody(melody_name)
    
    print("\nAppuyez sur Ctrl+C pour quitter...")
    
    # Simulation de rebonds aléatoires
    try:
        while True:
            # Jouer la note suivante comme si c'était un rebond
            player.play_next_note(random.uniform(0.5, 1.0))
            time.sleep(random.uniform(0.2, 0.5))  # Pause aléatoire
    except KeyboardInterrupt:
        print("\nDémo terminée.")