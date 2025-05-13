"""
Module de simulation physique optimisé pour TikSimPro
Génère des vidéos avec des simulations de physique de particules synchronisées à la musique
Version optimisée: calculs arrondis et optimisations de performance
"""

import os
import time
import random
import logging
import numpy as np
import pygame
import pymunk
from pathlib import Path
import wave
import cv2
from scipy.io import wavfile
from moviepy import ImageSequenceClip, AudioFileClip
from simulators.base_simulator import BaseSimulator

logger = logging.getLogger("TikSimPro")

class AdvancedPhysicsSimulation(BaseSimulator):
    """
    Module de simulation physique optimisée avec effets visuels et sonores
    Version rapide avec arrondis et optimisations
    """
    
    def __init__(self, width=1080, height=1920, fps=60, duration=61, output_path="output.mp4"):
        """
        Initialise la simulation physique optimisée
        
        Args:
            width: Largeur de la vidéo (format vertical TikTok par défaut)
            height: Hauteur de la vidéo
            fps: Images par seconde
            duration: Durée en secondes
            output_path: Chemin du fichier de sortie
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = duration
        self.output_path = output_path
        self.output_audio_file = None
        
        # Frames à générer
        self.total_frames = int(duration * fps)
        
        # Paramètres physiques (entiers pour optimisation)
        self.gravity = 1000
        
        # Palettes de couleurs (prédéfinies pour être plus rapide)
        self.color_palette = ["#FF0050", "#00F2EA", "#FFFFFF", "#FE2C55"]
        self.color_rgb_cache = {color: self.hex_to_rgb(color) for color in self.color_palette}
        
        # Répertoires de travail
        self._init_directories()
        
        # Paramètres de timing
        self.beat_frequency = 1.0  # secondes entre les beats musicaux
        
        # Objets de la simulation
        self.balls = []
        self.targets = []
        self.particles = []
        self.space = None
        
        # Réduire le nombre maximum d'objets pour optimisation
        self.max_balls = 30
        self.max_targets = 15
        self.max_particles = 200
        
        # Paramètres dynamiques pour les événements
        self.next_ball_time = 0
        self.next_target_time = 0
        self.next_event_time = 0
        
        # Musique et sons
        self.notes = []
        self.current_melody = []
        self.sound_events = []
        
        # Événements spéciaux
        self.special_effects = []
        
        # État de la simulation
        self.current_frame = 0
        self.simulation_running = False
        
        # Mémoire cache pour les surfaces
        self.surface_cache = {}
        
        # Paramètres de rendu optimisé
        self.render_quality = 'medium'  # 'low', 'medium', 'high'
        self.use_grid = True
        self.trail_length = 10  # Réduit pour optimisation
        
        # Optimisations de calcul
        self.update_frequency = max(1, 2)  # Mise à jour des particules tous les N frames (minimum 1)
        self.particle_batch_size = max(1, 20)  # Traiter les particules par lots (minimum 1)
        
        logger.info(f"Simulation optimisée initialisée: {width}x{height}, {fps} FPS, {duration}s")
    
    def _init_directories(self):
        """Initialise les répertoires de travail"""
        # Répertoires principaux
        self.temp_dir = os.path.join(os.getcwd(), "temp")
        self.frames_dir = os.path.join(self.temp_dir, "frames")
        self.sounds_dir = os.path.join(self.temp_dir, "sounds")
        
        # Créer tous les répertoires en une seule fois
        for directory in [self.temp_dir, self.frames_dir, self.sounds_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def setup(self, config):
        """Configure le simulateur avec les paramètres spécifiés"""
        # Appliquer tous les paramètres de configuration
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Recalculer les frames totaux si la durée a changé
        self.total_frames = int(self.duration * self.fps)
        
        # Assurer que les paramètres de calcul ne sont jamais zéro
        self.update_frequency = max(1, self.update_frequency)
        self.particle_batch_size = max(1, self.particle_batch_size)
        
        # Assurer que le répertoire de sortie existe
        output_dir = os.path.dirname(self.output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Réinitialiser l'état
        self.current_frame = 0
        self.balls = []
        self.targets = []
        self.particles = []
        self.special_effects = []
        self.sound_events = []
        
        # Générer un chemin pour le fichier audio
        base_path = os.path.splitext(self.output_path)[0]
        self.output_audio_file = f"{base_path}_audio.wav"
        
        # Précalculer la palette de couleurs
        self.color_rgb_cache = {color: self.hex_to_rgb(color) for color in self.color_palette}

        return True
    
    def set_color_palette(self, palette):
        """Définit la palette de couleurs à utiliser"""
        if isinstance(palette, list) and len(palette) > 0:
            self.color_palette = palette
            # Mettre à jour le cache de couleurs RGB
            self.color_rgb_cache = {color: self.hex_to_rgb(color) for color in self.color_palette}
            logger.info(f"Palette de couleurs définie: {palette}")
    
    def set_melody(self, melody_notes):
        """Définit la mélodie à jouer sur les rebonds"""
        if melody_notes and isinstance(melody_notes, list):
            self.current_melody = melody_notes
            logger.info(f"Mélodie définie: {len(melody_notes)} notes")
    
    def set_beat_frequency(self, frequency):
        """Définit la fréquence des beats musicaux"""
        if isinstance(frequency, (int, float)) and frequency > 0:
            self.beat_frequency = frequency
            logger.info(f"Fréquence des beats définie: {frequency}s")
    
    def hex_to_rgb(self, hex_color):
        """Convertit une couleur hexadécimale en RGB"""
        try:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except (ValueError, AttributeError, IndexError):
            return (255, 255, 255)  # Blanc par défaut
    
    def generate_sounds(self):
        """Génère les sons pour la simulation"""
        logger.info("Génération des sons...")
        
        # Fréquences de base des notes (gamme de Do majeur)
        note_freqs = {
            0: 262,  # Do (arrondi)
            1: 294,  # Ré (arrondi)
            2: 330,  # Mi (arrondi)
            3: 349,  # Fa (arrondi)
            4: 392,  # Sol (arrondi)
            5: 440,  # La (arrondi)
            6: 494,  # Si (arrondi)
        }
        
        # Paramètres pour la génération de notes
        sample_rate = 44100
        note_duration = 0.5  # secondes
        
        # Générer chaque note pour différentes octaves
        for note_idx, freq_key in enumerate(note_freqs):
            base_freq = note_freqs[freq_key]
            
            for octave, factor in enumerate([0.5, 1.0, 2.0]):
                freq = int(base_freq * factor)  # Arrondir la fréquence
                note_path = os.path.join(self.sounds_dir, f"note_{note_idx}_oct{octave}.wav")
                
                # Vérifier si la note existe déjà
                if os.path.exists(note_path) and os.path.getsize(note_path) > 0:
                    self.notes.append((note_idx, octave, note_path))
                    continue
                
                try:
                    # Générer l'onde sonore
                    num_samples = int(sample_rate * note_duration)
                    samples = np.zeros(num_samples, dtype=np.float32)
                    
                    # Paramètres ADSR
                    attack = 0.1
                    decay = 0.1
                    sustain_level = 0.7
                    release = 0.3
                    
                    attack_samples = int(attack * num_samples)
                    decay_samples = int(decay * num_samples)
                    release_samples = int(release * num_samples)
                    sustain_samples = num_samples - attack_samples - decay_samples - release_samples
                    
                    # Créer l'enveloppe ADSR
                    envelope = np.zeros(num_samples)
                    envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
                    envelope[attack_samples:attack_samples+decay_samples] = np.linspace(1, sustain_level, decay_samples)
                    envelope[attack_samples+decay_samples:attack_samples+decay_samples+sustain_samples] = sustain_level
                    envelope[attack_samples+decay_samples+sustain_samples:] = np.linspace(sustain_level, 0, release_samples)
                    
                    # Générer le son (simplifié pour optimisation)
                    t = np.arange(num_samples) / sample_rate
                    samples = 0.8 * np.sin(2 * np.pi * freq * t) * envelope
                    
                    # Ajouter un harmonique pour complexité
                    samples += 0.3 * np.sin(2 * np.pi * freq * 2 * t) * envelope
                    
                    # Normaliser
                    max_val = np.max(np.abs(samples))
                    if max_val > 0:
                        samples = samples / max_val * 0.9
                    
                    # Convertir en 16 bits
                    samples = (samples * 32767).astype(np.int16)
                    
                    # Créer un fichier WAV stéréo
                    stereo_samples = np.column_stack((samples, samples))
                    
                    # Sauvegarder le fichier WAV
                    with wave.open(note_path, 'wb') as wf:
                        wf.setnchannels(2)
                        wf.setsampwidth(2)  # 16 bits
                        wf.setframerate(sample_rate)
                        wf.writeframes(stereo_samples.tobytes())
                    
                    self.notes.append((note_idx, octave, note_path))
                    
                except Exception as e:
                    logger.error(f"Erreur génération note {note_idx} octave {octave}: {e}")
        
        # Générer des sons d'explosion (simplifiés)
        self._generate_explosion_sounds(sample_rate)
        
        logger.info(f"Sons générés: {len(self.notes)} notes")
    
    def _generate_explosion_sounds(self, sample_rate=44100):
        """Génère les sons d'explosion (version optimisée)"""
        for size in ["small", "medium", "large"]:
            explosion_path = os.path.join(self.sounds_dir, f"explosion_{size}.wav")
            
            # Vérifier si le son existe déjà
            if os.path.exists(explosion_path) and os.path.getsize(explosion_path) > 0:
                continue
            
            try:
                # Paramètres basés sur la taille (arrondis pour optimisation)
                if size == "small":
                    base_freq = 100
                    duration = 0.5
                elif size == "medium":
                    base_freq = 80
                    duration = 0.7
                else:  # large
                    base_freq = 60
                    duration = 1.0
                
                # Génération simplifiée pour optimisation
                num_samples = int(sample_rate * duration)
                t = np.arange(num_samples) / sample_rate
                
                # Enveloppe simplifiée
                envelope = np.ones(num_samples)
                envelope[:int(0.1*num_samples)] = np.linspace(0, 1, int(0.1*num_samples))
                envelope[int(0.7*num_samples):] = np.linspace(1, 0, num_samples-int(0.7*num_samples))
                
                # Générer le son d'explosion (version simplifiée)
                noise = np.random.uniform(-1, 1, num_samples)
                samples = (0.7 * np.sin(2 * np.pi * base_freq * t) + 0.5 * noise) * envelope
                
                # Normaliser
                samples = samples / np.max(np.abs(samples)) * 0.9
                
                # Convertir en 16 bits
                samples = (samples * 32767).astype(np.int16)
                
                # Créer un fichier WAV stéréo
                stereo_samples = np.column_stack((samples, samples))
                
                # Sauvegarder le fichier WAV
                with wave.open(explosion_path, 'wb') as wf:
                    wf.setnchannels(2)
                    wf.setsampwidth(2)  # 16 bits
                    wf.setframerate(sample_rate)
                    wf.writeframes(stereo_samples.tobytes())
                    
            except Exception as e:
                logger.error(f"Erreur génération explosion {size}: {e}")
    
    def render_audio_from_events(self, output_file=None):
        """
        Génère la piste audio à partir des événements (version améliorée)
        Garantit que tous les événements sonores sont traités
        """
        if not output_file:
            output_file = self.output_audio_file or "output_audio.wav"
                
        logger.info(f"Génération de la piste audio à partir de {len(self.sound_events)} événements...")

        try:
            # Si aucun événement sonore, créer un fichier audio vide
            if not self.sound_events:
                logger.warning("Aucun événement sonore, création d'un fichier audio vide")
                # Créer un fichier audio vide de la durée de la vidéo
                sample_rate = 44100
                num_samples = int(sample_rate * self.duration)
                silent_audio = np.zeros((num_samples, 2), dtype=np.float32)
                wavfile.write(output_file, sample_rate, (silent_audio * 32767).astype(np.int16))
                return output_file
                    
            sample_rate = 44100
            total_duration = self.duration  # Durée de la vidéo = durée de l'audio
            num_samples = int(sample_rate * total_duration)

            # Timeline audio stéréo initialisée à 0
            audio_timeline = np.zeros((num_samples, 2), dtype=np.float32)

            # Précharger tous les sons et les mettre en cache
            sound_cache = {}
            
            # Précharger tous les sons de notes
            for note_idx in range(7):  # Do à Si
                for octave in range(3):  # 3 octaves
                    note_file = os.path.join(self.sounds_dir, f"note_{note_idx}_oct{octave}.wav")
                    if os.path.exists(note_file):
                        try:
                            sr, sound_data = wavfile.read(note_file)
                            # Normaliser en float32 [-1.0, 1.0]
                            if sound_data.dtype == np.int16:
                                sound_data = sound_data.astype(np.float32) / 32767.0
                            # Si mono → stéréo
                            if len(sound_data.shape) == 1:
                                sound_data = np.column_stack((sound_data, sound_data))
                            sound_cache[note_file] = sound_data
                        except Exception as e:
                            logger.error(f"Erreur préchargement {note_file}: {e}")
            
            # Précharger les sons d'explosion
            for size in ["small", "medium", "large"]:
                explosion_file = os.path.join(self.sounds_dir, f"explosion_{size}.wav")
                if os.path.exists(explosion_file):
                    try:
                        sr, sound_data = wavfile.read(explosion_file)
                        # Normaliser en float32 [-1.0, 1.0]
                        if sound_data.dtype == np.int16:
                            sound_data = sound_data.astype(np.float32) / 32767.0
                        # Si mono → stéréo
                        if len(sound_data.shape) == 1:
                            sound_data = np.column_stack((sound_data, sound_data))
                        sound_cache[explosion_file] = sound_data
                    except Exception as e:
                        logger.error(f"Erreur préchargement {explosion_file}: {e}")
            
            # Traiter chaque événement sonore
            events_processed = 0
            for event in self.sound_events:
                time_offset = event["time"]
                event_type = event["type"]
                params = event["params"]

                # Déterminer le fichier son à utiliser
                if event_type == "note":
                    note_idx = params.get("note", 0)
                    octave = params.get("octave", 1)
                    note_file = os.path.join(self.sounds_dir, f"note_{note_idx}_oct{octave}.wav")
                elif event_type == "explosion":
                    size = params.get("size", "medium")
                    note_file = os.path.join(self.sounds_dir, f"explosion_{size}.wav")
                else:
                    continue

                # Charger le son
                sound_data = None
                if note_file in sound_cache:
                    sound_data = sound_cache[note_file]
                elif os.path.exists(note_file):
                    try:
                        sr, sound_data = wavfile.read(note_file)
                        # Normaliser en float32 [-1.0, 1.0]
                        if sound_data.dtype == np.int16:
                            sound_data = sound_data.astype(np.float32) / 32767.0
                        # Si mono → stéréo
                        if len(sound_data.shape) == 1:
                            sound_data = np.column_stack((sound_data, sound_data))
                        # Mettre en cache
                        sound_cache[note_file] = sound_data
                    except Exception as e:
                        logger.error(f"Erreur lecture {note_file}: {e}")
                        continue
                else:
                    logger.warning(f"Fichier son introuvable: {note_file}")
                    continue

                if sound_data is None:
                    continue

                # Ajouter le son à la timeline
                start_sample = int(time_offset * sample_rate)
                
                # Ignorer les sons hors timeline
                if start_sample >= num_samples:
                    continue
                    
                # Ajuster la longueur si nécessaire
                end_sample = min(start_sample + sound_data.shape[0], num_samples)
                data_length = end_sample - start_sample
                
                # Additionner le son sur la timeline (avec gain augmenté pour plus de volume)
                audio_timeline[start_sample:end_sample] += sound_data[:data_length] * 1.5  # Augmentation du volume
                
                events_processed += 1

            # Normaliser l'audio final pour éviter les saturations
            max_val = np.max(np.abs(audio_timeline))
            if max_val > 1.0:
                audio_timeline = audio_timeline / max_val * 0.95  # Laisser un peu de marge

            # Convertir en int16
            audio_output = (audio_timeline * 32767).astype(np.int16)

            # Sauvegarder le fichier WAV
            wavfile.write(output_file, sample_rate, audio_output)

            logger.info(f"Piste audio générée avec {events_processed}/{len(self.sound_events)} événements sonores")
            return output_file
        
        except Exception as e:
            logger.error(f"Erreur génération audio: {e}")
            return None
    
    def initialize_physics(self):
        """Initialise le monde physique et les objets"""
        logger.info("Initialisation de la physique...")
        
        try:
            # Initialiser pymunk avec des paramètres optimisés
            self.space = pymunk.Space()
            self.space.gravity = (0, self.gravity)
            
            # Optimiser les étapes de simulation
            self.space.iterations = 10  # Nombre d'itérations (par défaut: 10)
            self.space.damping = 0.9   # Amortissement global (par défaut: 1.0)
            
            # Créer les murs (sol et côtés)
            self.create_boundaries()
            
            # Configuration des collisions
            self.setup_collision_handlers()
            
            # Ajouter quelques objets initiaux (moins pour optimisation)
            for _ in range(5):
                self.add_random_target()
            
            logger.info("Physique initialisée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur initialisation physique: {e}")
            return False
    
    def create_boundaries(self):
        """Crée les murs autour de l'écran (simplifiés)"""
        # Épaisseur des murs (arrondie)
        thickness = 50
        
        # Créer les segments (bas, gauche, droite)
        boundaries = [
            # Segment du bas
            [(0, self.height), (self.width, self.height), thickness],
            # Segment de gauche
            [(0, 0), (0, self.height), thickness],
            # Segment de droite
            [(self.width, 0), (self.width, self.height), thickness]
        ]
        
        for boundary in boundaries:
            start, end, thickness = boundary
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            shape = pymunk.Segment(body, start, end, thickness)
            shape.elasticity = 0.9
            shape.friction = 0.5
            shape.collision_type = 3  # Type 3 = mur
            self.space.add(body, shape)
    
    def setup_collision_handlers(self):
        """Configure les gestionnaires de collision (optimisés et fiables)"""
        # Réinitialiser les gestionnaires existants s'il y en a
        if hasattr(self, '_collision_handlers'):
            for handler in self._collision_handlers:
                self.space.remove_collision_handler(handler[0], handler[1])
        
        self._collision_handlers = []
        
        # Collision entre balles et cibles
        handler_ball_target = self.space.add_collision_handler(1, 2)
        handler_ball_target.begin = self.on_ball_hit_target
        self._collision_handlers.append((1, 2))
        
        # Collision entre balles et murs
        handler_ball_wall = self.space.add_collision_handler(1, 3)
        handler_ball_wall.begin = self.on_ball_hit_wall
        self._collision_handlers.append((1, 3))
        
        # Collision entre balles
        handler_ball_ball = self.space.add_collision_handler(1, 1)
        handler_ball_ball.begin = self.on_ball_hit_ball
        self._collision_handlers.append((1, 1))
        
        logger.info("Gestionnaires de collision configurés correctement")
    
    def on_ball_hit_target(self, arbiter, space, data):
        """Gère la collision entre une balle et une cible (optimisé)"""
        # Toujours jouer un son, même si la cible a déjà explosé
        ball_shape = None
        target_shape = None
        
        # Identifier les formes impliquées
        for shape in arbiter.shapes:
            if shape.collision_type == 1:
                ball_shape = shape
            elif shape.collision_type == 2:
                target_shape = shape
        
        if not ball_shape or not target_shape:
            return True  # Continuer avec la collision normale
        
        # Trouver la cible et la balle correspondantes
        target_found = None
        ball_found = None
        
        for target in self.targets:
            if target["shape"] == target_shape:
                target_found = target
                break
                
        for ball in self.balls:
            if ball["shape"] == ball_shape:
                ball_found = ball
                break
        
        if not target_found or not ball_found:
            return True  # Continuer avec la collision normale
        
        # Toujours jouer un son, même si la cible a déjà explosé
        pos = target_found["body"].position
        self.add_sound_event("explosion", (pos.x, pos.y), size="medium")
        
        # Faire exploser la cible si ce n'est pas déjà fait
        if not target_found["exploded"]:
            target_found["exploded"] = True
            
            # Créer des particules d'explosion
            num_particles = min(random.randint(15, 25), self.max_particles - len(self.particles))
            if num_particles > 0:
                for _ in range(num_particles):
                    self.add_particle(pos.x, pos.y, target_found["color"])
            
            # Ajouter une impulsion à la balle
            ball_pos = ball_found["body"].position
            direction_x = ball_pos.x - pos.x
            direction_y = ball_pos.y - pos.y
            
            # Normaliser pour obtenir la direction (évitant la division par zéro)
            length = max(1.0, (direction_x**2 + direction_y**2)**0.5)
            impulse_x = direction_x / length * 1000
            impulse_y = direction_y / length * 1000
            
            # Appliquer l'impulsion
            ball_found["body"].apply_impulse_at_local_point((impulse_x, impulse_y))
        
        return True

    def on_ball_hit_wall(self, arbiter, space, data):
        """Gère la collision entre une balle et un mur (optimisé)"""
        # TOUJOURS jouer un son pour chaque collision avec un mur
        ball_shape = None
        
        # Identifier la balle impliquée
        for shape in arbiter.shapes:
            if shape.collision_type == 1:
                ball_shape = shape
                break
        
        if not ball_shape:
            return True  # Continuer avec la collision normale
        
        # Récupérer la balle
        ball_found = None
        for ball in self.balls:
            if ball["shape"] == ball_shape:
                ball_found = ball
                break
        
        if not ball_found:
            return True  # Continuer avec la collision normale
        
        # Calculer la force de l'impact (arrondie)
        velocity = ball_found["body"].velocity
        velocity_magnitude = max(100, int((velocity.x**2 + velocity.y**2)**0.5))  # Au moins 100 pour toujours avoir du son
        
        # Jouer un son à chaque collision
        note_index = 0
        if self.current_melody and len(self.current_melody) > 0:
            note_index = min(int(velocity_magnitude / 200), len(self.current_melody) - 1)
        else:
            note_index = random.randint(0, 6)
        
        octave = min(int(velocity_magnitude / 600), 2)  # 0, 1 ou 2 selon la vitesse
        
        # Position pour l'effet sonore
        pos = ball_found["body"].position
        self.add_sound_event("note", (pos.x, pos.y), note=note_index, octave=octave)
        
        return True

    def on_ball_hit_ball(self, arbiter, space, data):
        """Gère la collision entre deux balles (optimisé, toujours avec son)"""
        # TOUJOURS jouer un son pour les collisions entre balles
        shapes = arbiter.shapes
        
        if len(shapes) < 2:
            return True  # Continuer avec la collision normale
        
        # Récupérer les balles impliquées
        balls_involved = []
        for shape in shapes:
            for ball in self.balls:
                if ball["shape"] == shape:
                    balls_involved.append(ball)
        
        if len(balls_involved) < 2:
            return True  # Continuer avec la collision normale
        
        # Calculer la vitesse totale (pour la tonalité)
        total_velocity = 0
        for ball in balls_involved:
            velocity = ball["body"].velocity
            velocity_magnitude = int((velocity.x**2 + velocity.y**2)**0.5)
            total_velocity += velocity_magnitude
        
        # Mapper la vitesse totale à une note (avec valeur minimale pour garantir un son)
        total_velocity = max(300, total_velocity)
        
        if self.current_melody and len(self.current_melody) > 0:
            note_index = min(int(total_velocity / 300), len(self.current_melody) - 1)
        else:
            note_index = random.randint(0, 6)
        
        # Position moyenne des balles
        pos_x = sum(ball["body"].position.x for ball in balls_involved) / len(balls_involved)
        pos_y = sum(ball["body"].position.y for ball in balls_involved) / len(balls_involved)
        
        # Ajouter l'événement sonore (toujours)
        self.add_sound_event("note", (pos_x, pos_y), note=note_index)
        
        return True

    def add_random_ball(self):
        """Ajoute une balle avec des paramètres aléatoires (optimisé)"""
        # Limiter le nombre total de balles
        if len(self.balls) >= self.max_balls:
            # Supprimer la balle la plus ancienne
            if self.balls:
                oldest_ball = self.balls[0]
                self.space.remove(oldest_ball["body"], oldest_ball["shape"])
                self.balls.pop(0)
        
        # Position (arrondie)
        x = int(random.uniform(self.width * 0.1, self.width * 0.9))
        y = -50  # Apparaît au-dessus de l'écran
        
        # Taille et masse (arrondies)
        radius = int(random.uniform(20, 50))
        mass = int(radius * 0.2)
        
        # Vitesse initiale (arrondie)
        vx = int(random.uniform(-300, 300))
        vy = int(random.uniform(100, 300))
        
        # Couleur depuis le cache
        color_hex = random.choice(self.color_palette)
        color_rgb = self.color_rgb_cache[color_hex]
        
        # Créer la balle
        body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
        body.position = (x, y)
        body.velocity = (vx, vy)
        
        shape = pymunk.Circle(body, radius)
        shape.elasticity = 0.95
        shape.friction = 0.2
        shape.collision_type = 1  # Type 1 = balle
        
        self.space.add(body, shape)
        
        # Ajouter à la liste des balles
        self.balls.append({
            "body": body,
            "shape": shape,
            "radius": radius,
            "color": color_rgb,
            "trail": []  # Pour la traînée (réduite pour optimisation)
        })
    
    def add_random_target(self):
        """Ajoute une cible statique avec des paramètres aléatoires (optimisé)"""
        # Limiter le nombre total de cibles
        if len(self.targets) >= self.max_targets:
            return
            
        # Position (arrondie)
        margin = 100
        x = int(random.uniform(margin, self.width - margin))
        y = int(random.uniform(margin, self.height - margin))
        
        # Éviter le chevauchement avec d'autres cibles (optimisé)
        for target in self.targets:
            # Calcul de distance simplifié et arrondi
            target_pos = target["body"].position
            dx = x - target_pos.x
            dy = y - target_pos.y
            dist_squared = dx*dx + dy*dy
            
            if dist_squared < 22500:  # 150² = 22500, évite la racine carrée
                return self.add_random_target()
        
        # Taille (arrondie)
        radius = int(random.uniform(40, 80))
        
        # Couleur depuis le cache
        color_hex = random.choice(self.color_palette)
        color_rgb = self.color_rgb_cache[color_hex]
        
        # Créer le corps statique
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = (x, y)
        
        shape = pymunk.Circle(body, radius)
        shape.elasticity = 0.9
        shape.friction = 0.4
        shape.collision_type = 2  # Type 2 = cible
        
        self.space.add(body, shape)
        
        # Ajouter à la liste des cibles
        target = {
            "body": body,
            "shape": shape,
            "radius": radius,
            "color": color_rgb,
            "exploded": False,
            "explosion_progress": 0,
            "explosion_duration": 0.5,  # secondes
        }
        self.targets.append(target)
    
    def add_particle(self, x, y, color):
        """Ajoute une particule pour les effets visuels (optimisé)"""
        # Limiter le nombre total de particules
        if len(self.particles) >= self.max_particles:
            return
            
        # Paramètres aléatoires (arrondis)
        size = int(random.uniform(3, 8))
        angle = random.uniform(0, 6.28)  # 2*pi approx.
        speed = int(random.uniform(100, 300))
        
        # Calculs simplifiés et arrondis
        vx = int(np.cos(angle) * speed)
        vy = int(np.sin(angle) * speed)
        lifetime = round(random.uniform(0.5, 1.5), 1)  # Arrondi à 1 décimale
        
        # Ajouter à la liste des particules
        self.particles.append({
            "x": int(x),
            "y": int(y),
            "vx": vx,
            "vy": vy,
            "size": size,
            "current_size": size,
            "color": color,
            "lifetime": lifetime,
            "time_alive": 0
        })
    
    def add_sound_event(self, sound_type, position, **params):
        """Ajoute un événement sonore à la liste"""
        # Convertir position tuple en coordonnées
        if isinstance(position, tuple):
            pos_x, pos_y = position
        else:
            pos_x, pos_y = position.x, position.y
            
        # Enregistrer l'événement pour la génération audio ultérieure
        event = {
            "type": sound_type,
            "position": (int(pos_x), int(pos_y)),  # Arrondir les coordonnées
            "frame": self.current_frame,
            "time": round(self.current_frame / self.fps, 2),  # Arrondir à 2 décimales
            "params": params
        }
        
        self.sound_events.append(event)
    
    def trigger_special_event(self):
        """Déclenche un événement spécial aléatoire (optimisé)"""
        # Liste réduite d'événements pour optimisation
        event_type = random.choice([
            "ball_shower",
            "explode_all",
            "big_ball"
        ])
        
        if event_type == "ball_shower":
            # Faire pleuvoir plusieurs balles (nombre réduit)
            for _ in range(random.randint(3, 5)):
                self.add_random_ball()
                
        elif event_type == "explode_all":
            # Faire exploser toutes les cibles
            exploded_count = 0
            for target in self.targets:
                if not target["exploded"] and random.random() < 0.7:  # 70% de chance d'exploser
                    target["exploded"] = True
                    exploded_count += 1
                    
                    # Ajouter un son d'explosion
                    pos = target["body"].position
                    self.add_sound_event("explosion", (pos.x, pos.y), size="large")
                    
                    # Créer des particules d'explosion (nombre réduit)
                    particles_per_target = min(10, (self.max_particles - len(self.particles)) // max(1, exploded_count))
                    for _ in range(particles_per_target):
                        self.add_particle(pos.x, pos.y, target["color"])
                        
        elif event_type == "big_ball":
            # Créer une grosse balle
            x = int(random.uniform(self.width * 0.1, self.width * 0.9))
            y = -100
            radius = int(random.uniform(80, 120))
            mass = int(radius * 0.5)
            
            vx = int(random.uniform(-200, 200))
            vy = int(random.uniform(100, 300))
            
            # Jouer une note grave
            self.add_sound_event("note", (x, y), note=0, octave=0)
            
            # Couleur depuis le cache
            color_hex = random.choice(self.color_palette)
            color_rgb = self.color_rgb_cache[color_hex]
            
            # Créer la balle
            body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
            body.position = (x, y)
            body.velocity = (vx, vy)
            
            shape = pymunk.Circle(body, radius)
            shape.elasticity = 0.95
            shape.friction = 0.2
            shape.collision_type = 1
            
            self.space.add(body, shape)
            
            # Ajouter à la liste des balles
            self.balls.append({
                "body": body,
                "shape": shape,
                "radius": radius,
                "color": color_rgb,
                "trail": []
            })
    
    def update_simulation(self, dt):
        """Met à jour tous les objets de la simulation (optimisé)"""
        try:
            # Mettre à jour les balles
            for ball in self.balls:
                # Ajouter la position à la traînée (fréquence réduite)
                if self.current_frame % 2 == 0:  # Mettre à jour tous les 2 frames
                    pos_x, pos_y = int(ball["body"].position.x), int(ball["body"].position.y)
                    ball["trail"].append((pos_x, pos_y))
                    
                    # Limiter la longueur de la traînée
                    if len(ball["trail"]) > self.trail_length:
                        ball["trail"].pop(0)
            
            # Mettre à jour les particules (par lots pour optimisation)
            if self.current_frame % self.update_frequency == 0 and self.particles:
                # S'assurer que chunk_size est au moins 1
                chunk_size = max(1, min(self.particle_batch_size, len(self.particles)))
                
                for i in range(0, len(self.particles), chunk_size):
                    batch = self.particles[i:min(i+chunk_size, len(self.particles))]
                    
                    for particle in batch:
                        # Mise à jour simplifiée
                        particle["x"] += int(particle["vx"] * dt)
                        particle["y"] += int(particle["vy"] * dt)
                        particle["vy"] += int(self.gravity * 0.3 * dt)  # Gravité légère
                        particle["time_alive"] += dt
                        
                        # Mise à jour de la taille (calculée une fois sur deux)
                        if self.current_frame % 4 == 0:
                            factor = max(0, 1 - (particle["time_alive"] / particle["lifetime"]))
                            particle["current_size"] = particle["size"] * factor
            
            # Supprimer les particules mortes (lot complet)
            self.particles = [p for p in self.particles if p["time_alive"] < p["lifetime"]]
            
            # Mettre à jour les cibles (optimisé)
            for target in self.targets:
                if target["exploded"] and target["explosion_progress"] < 1.0:
                    target["explosion_progress"] += dt / target["explosion_duration"]
            
            # Supprimer les cibles complètement explosées
            self.targets = [t for t in self.targets if not (t["exploded"] and t["explosion_progress"] >= 1.0)]
            
            # Supprimer les balles sorties de l'écran (optimisé)
            balls_to_remove = []
            for ball in self.balls:
                pos = ball["body"].position
                # Vérification simplifiée
                if pos.y > self.height + 100 or pos.x < -100 or pos.x > self.width + 100:
                    balls_to_remove.append(ball)
                    
            for ball in balls_to_remove:
                self.space.remove(ball["body"], ball["shape"])
                self.balls.remove(ball)
            
            # Mettre à jour les effets spéciaux
            effects_to_remove = []
            for effect in self.special_effects:
                if self.current_frame >= effect["end_frame"]:
                    # Appliquer l'effet de fin
                    if effect["type"] == "restore_gravity":
                        self.space.gravity = effect["original_gravity"]
                    elif effect["type"] == "restore_palette":
                        self.color_palette = effect["original_palette"]
                        self.color_rgb_cache = {color: self.hex_to_rgb(color) for color in self.color_palette}
                    
                    effects_to_remove.append(effect)
            
            # Supprimer les effets terminés
            for effect in effects_to_remove:
                self.special_effects.remove(effect)
            
            # Mettre à jour la physique
            self.space.step(dt)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise à jour simulation: {e}")
            return False
    
    def render_frame(self, frame_number):
        """Rend un frame de la simulation (optimisé)"""
        try:
            # Créer une surface pour le rendu
            surface = pygame.Surface((self.width, self.height))
            
            # Remplir l'arrière-plan avec une couleur unie (optimisé)
            surface.fill((10, 10, 15))
            
            # Dessiner un arrière-plan dégradé (simplifié)
            if self.render_quality != 'low':
                # Dessiner un arrière-plan dégradé (optimisé)
                gradient_step = 4 if self.render_quality == 'medium' else 2  # Optimisation
                gradient_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                color1 = (15, 10, 30)
                color2 = (30, 20, 40)
                
                for y in range(0, self.height, gradient_step):
                    # Calculer la couleur interpolée (simplifié)
                    t = y / self.height
                    r = int(color1[0] * (1 - t) + color2[0] * t)
                    g = int(color1[1] * (1 - t) + color2[1] * t)
                    b = int(color1[2] * (1 - t) + color2[2] * t)
                    
                    pygame.draw.line(gradient_surface, (r, g, b), (0, y), (self.width, y), gradient_step)
                    
                surface.blit(gradient_surface, (0, 0))
            
            # Ajouter un effet de grille (simplifié)
            if self.use_grid and self.render_quality != 'low':
                grid_spacing = 200 if self.render_quality == 'medium' else 100
                grid_color = (50, 50, 70, 20)  # Avec transparence
                
                # Vérifier si une grille est en cache
                grid_key = f"grid_{grid_spacing}"
                if grid_key not in self.surface_cache:
                    # Créer une nouvelle grille
                    grid_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    
                    for x in range(0, self.width, grid_spacing):
                        pygame.draw.line(grid_surface, grid_color, (x, 0), (x, self.height))
                        
                    for y in range(0, self.height, grid_spacing):
                        pygame.draw.line(grid_surface, grid_color, (0, y), (self.width, y))
                        
                    # Mettre en cache pour réutilisation
                    self.surface_cache[grid_key] = grid_surface
                
                # Utiliser la grille du cache
                surface.blit(self.surface_cache[grid_key], (0, 0))
            
            # Dessiner les cibles
            for target in self.targets:
                if not target["exploded"]:
                    # Dessiner le cercle (version optimisée)
                    pos = target["body"].position
                    radius = target["radius"]
                    
                    # Version simplifiée pour 'low'
                    if self.render_quality == 'low':
                        pygame.draw.circle(surface, target["color"], (int(pos.x), int(pos.y)), int(radius))
                    else:
                        # Effet de lueur (version simplifiée)
                        glow_radius = int(radius * 1.1)
                        
                        # Vérifier si une lueur similaire est en cache
                        glow_key = f"glow_{glow_radius}_{target['color']}"
                        if glow_key not in self.surface_cache:
                            # Créer une nouvelle lueur
                            glow = pygame.Surface((int(glow_radius * 2), int(glow_radius * 2)), pygame.SRCALPHA)
                            r, g, b = target["color"]
                            pygame.draw.circle(glow, (r, g, b, 100), (glow_radius, glow_radius), glow_radius)
                            
                            # Mettre en cache
                            if len(self.surface_cache) < 50:  # Limiter la taille du cache
                                self.surface_cache[glow_key] = glow
                        else:
                            # Utiliser la lueur du cache
                            glow = self.surface_cache[glow_key]
                        
                        # Positionner la lueur
                        surface.blit(glow, (int(pos.x - glow_radius), int(pos.y - glow_radius)))
                        
                        # Cercle principal
                        pygame.draw.circle(surface, target["color"], (int(pos.x), int(pos.y)), int(radius))
                        
                        # Reflet (effet 3D simplifié)
                        if self.render_quality == 'high':
                            highlight_pos = (int(pos.x - radius * 0.3), int(pos.y - radius * 0.3))
                            highlight_size = int(radius * 0.4)
                            # Couleur de surbrillance simplifiée
                            highlight_color = (min(255, target["color"][0] + 40), 
                                              min(255, target["color"][1] + 40), 
                                              min(255, target["color"][2] + 40))
                            pygame.draw.circle(surface, highlight_color, highlight_pos, highlight_size)
                
                elif target["explosion_progress"] < 1.0:
                    # Animation d'explosion (simplifiée)
                    pos = target["body"].position
                    progress = target["explosion_progress"]
                    
                    # Version très simplifiée pour 'low'
                    if self.render_quality == 'low':
                        expanded_radius = int(target["radius"] * (1 + progress))
                        color = target["color"]
                        pygame.draw.circle(surface, color, (int(pos.x), int(pos.y)), expanded_radius, 1)
                    else:
                        # Cercle qui se dilate et s'estompe
                        alpha = int(255 * (1 - progress))
                        expanded_radius = int(target["radius"] * (1 + progress * 2))
                        
                        # Surface avec transparence
                        s = pygame.Surface((expanded_radius * 2, expanded_radius * 2), pygame.SRCALPHA)
                        r, g, b = target["color"]
                        pygame.draw.circle(s, (r, g, b, alpha), 
                                         (expanded_radius, expanded_radius), 
                                         expanded_radius)
                        
                        surface.blit(s, (int(pos.x - expanded_radius), int(pos.y - expanded_radius)))
            
            # Dessiner les balles
            for ball in self.balls:
                # Dessiner la traînée (simplifiée)
                if len(ball["trail"]) > 1 and self.render_quality != 'low':
                    # Éviter une division par zéro dans le pas
                    step = max(1, 2 if self.render_quality == 'medium' else 1)
                    
                    # Assurer qu'il y a suffisamment d'éléments dans la traînée pour le pas
                    if len(ball["trail"]) > step:
                        for i in range(0, len(ball["trail"]) - step, step):
                            # Éviter l'index out of range
                            if i+step < len(ball["trail"]):
                                alpha = int(255 * (i / len(ball["trail"])))
                                trail_width = max(1, int(ball["radius"] * (i / len(ball["trail"])) * 1.2))
                                
                                r, g, b = ball["color"]
                                # Créer une surface simplifiée pour le segment
                                line_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                                pygame.draw.line(line_surface, 
                                              (r, g, b, alpha), 
                                              ball["trail"][i], 
                                              ball["trail"][i+step], 
                                              trail_width)
                                surface.blit(line_surface, (0, 0))
                
                # Dessiner la balle
                pos = ball["body"].position
                radius = ball["radius"]
                
                # Version simplifiée pour 'low'
                if self.render_quality == 'low':
                    pygame.draw.circle(surface, ball["color"], (int(pos.x), int(pos.y)), int(radius))
                else:
                    # Effet de lueur (simplifié)
                    glow_radius = int(radius * 1.1)
                    glow = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                    r, g, b = ball["color"]
                    pygame.draw.circle(glow, (r, g, b, 100), (glow_radius, glow_radius), glow_radius)
                    
                    surface.blit(glow, (int(pos.x - glow_radius), int(pos.y - glow_radius)))
                    
                    # Dessiner la balle
                    pygame.draw.circle(surface, ball["color"], (int(pos.x), int(pos.y)), int(radius))
                    
                    # Ajouter un reflet (simplifié)
                    if self.render_quality == 'high':
                        highlight_pos = (int(pos.x - radius * 0.3), int(pos.y - radius * 0.3))
                        highlight_size = int(radius * 0.3)
                        pygame.draw.circle(surface, (255, 255, 255), highlight_pos, highlight_size)
            
            # Dessiner les particules (optimisé, par lots)
            if self.render_quality != 'low':
                # Dessiner par lots pour optimisation
                batch_size = min(50, len(self.particles))
                # Éviter une division par zéro
                if batch_size > 0:
                    for i in range(0, len(self.particles), batch_size):
                        # Éviter l'index out of range
                        end_idx = min(i+batch_size, len(self.particles))
                        particles_batch = self.particles[i:end_idx]
                        
                        for particle in particles_batch:
                            # Dessiner la particule (simplifié)
                            size = int(particle["current_size"])
                            if size <= 0:
                                continue
                                
                            # Calculer alpha
                            alpha = int(255 * (1 - particle["time_alive"] / particle["lifetime"]))
                            
                            # Surface simplifiée
                            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                            r, g, b = particle["color"]
                            pygame.draw.circle(s, (r, g, b, alpha), (size, size), size)
                            
                            x, y = int(particle["x"]), int(particle["y"])
                            surface.blit(s, (x - size, y - size))
            else:
                # Version encore plus simplifiée pour 'low'
                # Dessiner par lots pour optimisation
                draw_step = max(1, 3)  # Dessiner 1 particule sur 3, minimum 1
                if len(self.particles) > 0:
                    for i in range(0, len(self.particles), draw_step):
                        if i < len(self.particles):
                            particle = self.particles[i]
                            size = int(particle["current_size"])
                            if size > 0:
                                x, y = int(particle["x"]), int(particle["y"])
                                pygame.draw.circle(surface, particle["color"], (x, y), size)
            
            # Enregistrer le frame
            frame_path = os.path.join(self.frames_dir, f"frame_{frame_number:06d}.png")
            pygame.image.save(surface, frame_path)
            
            return frame_path
            
        except Exception as e:
            logger.error(f"Erreur rendu frame {frame_number}: {e}")
            return None
    
    def run_simulation(self):
        """Exécute la simulation complète (optimisé)"""
        logger.info("Démarrage de la simulation optimisée...")
        
        try:
            # Initialiser pygame
            pygame.init()
            
            # Réinitialiser les listes
            self.balls = []
            self.targets = []
            self.particles = []
            self.special_effects = []
            self.sound_events = []
            
            # Initialiser la physique
            if not self.initialize_physics():
                logger.error("Erreur lors de l'initialisation de la physique")
                return False
            
            # Générer les sons
            self.generate_sounds()
            
            # Liste pour stocker les événements sonores
            self.sound_events = []
            
            # Réinitialiser le compteur de frames
            self.current_frame = 0
            
            # Marquer la simulation comme en cours
            self.simulation_running = True
            
            # Configurer les temps pour les événements
            next_ball_time = 0
            next_target_time = 1.0
            next_event_time = 5.0
            
            # Déterminer le pas de temps
            dt = 1.0 / self.fps
            
            # Configurer la qualité de rendu en fonction de la résolution
            if self.width * self.height > 2000000:  # Vidéo HD ou plus
                self.render_quality = 'medium'
            elif self.width * self.height > 800000:  # Vidéo SD
                self.render_quality = 'high'
            else:
                self.render_quality = 'high'  # Petites vidéos
            
            logger.info(f"Génération de {self.total_frames} frames (qualité: {self.render_quality})...")
            start_time = time.time()
            last_progress_time = start_time
            
            while self.current_frame < self.total_frames and self.simulation_running:
                # Calculer le temps actuel
                current_time = self.current_frame * dt
                
                # Événements périodiques (fréquence optimisée)
                if current_time >= next_ball_time:
                    self.add_random_ball()
                    next_ball_time = current_time + random.uniform(0.8, 2.4)  # Légèrement plus espacé
                    
                if current_time >= next_target_time and len(self.targets) < self.max_targets:
                    self.add_random_target()
                    next_target_time = current_time + random.uniform(1.5, 3.5)  # Plus espacé
                    
                if current_time >= next_event_time:
                    self.trigger_special_event()
                    next_event_time = current_time + random.uniform(6.0, 12.0)  # Plus espacé
                
                # Mettre à jour la simulation
                if not self.update_simulation(dt):
                    logger.error(f"Erreur de mise à jour à la frame {self.current_frame}")
                    break
                
                # Rendre le frame
                frame_path = self.render_frame(self.current_frame)
                if not frame_path:
                    logger.error(f"Erreur de rendu à la frame {self.current_frame}")
                    break
                
                # Incrémenter le compteur de frames
                self.current_frame += 1
                
                # Afficher la progression (moins fréquemment pour optimisation)
                current_time = time.time()
                if self.current_frame % 60 == 0 or self.current_frame == self.total_frames - 1 or current_time - last_progress_time > 5:
                    elapsed = current_time - start_time
                    progress = self.current_frame / self.total_frames
                    eta = (elapsed / progress - elapsed) if progress > 0 else 0
                    fps = self.current_frame / max(1, elapsed)
                    
                    logger.info(f"Progression: {self.current_frame}/{self.total_frames} frames ({progress*100:.1f}%, {fps:.1f} FPS, ETA: {eta:.1f}s)")
                    last_progress_time = current_time
            
            # Marquer la simulation comme terminée
            self.simulation_running = False
            
            # Nettoyer le cache
            self.surface_cache.clear()
            
            # Fermer pygame
            pygame.quit()
            
            # Vérifier si la simulation a été complétée
            if self.current_frame >= self.total_frames:
                logger.info("Simulation optimisée terminée avec succès")
                return True
            else:
                logger.warning(f"Simulation terminée prématurément à la frame {self.current_frame}/{self.total_frames}")
                return False
                
        except Exception as e:
            logger.exception(f"Erreur lors de la simulation: {e}")
            try:
                pygame.quit()
            except:
                pass
            
            self.simulation_running = False
            return False
    
    def generate_video(self):
        """Génère la vidéo finale à partir des frames et des sons (optimisé)"""
        logger.info("Génération de la vidéo finale...")
        
        # Si pas de frames générés, échec
        if self.current_frame == 0:
            logger.error("Aucune frame générée, impossible de créer la vidéo")
            return None
        
        try:
            # Créer la vidéo à partir des frames
            frame_pattern = os.path.join(self.frames_dir, "frame_%06d.png")
            
            # Utiliser MoviePy avec options optimisées
            clip = ImageSequenceClip(self.frames_dir, fps=self.fps)
            
            # Ajouter l'audio à la vidéo si disponible
            if self.output_audio_file and os.path.exists(self.output_audio_file):
                try:
                    audio_clip = AudioFileClip(self.output_audio_file)
                    clip = clip.with_audio(audio_clip)
                    logger.info(f"Piste audio ajoutée: {self.output_audio_file}")
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout de l'audio: {e}")
            
            # Écrire la vidéo avec paramètres optimisés
            logger.info("Écriture de la vidéo en cours... (cela peut prendre quelques minutes)")
            clip.write_videofile(
                self.output_path,
                codec='libx264',
                audio_codec='aac',
                fps=self.fps,
                threads=8,  # Augmenter le nombre de threads
                preset='faster',  # Encoder plus rapide
                bitrate='3000k'   # Qualité raisonnable
            )
            
            logger.info(f"Vidéo créée avec succès: {self.output_path}")
            
            # Fermer les clips pour libérer les ressources
            clip.close()
            
            return self.output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la vidéo: {e}")
            
            # Utiliser une méthode alternative (ffmpeg directement)
            try:
                import subprocess
                
                # Trouver le chemin de ffmpeg
                ffmpeg_paths = [
                    "ffmpeg",
                    "ffmpeg.exe",
                    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                    "/usr/bin/ffmpeg",
                    "/usr/local/bin/ffmpeg"
                ]
                
                ffmpeg_path = None
                for path in ffmpeg_paths:
                    try:
                        if os.path.exists(path):
                            ffmpeg_path = path
                            break
                        elif path == "ffmpeg" or path == "ffmpeg.exe":
                            subprocess.run([path, "-version"], check=True, capture_output=True)
                            ffmpeg_path = path
                            break
                    except:
                        continue
                
                if not ffmpeg_path:
                    logger.error("ffmpeg non trouvé, impossible de générer la vidéo")
                    return None
                
                # Construire la commande ffmpeg optimisée
                cmd = [
                    ffmpeg_path, '-y',
                    '-framerate', str(self.fps),
                    '-i', frame_pattern,
                    '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p',
                    '-r', str(self.fps),
                    '-crf', '28',  # Qualité plus basse pour vitesse (23 est par défaut)
                    '-preset', 'veryfast',  # Plus rapide (medium est par défaut)
                    '-tune', 'fastdecode'
                ]
                
                # Ajouter l'audio si disponible
                if self.output_audio_file and os.path.exists(self.output_audio_file):
                    cmd.extend([
                        '-i', self.output_audio_file,
                        '-c:a', 'aac',
                        '-b:a', '128k',  # Bitrate audio réduit
                        '-shortest'
                    ])
                
                # Ajouter le fichier de sortie
                cmd.append(self.output_path)
                
                logger.info(f"Exécution commande ffmpeg: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
                
                logger.info(f"Vidéo créée avec succès (méthode alternative): {self.output_path}")
                return self.output_path
                
            except Exception as e:
                logger.error(f"Erreur lors de la génération de la vidéo (méthode alternative): {e}")
                return None
    
    def get_output_path(self):
        """Retourne le chemin de la vidéo générée"""
        return self.output_path