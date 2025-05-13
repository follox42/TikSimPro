"""
TikSim Pro - Système automatisé de création et publication de contenu viral pour TikTok
=====================================================================================
Ce système intelligent scrape TikTok, analyse les tendances, génère des simulations physiques musicales,
et publie automatiquement du contenu optimisé pour la viralité.
"""

import os
import time
import random
import json
import schedule
import logging
import numpy as np
import pygame
import pymunk
import cv2
import requests
from selenium import webdriver
from bs4 import BeautifulSoup
from PIL import Image, ImageFont, ImageDraw
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, TextClip, ImageSequenceClip, concatenate_audioclips, concatenate_videoclips, CompositeAudioClip, AudioFileClip
from threading import Thread
from datetime import datetime
import yt_dlp
from pathlib import Path
import librosa
import numpy as np
from scipy.io import wavfile
from youtubesearchpython import VideosSearch 
from tikotokscraper import TikTokScraper

# import tensorflow as tf

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tiksim.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("TikSimPro")

class AdvancedPhysicsSimulation:
    """
    Module de simulation physique avancée avec effets visuels et sonores
    """
    
    def __init__(self, width=1080, height=1920, fps=60, duration=61, output_path="output.mp4"):
        """
        Initialise la simulation physique avancée
        
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
        
        # Frames à générer
        self.total_frames = int(duration * fps)
        logger.info(f"Frames total a generer: {self.total_frames}")
        # Paramètres physiques
        self.gravity = 1000
        
        # Palettes de couleurs
        self.color_palette = ["#FF0050", "#00F2EA", "#FFFFFF", "#FE2C55"]
        
        # Répertoires de travail
        self.temp_dir = os.path.join(os.getcwd(), "temp")
        self.frames_dir = os.path.join(self.temp_dir, "frames")
        self.sounds_dir = os.path.join(self.temp_dir, "sounds")
        
        # Créer les répertoires
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.frames_dir, exist_ok=True)
        os.makedirs(self.sounds_dir, exist_ok=True)
        
        logger.info(f"Les frames seront enregistrées dans: {self.frames_dir}")

        # Paramètres de timing
        self.beat_frequency = 1.0  # secondes entre les beats musicaux
        
        # Objets de la simulation
        self.balls = []
        self.targets = []
        self.particles = []
        
        # Paramètres dynamiques pour les événements
        self.next_ball_time = 0
        self.next_target_time = 0
        self.next_event_time = 0
        
        # Musique et sons
        self.notes = []
        self.current_melody = []
        
        # Événements spéciaux
        self.special_effects = []
        
        logger.info(f"Simulation initialisée: {width}x{height}, {fps} FPS, {duration}s")
    
    def set_color_palette(self, palette):
        """Définit la palette de couleurs à utiliser"""
        if isinstance(palette, list) and len(palette) > 0:
            self.color_palette = palette
            logger.info(f"Palette de couleurs définie: {palette}")
    
    def set_melody(self, melody_notes):
        """Définit la mélodie à jouer sur les rebonds"""
        self.current_melody = melody_notes
        logger.info(f"Mélodie définie: {len(melody_notes)} notes")
    
    def set_beat_frequency(self, frequency):
        """Définit la fréquence des beats musicaux"""
        self.beat_frequency = frequency
        logger.info(f"Fréquence des beats définie: {frequency}s")
    
    def hex_to_rgb(self, hex_color):
        """Convertit une couleur hexadécimale en RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def generate_sounds(self):
        """Génère les sons pour la simulation"""
        logger.info("Génération des sons...")
        
        # Fréquences de base des notes (gamme de Do majeur)
        note_freqs = {
            0: 261.63,  # Do
            1: 293.66,  # Ré
            2: 329.63,  # Mi
            3: 349.23,  # Fa
            4: 392.00,  # Sol
            5: 440.00,  # La
            6: 493.88,  # Si
        }
        
        # Paramètres pour la génération de notes
        sample_rate = 44100
        note_duration = 0.5  # secondes
        
        # Générer chaque note
        for note_idx, freq_key in enumerate(note_freqs):
            base_freq = note_freqs[freq_key]
            
            # Générer pour différentes octaves
            for octave, factor in enumerate([0.5, 1.0, 2.0]):
                freq = base_freq * factor
                note_path = os.path.join(self.sounds_dir, f"note_{note_idx}_oct{octave}.wav")
                
                # Vérifier si la note existe déjà
                if not os.path.exists(note_path):
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
                    
                    # Générer le son
                    for i in range(num_samples):
                        t = i / sample_rate
                        mod = 1.0 + 0.005 * np.sin(2 * np.pi * 5 * t)
                        samples[i] = 0.8 * np.sin(2 * np.pi * freq * mod * t) * envelope[i]
                    
                    # Ajouter des harmoniques
                    for harmonic, factor in [(2, 0.3), (3, 0.2), (4, 0.1)]:
                        harmonic_freq = freq * harmonic
                        for i in range(num_samples):
                            t = i / sample_rate
                            samples[i] += 0.8 * factor * np.sin(2 * np.pi * harmonic_freq * t) * envelope[i]
                    
                    # Normaliser
                    max_val = np.max(np.abs(samples))
                    if max_val > 0:
                        samples = samples / max_val * 0.9
                    
                    # Convertir en 16 bits
                    samples = (samples * 32767).astype(np.int16)
                    
                    # Créer un fichier WAV stéréo
                    stereo_samples = np.column_stack((samples, samples))
                    
                    # Sauvegarder le fichier WAV
                    import wave
                    with wave.open(note_path, 'wb') as wf:
                        wf.setnchannels(2)
                        wf.setsampwidth(2)  # 16 bits
                        wf.setframerate(sample_rate)
                        wf.writeframes(stereo_samples.tobytes())
                
                self.notes.append((note_idx, octave, note_path))
        
        # Générer des sons d'explosion
        for size in ["small", "medium", "large"]:
            explosion_path = os.path.join(self.sounds_dir, f"explosion_{size}.wav")
            
            # Vérifier si le son existe déjà
            if os.path.exists(explosion_path):
                continue
            
            # Paramètres basés sur la taille
            if size == "small":
                base_freq = 100
                duration = 0.5
            elif size == "medium":
                base_freq = 80
                duration = 0.7
            else:  # large
                base_freq = 60
                duration = 1.0
            
            # Générer l'onde sonore
            num_samples = int(sample_rate * duration)
            samples = np.zeros(num_samples, dtype=np.float32)
            
            # Paramètres ADSR
            attack = 0.05
            decay = 0.2
            sustain_level = 0.4
            release = 0.75
            
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
            
            # Générer un son complexe pour l'explosion
            noise = np.random.uniform(-1, 1, num_samples)
            
            for i in range(num_samples):
                t = i / sample_rate
                # Base tone
                samples[i] = 0.7 * np.sin(2 * np.pi * base_freq * t) * envelope[i]
                # Noise component
                samples[i] += 0.5 * noise[i] * envelope[i]
                # Add harmonics and sub-harmonics
                samples[i] += 0.3 * np.sin(2 * np.pi * base_freq * 2 * t) * envelope[i]
                samples[i] += 0.2 * np.sin(2 * np.pi * base_freq * 0.5 * t) * envelope[i]
            
            # Normaliser
            max_val = np.max(np.abs(samples))
            if max_val > 0:
                samples = samples / max_val * 0.9
            
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
        
        logger.info(f"Sons générés: {len(self.notes)} notes")
    
    def render_audio_from_events(self, output_file="output_audio.wav"):
        """
        Génère la piste audio finale à partir des événements de la simulation
        (rebonds, explosions, etc.), et l'enregistre dans un fichier WAV.
        """
        logger.info("Génération de la piste audio à partir des événements...")

        sample_rate = 44100
        total_duration = self.duration  # Durée de la vidéo = durée de l'audio
        num_samples = int(sample_rate * total_duration)

        # Timeline audio stéréo initialisée à 0
        audio_timeline = np.zeros((num_samples, 2), dtype=np.float32)

        # Charger et mixer chaque event
        for event in self.sound_events:
            time_offset = event["time"]
            event_type = event["type"]
            params = event["params"]

            # Choisir le fichier correspondant
            if event_type == "note":
                note_idx = params.get("note", 0)
                octave = params.get("octave", 1)
                note_file = os.path.join(self.sounds_dir, f"note_{note_idx}_oct{octave}.wav")
            elif event_type == "explosion":
                size = params.get("size", "medium")
                note_file = os.path.join(self.sounds_dir, f"explosion_{size}.wav")
            else:
                continue  # Inconnu, on skip

            if not os.path.exists(note_file):
                logger.warning(f"Fichier sonore introuvable: {note_file}")
                continue

            # Charger le son (mono ou stéréo)
            try:
                sr, sound_data = wavfile.read(note_file)

                # Normaliser en float32 [-1.0, 1.0]
                if sound_data.dtype == np.int16:
                    sound_data = sound_data.astype(np.float32) / 32767.0
                elif sound_data.dtype == np.int32:
                    sound_data = sound_data.astype(np.float32) / 2147483647.0
                elif sound_data.dtype == np.uint8:
                    sound_data = (sound_data.astype(np.float32) - 128) / 128.0

                # Si mono → stéréo
                if len(sound_data.shape) == 1:
                    sound_data = np.column_stack((sound_data, sound_data))

                # Position dans la timeline
                start_sample = int(time_offset * sample_rate)
                end_sample = start_sample + sound_data.shape[0]

                if start_sample >= num_samples:
                    continue  # Trop tard → skip

                if end_sample > num_samples:
                    sound_data = sound_data[:num_samples - start_sample]

                # Additionner le son sur la timeline
                audio_timeline[start_sample:start_sample+sound_data.shape[0]] += sound_data

            except Exception as e:
                logger.error(f"Erreur lecture {note_file}: {e}")
                continue

        # Normaliser l'audio final pour éviter les saturations
        max_val = np.max(np.abs(audio_timeline))
        if max_val > 1.0:
            audio_timeline = audio_timeline / max_val * 0.9

        # Convertir en int16
        audio_output = (audio_timeline * 32767).astype(np.int16)

        # Sauvegarder le fichier WAV
        wavfile.write(output_file, sample_rate, audio_output)

        logger.info(f"Piste audio générée avec succès: {output_file}")
        return output_file

    def initialize_physics(self):
        """Initialise le monde physique et les objets"""
        logger.info("Initialisation de la physique...")
        
        # Initialiser pymunk
        self.space = pymunk.Space()
        self.space.gravity = (0, self.gravity)
        
        # Créer les murs (sol et côtés)
        self.create_boundaries()
        
        # Configuration des collisions
        self.setup_collision_handlers()
        
        # Ajouter quelques objets initiaux
        for _ in range(10):
            self.add_random_target()
        
        logger.info("Physique initialisée")
    
    def create_boundaries(self):
        """Crée les murs autour de l'écran"""
        # Épaisseur des murs
        thickness = 50
        
        # Créer les segments (haut, bas, gauche, droite)
        boundaries = [
            # Segment du bas
            [(0, self.height), (self.width, self.height), thickness],
            # Segment de gauche
            [(0, 0), (0, self.height), thickness],
            # Segment de droite
            [(self.width, 0), (self.width, self.height), thickness]
            # Pas de segment en haut pour laisser entrer les balles
        ]
        
        for boundary in boundaries:
            start, end, thickness = boundary
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            shape = pymunk.Segment(body, start, end, thickness)
            shape.elasticity = 0.9  # Rebondissant
            shape.friction = 0.5
            shape.collision_type = 3  # Type 3 = mur
            self.space.add(body, shape)
    
    def setup_collision_handlers(self):
        """Configure les gestionnaires de collision"""
        # Collision entre balles et cibles
        handler = self.space.add_collision_handler(1, 2)  # Types 1 (balle) et 2 (cible)
        handler.begin = self.on_ball_hit_target
        
        # Collision entre balles et murs
        handler_wall = self.space.add_collision_handler(1, 3)  # Types 1 (balle) et 3 (mur)
        handler_wall.begin = self.on_ball_hit_wall
        
        # Collision entre balles
        handler_balls = self.space.add_collision_handler(1, 1)  # Type 1 (balle) et 1 (balle)
        handler_balls.begin = self.on_ball_hit_ball
    
    def on_ball_hit_target(self, arbiter, space, data):
        """Gère la collision entre une balle et une cible"""
        # Récupérer les formes impliquées
        ball_shape, target_shape = arbiter.shapes
        
        # Trouver la cible correspondante
        for target in self.targets:
            if target["shape"] == target_shape and not target["exploded"]:
                # Faire exploser la cible
                target["explode"]()
                
                # Ajouter un effet sonore
                self.add_sound_event("explosion", target["body"].position, size="medium")
                
                # Créer des particules d'explosion
                num_particles = random.randint(30, 50)
                for _ in range(num_particles):
                    self.add_particle(
                        target["body"].position.x, 
                        target["body"].position.y,
                        target["color"]
                    )
                
                # Ajouter une impulsion à la balle
                ball = None
                for b in self.balls:
                    if b["shape"] == ball_shape:
                        ball = b
                        break
                
                if ball:
                    # Calculer la direction de rebond
                    direction = ball["body"].position - target["body"].position
                    impulse = direction.normalized() * 1000  # Force de l'impulsion
                    ball["body"].apply_impulse_at_local_point(impulse)
                
                break
        
        # Continuer avec la collision normale
        return True
    
    def on_ball_hit_wall(self, arbiter, space, data):
        """Gère la collision entre une balle et un mur"""
        # Récupérer la balle impliquée
        ball_shape = arbiter.shapes[0] if arbiter.shapes[0].collision_type == 1 else arbiter.shapes[1]
        
        # Récupérer la vitesse de la balle
        for ball in self.balls:
            if ball["shape"] == ball_shape:
                # Calculer la force de l'impact
                velocity_magnitude = np.linalg.norm(ball["body"].velocity)
                
                # Ne jouer une note que si l'impact est suffisamment fort
                if velocity_magnitude > 300:
                    # Mapper la vitesse à une note
                    # Plus la balle est rapide, plus la note est aiguë
                    note_index = min(int(velocity_magnitude / 200), len(self.current_melody) - 1) if self.current_melody else random.randint(0, 6)
                    self.add_sound_event("note", ball["body"].position, note=note_index)
                
                break
        
        # Continuer avec la collision normale
        return True
    
    def on_ball_hit_ball(self, arbiter, space, data):
        """Gère la collision entre deux balles"""
        # Récupérer les balles impliquées
        shapes = arbiter.shapes
        
        # Récupérer la force de l'impact
        total_velocity = 0
        balls_involved = []
        
        for shape in shapes:
            for ball in self.balls:
                if ball["shape"] == shape:
                    velocity_magnitude = np.linalg.norm(ball["body"].velocity)
                    total_velocity += velocity_magnitude
                    balls_involved.append(ball)
        
        # Ne jouer une note que si l'impact est suffisamment fort
        if total_velocity > 500 and len(balls_involved) == 2:
            # Mapper la vitesse totale à une note
            note_index = min(int(total_velocity / 300), len(self.current_melody) - 1) if self.current_melody else random.randint(0, 6)
            
            # Position moyenne des deux balles
            pos_x = (balls_involved[0]["body"].position.x + balls_involved[1]["body"].position.x) / 2
            pos_y = (balls_involved[0]["body"].position.y + balls_involved[1]["body"].position.y) / 2
            
            self.add_sound_event("note", (pos_x, pos_y), note=note_index)
        
        # Continuer avec la collision normale
        return True
    
    def add_random_ball(self):
        """Ajoute une balle avec des paramètres aléatoires"""
        # Position
        x = random.uniform(self.width * 0.1, self.width * 0.9)
        y = -50  # Apparaît au-dessus de l'écran
        
        # Taille et masse
        radius = random.uniform(20, 50)
        mass = radius * 0.2
        
        # Vitesse initiale
        vx = random.uniform(-300, 300)
        vy = random.uniform(100, 300)
        
        # Couleur (choisir dans la palette)
        color_hex = random.choice(self.color_palette)
        color_rgb = self.hex_to_rgb(color_hex)
        
        # Créer la balle
        body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
        body.position = (x, y)
        body.velocity = (vx, vy)
        
        shape = pymunk.Circle(body, radius)
        shape.elasticity = 0.95  # Très rebondissant
        shape.friction = 0.2
        shape.collision_type = 1  # Type 1 = balle
        
        self.space.add(body, shape)
        
        # Ajouter à la liste des balles
        self.balls.append({
            "body": body,
            "shape": shape,
            "radius": radius,
            "color": color_rgb,
            "trail": []  # Pour la traînée
        })
    
    def add_random_target(self):
        """Ajoute une cible statique avec des paramètres aléatoires"""
        # Position
        margin = 100
        x = random.uniform(margin, self.width - margin)
        y = random.uniform(margin, self.height - margin)
        
        # Éviter le chevauchement avec d'autres cibles
        for target in self.targets:
            dist = np.linalg.norm(np.array([x, y]) - np.array([target["body"].position.x, target["body"].position.y]))
            if dist < 150:  # Si trop proche, trouver une autre position
                return self.add_random_target()
        
        # Taille
        radius = random.uniform(40, 80)
        
        # Couleur (choisir dans la palette)
        color_hex = random.choice(self.color_palette)
        color_rgb = self.hex_to_rgb(color_hex)
        
        # Créer le corps statique
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = (x, y)
        
        shape = pymunk.Circle(body, radius)
        shape.elasticity = 0.9
        shape.friction = 0.4
        shape.collision_type = 2  # Type 2 = cible
        
        self.space.add(body, shape)
        
        # Ajouter à la liste des cibles
        self.targets.append({
            "body": body,
            "shape": shape,
            "radius": radius,
            "color": color_rgb,
            "exploded": False,
            "explosion_progress": 0,
            "explosion_duration": 0.5,  # secondes
            "explode": lambda: self.explode_target(body)
        })
    
    def explode_target(self, body):
        for target in self.targets:
            if target["body"] == body and not target["exploded"]:
                target["exploded"] = True

    def add_particle(self, x, y, color):
        """Ajoute une particule pour les effets visuels"""
        # Paramètres aléatoires
        size = random.uniform(3, 8)
        angle = random.uniform(0, 2 * np.pi)
        speed = random.uniform(100, 300)
        vx = np.cos(angle) * speed
        vy = np.sin(angle) * speed
        lifetime = random.uniform(0.5, 1.5)
        
        # Ajouter à la liste des particules
        self.particles.append({
            "x": x,
            "y": y,
            "vx": vx,
            "vy": vy,
            "size": size,
            "current_size": size,  # Pour l'animation
            "color": color,
            "lifetime": lifetime,
            "time_alive": 0
        })
    
    def add_sound_event(self, sound_type, position, **kwargs):
        """Ajoute un événement sonore à la liste"""
        # Enregistrer l'événement pour la génération audio ultérieure
        event = {
            "type": sound_type,
            "position": position,
            "frame": self.current_frame,
            "time": self.current_frame / self.fps,
            "params": kwargs
        }
        
        self.sound_events.append(event)
    
    def trigger_special_event(self):
        """Déclenche un événement spécial aléatoire"""
        event_type = random.choice([
            "ball_shower",
            "explode_all",
            "gravity_change",
            "big_ball",
            "color_shift"
        ])
        
        if event_type == "ball_shower":
            # Faire pleuvoir plusieurs balles
            for _ in range(random.randint(5, 10)):
                self.add_random_ball()
                
        elif event_type == "explode_all":
            # Faire exploser toutes les cibles
            for target in self.targets:
                if not target["exploded"]:
                    target["exploded"] = True
                    
                    # Ajouter un son d'explosion
                    self.add_sound_event("explosion", (target["body"].position.x, target["body"].position.y), size="large")
                    
                    # Créer des particules d'explosion
                    num_particles = random.randint(20, 30)
                    for _ in range(num_particles):
                        self.add_particle(
                            target["body"].position.x, 
                            target["body"].position.y,
                            target["color"]
                        )
                        
        elif event_type == "gravity_change":
            # Changer la gravité temporairement
            original_gravity = self.space.gravity
            self.space.gravity = (random.uniform(-500, 500), random.uniform(-500, 1500))
            
            # Planifier le retour à la normale
            self.special_effects.append({
                "type": "restore_gravity",
                "original_gravity": original_gravity,
                "end_frame": self.current_frame + int(3 * self.fps)  # 3 secondes
            })
            
        elif event_type == "big_ball":
            # Créer une très grosse balle
            x = random.uniform(self.width * 0.1, self.width * 0.9)
            y = -100
            radius = random.uniform(80, 120)
            mass = radius * 0.5
            
            vx = random.uniform(-200, 200)
            vy = random.uniform(100, 300)
            
            # Jouer une note grave pour signaler l'arrivée d'une grosse balle
            self.add_sound_event("note", (x, y), note=0, octave=0)  # Note grave
            
            # Couleur (choisir dans la palette)
            color_hex = random.choice(self.color_palette)
            color_rgb = self.hex_to_rgb(color_hex)
            
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
            
        elif event_type == "color_shift":
            # Changer temporairement la palette de couleurs
            original_palette = self.color_palette.copy()
            
            # Créer une palette décalée
            shifted_palette = []
            for color in original_palette:
                r, g, b = self.hex_to_rgb(color)
                # Décaler les couleurs
                r = (r + random.randint(20, 60)) % 256
                g = (g + random.randint(20, 60)) % 256
                b = (b + random.randint(20, 60)) % 256
                shifted_palette.append(f"#{r:02x}{g:02x}{b:02x}")
            
            self.color_palette = shifted_palette
            
            # Planifier le retour à la normale
            self.special_effects.append({
                "type": "restore_palette",
                "original_palette": original_palette,
                "end_frame": self.current_frame + int(5 * self.fps)  # 5 secondes
            })
    
    def update_simulation(self, dt):
        """Met à jour tous les objets de la simulation"""
        # Mettre à jour les balles
        for ball in self.balls:
            # Ajouter la position à la traînée
            ball["trail"].append((int(ball["body"].position.x), int(ball["body"].position.y)))
            if len(ball["trail"]) > 20:  # Limiter la longueur de la traînée
                ball["trail"].pop(0)
        
        # Mettre à jour les particules
        for particle in self.particles:
            # Mettre à jour la position
            particle["x"] += particle["vx"] * dt
            particle["y"] += particle["vy"] * dt
            particle["vy"] += self.gravity * 0.3 * dt  # Gravité légère
            particle["time_alive"] += dt
            
            # Mettre à jour la taille
            factor = max(0, 1 - (particle["time_alive"] / particle["lifetime"]))
            particle["current_size"] = particle["size"] * factor
        
        # Supprimer les particules mortes
        self.particles = [p for p in self.particles if p["time_alive"] < p["lifetime"]]
        
        # Mettre à jour les cibles
        for target in self.targets:
            if target["exploded"] and target["explosion_progress"] < 1.0:
                target["explosion_progress"] += dt / target["explosion_duration"]
        
        # Supprimer les cibles complètement explosées
        self.targets = [t for t in self.targets if not (t["exploded"] and t["explosion_progress"] >= 1.0)]
        
        # Supprimer les balles sorties de l'écran
        balls_to_remove = []
        for ball in self.balls:
            pos = ball["body"].position
            if pos.y > self.height + 100 or pos.x < -100 or pos.x > self.width + 100:
                self.space.remove(ball["body"], ball["shape"])
                balls_to_remove.append(ball)
                
        for ball in balls_to_remove:
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
                effects_to_remove.append(effect)
        
        # Supprimer les effets terminés
        for effect in effects_to_remove:
            self.special_effects.remove(effect)
        
        # Mettre à jour la physique
        self.space.step(dt)
    
    def render_frame(self, frame_number):
        """Rend un frame de la simulation"""
        # Créer une surface pour le rendu
        surface = pygame.Surface((self.width, self.height))
        
        # Remplir l'arrière-plan
        background_color = (10, 10, 15)  # Fond sombre
        surface.fill(background_color)
        
        # Dessiner un arrière-plan dégradé
        gradient_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        color1 = (15, 10, 30)
        color2 = (30, 20, 40)
        
        for y in range(self.height):
            # Calculer la couleur interpolée
            t = y / self.height
            r = color1[0] * (1 - t) + color2[0] * t
            g = color1[1] * (1 - t) + color2[1] * t
            b = color1[2] * (1 - t) + color2[2] * t
            
            pygame.draw.line(gradient_surface, (r, g, b), (0, y), (self.width, y))
            
        surface.blit(gradient_surface, (0, 0))
        
        # Ajouter un effet de grille
        grid_spacing = 100
        grid_color = (50, 50, 70, 20)  # Avec transparence
        
        grid_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        for x in range(0, self.width, grid_spacing):
            pygame.draw.line(grid_surface, grid_color, (x, 0), (x, self.height))
            
        for y in range(0, self.height, grid_spacing):
            pygame.draw.line(grid_surface, grid_color, (0, y), (self.width, y))
            
        surface.blit(grid_surface, (0, 0))
        
        # Dessiner les cibles
        for target in self.targets:
            if not target["exploded"]:
                # Dessiner le cercle avec un effet de lueur
                glow_radius = target["radius"] * 1.1
                
                # Surface de lueur avec transparence
                glow = pygame.Surface((int(glow_radius * 2), int(glow_radius * 2)), pygame.SRCALPHA)
                r, g, b = target["color"]
                glow_color = (r, g, b, 100)  # Ajouter transparence
                pygame.draw.circle(glow, glow_color, (int(glow_radius), int(glow_radius)), int(glow_radius))
                
                # Appliquer un flou (simulation)
                for i in range(3):
                    pygame.draw.circle(glow, (r, g, b, 30), 
                                      (int(glow_radius), int(glow_radius)), 
                                      int(glow_radius - i))
                
                # Positionner la lueur
                pos = target["body"].position
                surface.blit(glow, (int(pos.x - glow_radius), int(pos.y - glow_radius)))
                
                # Cercle principal
                pygame.draw.circle(surface, target["color"], (int(pos.x), int(pos.y)), int(target["radius"]))
                
                # Reflet (effet 3D)
                highlight_pos = (int(pos.x - target["radius"] * 0.3), int(pos.y - target["radius"] * 0.3))
                highlight_size = target["radius"] * 0.4
                highlight_color = tuple(min(c + 40, 255) for c in target["color"])
                pygame.draw.circle(surface, highlight_color, highlight_pos, int(highlight_size))
            
            elif target["explosion_progress"] < 1.0:
                # Animation d'explosion
                pos = target["body"].position
                progress = target["explosion_progress"]
                
                # Cercle qui se dilate et s'estompe
                alpha = int(255 * (1 - progress))
                expanded_radius = target["radius"] * (1 + progress * 2)
                
                # Surface avec transparence
                s = pygame.Surface((int(expanded_radius * 2), int(expanded_radius * 2)), pygame.SRCALPHA)
                r, g, b = target["color"]
                pygame.draw.circle(s, (r, g, b, alpha), 
                                 (int(expanded_radius), int(expanded_radius)), 
                                 int(expanded_radius))
                
                surface.blit(s, (int(pos.x - expanded_radius), int(pos.y - expanded_radius)))
        
        # Dessiner les balles
        for ball in self.balls:
            # Dessiner la traînée
            if len(ball["trail"]) > 1:
                for i in range(len(ball["trail"]) - 1):
                    alpha = int(255 * (i / len(ball["trail"])))
                    trail_width = int(ball["radius"] * (i / len(ball["trail"])) * 1.5)
                    if trail_width > 0:
                        r, g, b = ball["color"]
                        pygame.draw.line(surface, 
                                       (r, g, b, alpha), 
                                       ball["trail"][i], 
                                       ball["trail"][i+1], 
                                       trail_width)
            
            # Dessiner l'effet de lueur
            glow_radius = ball["radius"] * 1.2
            glow = pygame.Surface((int(glow_radius * 2), int(glow_radius * 2)), pygame.SRCALPHA)
            r, g, b = ball["color"]
            pygame.draw.circle(glow, (r, g, b, 100), 
                             (int(glow_radius), int(glow_radius)), 
                             int(glow_radius))
            
            pos = ball["body"].position
            surface.blit(glow, (int(pos.x - glow_radius), int(pos.y - glow_radius)))
            
            # Dessiner la balle
            pygame.draw.circle(surface, ball["color"], 
                             (int(pos.x), int(pos.y)), 
                             int(ball["radius"]))
            
            # Ajouter un reflet (effet 3D)
            highlight_pos = (int(pos.x - ball["radius"] * 0.3), int(pos.y - ball["radius"] * 0.3))
            highlight_size = ball["radius"] * 0.3
            pygame.draw.circle(surface, (255, 255, 255), highlight_pos, int(highlight_size))
        
        # Dessiner les particules
        for particle in self.particles:
            # Surface avec transparence
            particle_size = int(particle["current_size"] * 2)
            if particle_size <= 0:
                continue
                
            s = pygame.Surface((particle_size, particle_size), pygame.SRCALPHA)
            r, g, b = particle["color"]
            alpha = int(255 * (1 - particle["time_alive"] / particle["lifetime"]))
            pygame.draw.circle(s, (r, g, b, alpha), 
                             (int(particle_size/2), int(particle_size/2)), 
                             int(particle["current_size"]))
            
            surface.blit(s, (int(particle["x"] - particle["current_size"]), int(particle["y"] - particle["current_size"])))
        
        # Enregistrer le frame
        frame_path = os.path.join(self.frames_dir, f"frame_{frame_number:06d}.png")
        pygame.image.save(surface, frame_path)
        
        return frame_path
    
    def run_simulation(self):
        """Exécute la simulation complète"""
        logger.info("Démarrage de la simulation...")
        
        # Initialiser pygame
        pygame.init()
        
        # Initialiser la physique
        self.initialize_physics()
        
        # Générer les sons
        self.generate_sounds()
        
        # Liste pour stocker les événements sonores
        self.sound_events = []
        
        # Réinitialiser le compteur de frames
        self.current_frame = 0
        
        # Configurer les temps pour les événements
        next_ball_time = 0
        next_target_time = 1.0
        next_event_time = 5.0
        
        # Boucle principale
        dt = 1.0 / self.fps
        
        logger.info(f"Génération de {self.total_frames} frames...")
        start_time = time.time()
        
        while self.current_frame < self.total_frames:
            # Calculer le temps actuel
            current_time = self.current_frame * dt
            
            # Événements périodiques
            if current_time >= next_ball_time:
                self.add_random_ball()
                next_ball_time = current_time + random.uniform(0.5, 2.0)
                
            if current_time >= next_target_time and len(self.targets) < 20:
                self.add_random_target()
                next_target_time = current_time + random.uniform(1.0, 3.0)
                
            if current_time >= next_event_time:
                self.trigger_special_event()
                next_event_time = current_time + random.uniform(5.0, 10.0)
            
            # Mettre à jour la simulation
            self.update_simulation(dt)
            
            # Rendre le frame
            self.render_frame(self.current_frame)
            
            # Incrémenter le compteur de frames
            self.current_frame += 1
            
            # Afficher la progression
            if self.current_frame % 60 == 0 or self.current_frame == self.total_frames - 1:
                elapsed = time.time() - start_time
                progress = self.current_frame / self.total_frames
                eta = elapsed / progress - elapsed if progress > 0 else 0
                
                logger.info(f"Progression: {self.current_frame}/{self.total_frames} frames ({progress*100:.1f}%, ETA: {eta:.1f}s)")
        
        # Fermer pygame
        pygame.quit()
        
        logger.info("Simulation terminée")
        return True
    
    def generate_video(self):
        """Génère la vidéo finale à partir des frames et des sons"""
        logger.info("Génération de la vidéo finale...")
        
        # Créer la vidéo à partir des frames
        from pathlib import Path
        frame_pattern = str(Path(self.frames_dir) / "frame_%06d.png")

        
        try:
            # Utiliser MoviePy
            clip = ImageSequenceClip(self.frames_dir + "/frame_%06d.png", fps=self.fps)

            # Ajouter l'audio des événements à la vidéo
            if os.path.exists(self.output_audio_file):
                final_clip = VideoFileClip(self.output_path).set_audio(AudioFileClip(self.output_audio_file))
                final_clip.write_videofile(
                    self.output_path.replace(".mp4", "_with_audio.mp4"),
                    codec='libx264',
                    audio_codec='aac',
                    fps=self.fps
                )
                logger.info(f"Vidéo finale avec audio: {self.output_path.replace('.mp4', '_with_audio.mp4')}")
            else:
                logger.warning(f"Fichier audio non trouvé: {self.output_audio_file}")

            
            # Écrire la vidéo
            clip.write_videofile(
                self.output_path,
                codec='libx264',
                audio_codec='aac',
                fps=self.fps
            )
            
            logger.info(f"Vidéo créée avec succès: {self.output_path}")
            
            return self.output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la vidéo: {e}")
            
            # Utiliser une méthode alternative (ffmpeg directement)
            try:
                import subprocess
                
                ffmpeg_path = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
                cmd = [
                    ffmpeg_path, '-y',
                    '-framerate', str(self.fps),
                    '-i', frame_pattern,
                    '-c:v', 'libx264',
                    '-r', str(self.fps),
                    '-pix_fmt', 'yuv420p',
                    self.output_path
                ]

                
                subprocess.run(cmd, check=True)
                
                logger.info(f"Vidéo créée avec succès (méthode alternative): {self.output_path}")
                return self.output_path
                
            except Exception as e:
                logger.error(f"Erreur lors de la génération de la vidéo (méthode alternative): {e}")
                return None


class VideoEnhancer:
    """
    Module d'amélioration des vidéos avec texte, effets et musique
    """
    
    def __init__(self, fonts_dir=None):
        """
        Initialise l'améliorateur de vidéos
        
        Args:
            fonts_dir: Répertoire contenant des polices supplémentaires
        """
        self.temp_dir = os.path.join(os.getcwd(), "temp_enhance")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Polices TikTok populaires
        self.default_fonts = ["Arial", "Impact", "Verdana", "Comic Sans MS"]
        self.available_fonts = self.find_available_fonts()
        
        # Couleurs TikTok
        self.tiktok_colors = [
            "#FF0050",  # Rouge TikTok
            "#00F2EA",  # Turquoise TikTok
            "#FFFFFF",  # Blanc
            "#FE2C55",  # Rose TikTok
            "#25F4EE"   # Bleu TikTok
        ]
        
        logger.info("Module d'amélioration vidéo initialisé")
    
    def find_available_fonts(self):
        """Trouve les polices disponibles (chemins complets aux fichiers TTF/OTF)"""
        search_dirs = [
            "C:/Windows/Fonts/",
            "/usr/share/fonts/",
            "/Library/Fonts/"
        ]
        
        font_candidates = ["arial.ttf", "Arial.ttf", "impact.ttf", "verdana.ttf", "comic.ttf"]

        available = []
        for font_file in font_candidates:
            for dir_path in search_dirs:
                path = Path(dir_path) / font_file
                if path.exists():
                    available.append(str(path))
            
        if not available:
            # Utiliser la police par défaut si aucune n'est disponible
            available = [ImageFont.load_default()]
        
        logger.info(f"Polices trouvées: {available}")
        return available
    
    def hex_to_rgb(self, hex_color):
        """Convertit une couleur hexadécimale en RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def add_intro_text(self, video_path, output_path, text="Watch till the end! 👀"):
        """Ajoute un texte d'introduction au début de la vidéo"""
        try:
            # Charger la vidéo
            video = VideoFileClip(video_path)
            
            # Sélectionner une police et une couleur
            font = random.choice(self.available_fonts)
            color = random.choice(self.tiktok_colors)
            
            # Créer le texte
            txt_clip = TextClip(
                font,
                text=text,
                font_size=70,
                color="white",
                stroke_color="black",
                stroke_width=2
            ).with_position('center').with_duration(3)

            # Créer un fond noir de la taille de la vidéo
            bg_clip = ImageClip(
                np.zeros((video.h, video.w, 3), dtype=np.uint8)
            ).with_duration(3)

            # Superposer texte sur fond noir
            intro_clip = CompositeVideoClip([bg_clip, txt_clip])

            # Concaténer intro + vidéo
            final_clip = concatenate_videoclips([intro_clip, video])

            # Écrire la vidéo finale
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac'
            )

            # Fermer les clips
            video.close()
            final_clip.close()

            logger.info(f"Introduction ajoutée: {output_path}")
            return output_path

        except Exception as e:
            video.close()
            logger.error(f"Erreur lors de l'ajout de l'introduction: {e}")
            return video_path
    
    def add_hashtags(self, video_path, output_path, hashtags):
        """Ajoute des hashtags en superposition sur la vidéo"""
        try:
            # Charger la vidéo
            video = VideoFileClip(video_path)
            
            # Formater la chaîne de hashtags
            if len(hashtags) > 10:
                hashtags = hashtags[:10]
            
            hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
            
            # Limiter la longueur
            if len(hashtag_text) > 50:
                hashtag_text = hashtag_text[:47] + "..."
            
            # Créer le texte
            font = random.choice(self.available_fonts)
            txt_clip = TextClip(
                font,
                text=hashtag_text,
                font_size=30,
                color="white",
                stroke_color="black",
                stroke_width=1
            ).with_position(('center', 'bottom')).with_duration(video.duration)

            # Composite final (vidéo + texte)
            final_clip = CompositeVideoClip([video, txt_clip])

            # Sauvegarder la vidéo finale
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac'
            )

            # Cleanup
            video.close()
            final_clip.close()

            logger.info(f"Hashtags ajoutés: {output_path}")
            return output_path

                
        except Exception as e:
            logger.exception(f"Erreur lors de l'ajout des hashtags: {e}")
            video.close()
            return video_path
    
    def add_viral_music(self, video_path, output_path, music_file=None):
        """Ajoute une musique virale à la vidéo"""
        try:
            # Charger la vidéo
            video = VideoFileClip(video_path)
            
            # Si aucun fichier de musique n'est spécifié, utiliser les sons de la simulation
            if not music_file:
                logger.info("Pas de musique spécifiée, la vidéo gardera sa piste audio originale")
                return video_path
            
            # Charger la musique
            music = AudioFileClip(music_file)

            # Boucler la musique si nécessaire
            if music.duration < video.duration:
                repeats = int(video.duration / music.duration) + 1
                music_looped = concatenate_audioclips([music] * repeats)
            else:
                music_looped = music

            # Découper proprement après la boucle
            music_final = music_looped.subclipped(0, video.duration)

            # Ajouter à la vidéo
            final = video.with_audio(music_final)
            
            # Écrire la vidéo
            final.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac'
            )
            
            # Fermer les clips
            video.close()
            final.close()
            
            logger.info(f"Musique ajoutée: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la musique: {e}")
            return video_path
    
    def enhance_video(self, video_path, output_path, options):
        """
        Améliore une vidéo avec plusieurs effets
        
        Args:
            video_path: Chemin de la vidéo d'origine
            output_path: Chemin de sortie
            options: Dictionnaire d'options d'amélioration
        """
        current_path = video_path
        
        # Créer des chemins temporaires
        temp_intro = os.path.join(self.temp_dir, "temp_intro.mp4")
        temp_hashtags = os.path.join(self.temp_dir, "temp_hashtags.mp4")
        
        # Ajouter une introduction
        if options.get("add_intro", True):
            intro_text = options.get("intro_text", "Watch till the end! 👀")
            intro_result = self.add_intro_text(current_path, temp_intro, intro_text)
            if intro_result:
                current_path = intro_result
        
        # Ajouter des hashtags
        if options.get("add_hashtags", True):
            hashtags = options.get("hashtags", ["fyp", "viral", "satisfying"])
            hashtag_result = self.add_hashtags(current_path, temp_hashtags, hashtags)
            if hashtag_result:
                current_path = hashtag_result
        
        # Ajouter de la musique
        if options.get("add_music", True):
            music_file = options.get("music_file")
            if music_file:
                music_result = self.add_viral_music(current_path, output_path, music_file)
                if music_result:
                    current_path = music_result
            else:
                logger.error(f"Fichier audio introuvable: {music_file}")
        
        # Si le chemin actuel n'est pas le chemin de sortie final, le copier
        if current_path != output_path:
            import shutil
            shutil.copy2(current_path, output_path)
        
        # Nettoyer les fichiers temporaires
        for file in [temp_intro, temp_hashtags]:
            if os.path.exists(file):
                os.remove(file)
        
        logger.info(f"Vidéo améliorée: {output_path}")
        return output_path


from tiktok_publisher import TikTokPublisher

class TikTokAutomator:
    """
    Classe principale qui coordonne tout le processus de génération et publication
    """
    
    def __init__(self, output_dir="videos"):
        """
        Initialise l'automatiseur TikTok
        
        Args:
            output_dir: Répertoire de sortie pour les vidéos
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Créer les modules
        self.scraper = TikTokScraper()
        self.enhancer = VideoEnhancer()
        self.publisher = TikTokPublisher()
        
        # Configuration
        self.config = {
            "video_duration": 61,
            "fps": 60,
            "width": 1080,
            "height": 1920,
            "auto_publish": False,
            "publish_time": None,
            "enhancement_options": {
                "add_intro": False,
                "add_hashtags": False,
                "add_music": True
            }
        }
        
        logger.info("TikTok Automator initialisé")
    
    def update_config(self, new_config):
        """Met à jour la configuration"""
        self.config.update(new_config)
        logger.info("Configuration mise à jour")
    
    def generate_video(self, options=None):
        """
        Génère une vidéo virale basée sur l'analyse des tendances
        
        Args:
            options: Options spécifiques pour la génération (optionnel)
            
        Returns:
            Le chemin de la vidéo générée
        """
        try:
            # Obtenir l'analyse des tendances
            trend_analysis = self.scraper.get_trend_analysis()
            
            # Appliquer les recommandations aux options
            settings = trend_analysis["recommended_settings"]
            
            # Créer un nom de fichier basé sur le timestamp
            timestamp = int(time.time())
            video_name = f"tiktok_viral_{timestamp}.mp4"
            video_path = os.path.join(self.output_dir, video_name)
            
            # Configurer la simulation
            simulation = AdvancedPhysicsSimulation(
                width=self.config["width"],
                height=self.config["height"],
                fps=self.config["fps"],
                duration=self.config["video_duration"],
                output_path=video_path
            )
            
            # Appliquer les paramètres recommandés
            simulation.set_color_palette(settings["color_palette"])
            simulation.set_beat_frequency(settings["beat_frequency"])
            
            # Télécharger la musique tendance et extraire la mélodie
            from TikTokAudioManager import TikTokAudioManager

            audio_manager = TikTokAudioManager()
            popular_song = trend_analysis["popular_music"][0]  # Exemple : "STAY - Justin Bieber"

            print(f"🔽 Téléchargement de la musique tendance : {popular_song}")
            audio_file = audio_manager.search_and_download_song(popular_song)

            if audio_file:
                melody_notes = audio_manager.extract_melody(audio_file)
                logger.debug(f"melody: {melody_notes}")
                simulation.set_melody(melody_notes)
            else:
                print("⚠️ Échec du téléchargement de la musique, simulation avec notes par défaut")

            # Exécuter la simulation
            simulation.run_simulation()
            
            # Générer la vidéo
            video_result = simulation.generate_video()
            
            # Générer la piste audio des événements
            audio_file = simulation.render_audio_from_events(f"videos/tiktok_audio_{timestamp}.wav")
            simulation.output_audio_file = audio_file

            if not video_result:
                logger.error("Échec de la génération de la vidéo")
                return None
            
            # Améliorer la vidéo
            enhanced_path = os.path.join(self.output_dir, f"tiktok_viral_{timestamp}_enhanced.mp4")
            
            # Options d'amélioration
            enhance_options = self.config["enhancement_options"].copy()

            # Ajouter l'audio mixé dans les options
            enhance_options.update({
                "intro_text": "Watch this all the way through! 👀",
                "hashtags": settings["recommended_hashtags"],
                "music_file": audio_file
            })
            
            # Appliquer les améliorations
            enhanced_result = self.enhancer.enhance_video(
                video_result,
                enhanced_path,
                enhance_options
            )
            
            logger.info(f"Vidéo générée avec succès: {enhanced_result}")
            return enhanced_result
            
        except Exception as e:
            logger.exception(f"Erreur lors de la génération de la vidéo: {e}")
            return None
    
    def publish_now(self, video_path=None):
        """
        Publie immédiatement une vidéo sur TikTok
        
        Args:
            video_path: Chemin de la vidéo à publier (optionnel)
            
        Returns:
            True si la publication a réussi, False sinon
        """
        if not video_path:
            # Trouver la vidéo la plus récente
            video_files = [f for f in os.listdir(self.output_dir) if f.endswith('.mp4')]
            if not video_files:
                logger.error("Aucune vidéo trouvée à publier")
                return False
            
            # Trier par date de modification (la plus récente en premier)
            video_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.output_dir, f)), reverse=True)
            video_path = os.path.join(self.output_dir, video_files[0])
        
        # Obtenir des hashtags tendance
        hashtags = self.scraper.get_trending_hashtags()[:8]  # Limiter à 8 hashtags
        
        # Ajouter toujours les hashtags essentiels
        essential_hashtags = ["fyp", "foryou", "viral"]
        for tag in essential_hashtags:
            if tag not in hashtags:
                hashtags.insert(0, tag)
        
        # Générer une description captivante
        captions = [
            "This simulation is so satisfying! 😍",
            "Watch till the end for a surprise! 👀",
            "I could watch this all day! 🤩",
            "The physics in this are incredible! 🔥",
            "Turn on the sound! 🔊"
        ]
        caption = random.choice(captions)
        
        # Publier la vidéo
        return self.publisher.upload_video(
            video_path=video_path,
            caption=caption,
            hashtags=hashtags
        )
    
    def schedule_publication(self, video_path, schedule_time):
        """
        Planifie la publication d'une vidéo
        
        Args:
            video_path: Chemin de la vidéo à publier
            schedule_time: Heure de publication (format datetime)
            
        Returns:
            ID de la tâche planifiée
        """
        def publish_task():
            logger.info(f"Publication programmée démarrée pour: {video_path}")
            self.publish_now(video_path)
        
        # Calculer le délai
        now = datetime.now()
        if schedule_time < now:
            logger.error("L'heure de publication est dans le passé")
            return None
        
        # Programmer la tâche
        delay = (schedule_time - now).total_seconds()
        
        # Utiliser schedule pour la planification
        job = schedule.every(delay).seconds.do(publish_task)
        
        logger.info(f"Publication programmée pour: {schedule_time}")
        return job
    
    def generate_and_publish(self, publish=True, schedule_time=None):
        """
        Génère et publie une vidéo virale
        
        Args:
            publish: Publier automatiquement
            schedule_time: Heure de publication (optionnel)
            
        Returns:
            Le chemin de la vidéo générée
        """
        # Générer la vidéo
        video_path = self.generate_video()
        
        if not video_path:
            logger.error("Échec de la génération de la vidéo")
            return None
        
        # Publier si demandé
        if publish:
            if schedule_time:
                self.schedule_publication(video_path, schedule_time)
            else:
                self.publish_now(video_path)
        
        return video_path
    
    def run_daily_schedule(self, times=None):
        """
        Configure une planification quotidienne pour générer et publier des vidéos
        
        Args:
            times: Liste d'heures de publication (format HH:MM)
        """
        if not times:
            # Heures optimales pour TikTok
            times = ["09:00", "12:30", "18:00", "21:00"]
        
        logger.info(f"Configuration de la planification quotidienne: {times}")
        
        # Configurer les tâches planifiées
        for time_str in times:
            schedule.every().day.at(time_str).do(self.generate_and_publish, publish=True)
        
        # Exécuter les tâches planifiées
        while True:
            schedule.run_pending()
            time.sleep(60)


# Point d'entrée principal
if __name__ == "__main__":
    try:
        # Configurer les arguments en ligne de commande
        import argparse
        
        parser = argparse.ArgumentParser(description="TikSim Pro - Générateur Automatique de Contenu Viral pour TikTok")
        parser.add_argument("--generate", action="store_true", help="Générer une vidéo sans publier")
        parser.add_argument("--publish", action="store_true", help="Publier la dernière vidéo générée")
        parser.add_argument("--schedule", action="store_true", help="Démarrer la planification quotidienne")
        parser.add_argument("--times", nargs="+", help="Heures de publication (format HH:MM)")
        parser.add_argument("--duration", type=int, default=61, help="Durée de la vidéo en secondes")
        
        args = parser.parse_args()
        
        # Créer l'automatiseur
        automator = TikTokAutomator()
        
        # Mettre à jour la configuration
        if args.duration:
            automator.update_config({"video_duration": args.duration,
                                      "enhancement_options": {
                                        "add_intro": False,
                                        "add_hashtags": False
                                    }})
                                
        # Exécuter l'action demandée
        if args.generate:
            video_path = automator.generate_video()
            print(f"Vidéo générée: {video_path}")
            
        elif args.publish:
            result = automator.publish_now()
            print(f"Publication {'réussie' if result else 'échouée'}")
            
        elif args.schedule:
            print("Démarrage de la planification quotidienne...")
            automator.run_daily_schedule(args.times)
            
        else:
            # Mode interactif par défaut
            print("\nTikSim Pro - Générateur Automatique de Contenu Viral pour TikTok")
            print("=" * 70)
            print("1. Générer une vidéo")
            print("2. Publier la dernière vidéo")
            print("3. Générer et publier")
            print("4. Configurer une planification quotidienne")
            print("5. Quitter")
            
            choice = input("\nChoisissez une option (1-5): ")
            
            if choice == "1":
                video_path = automator.generate_video()
                print(f"Vidéo générée: {video_path}")
                
            elif choice == "2":
                result = automator.publish_now()
                print(f"Publication {'réussie' if result else 'échouée'}")
                
            elif choice == "3":
                video_path = automator.generate_and_publish()
                print(f"Vidéo générée et publiée: {video_path}")
                
            elif choice == "4":
                times_input = input("Entrez les heures de publication (format HH:MM, séparées par des espaces): ")
                times = times_input.split()
                print(f"Démarrage de la planification quotidienne: {times}")
                automator.run_daily_schedule(times)
                
            elif choice == "5":
                print("Au revoir!")
                
            else:
                print("Option invalide")
        
    except KeyboardInterrupt:
        print("\nOpération annulée par l'utilisateur.")
        
    except Exception as e:
        print(f"Erreur: {e}")
        logger.error(f"Erreur non gérée: {e}", exc_info=True)