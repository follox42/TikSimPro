"""
Générateur de Vidéos TikTok - Simulation Physique de Balles Explosives
----------------------------------------------------------------------
Ce script crée une simulation physique attrayante où des balles colorées
rebondissent et explosent des cercles statiques lorsqu'elles les touchent.
Parfait pour des vidéos TikTok virales de 61 secondes.

Prérequis:
pip install pygame pymunk numpy opencv-python matplotlib
"""

import os
import pygame
import pymunk
import pymunk.pygame_util
import random
import math
import numpy as np
import cv2
from matplotlib import cm
import time
import pygame.midi
import matplotlib.pyplot as plt

# Constantes
WIDTH, HEIGHT = 1080, 1920  # Format vertical TikTok
FPS = 60
GRAVITY = 1000
VIDEO_DURATION = 10  # 61 secondes exactement
TOTAL_FRAMES = VIDEO_DURATION * FPS

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BACKGROUND_COLOR = (10, 10, 15)

# Palettes de couleurs vibrantes pour TikTok
# Utiliser la nouvelle syntaxe recommandée pour les colormaps
COLORMAP = plt.cm.plasma

class Particle:
    """Particules pour les effets d'explosion"""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.size = random.randint(3, 8)
        self.current_size = self.size  # Initialiser current_size
        self.color = color
        self.current_color = (*color, 255)  # Initialiser current_color avec alpha
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(100, 300)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = random.uniform(0.5, 1.5)
        self.time_alive = 0
        
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += GRAVITY * 0.3 * dt  # Gravité légère
        self.time_alive += dt
        # Réduire la taille avec le temps
        factor = max(0, 1 - (self.time_alive / self.lifetime))
        self.current_size = self.size * factor
        # Faire disparaître progressivement
        alpha = int(255 * factor)
        r, g, b = self.color
        self.current_color = (r, g, b, alpha)
        
    def is_dead(self):
        return self.time_alive >= self.lifetime
        
    def draw(self, surface):
        # Dessiner avec transparence
        s = pygame.Surface((int(self.current_size * 2), int(self.current_size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, self.current_color, (int(self.current_size), int(self.current_size)), int(self.current_size))
        surface.blit(s, (int(self.x - self.current_size), int(self.y - self.current_size)))

class CircleTarget:
    """Cercles cibles que les balles peuvent exploser"""
    def __init__(self, space, position, radius, mass=10.0, is_static=True):
        self.radius = radius
        self.position = position
        self.mass = mass
        self.exploded = False
        self.explosion_progress = 0
        self.explosion_duration = 0.5  # secondes
        
        # Couleur basée sur la position (pour un effet visuel agréable)
        norm_y = position[1] / HEIGHT
        color_tuple = COLORMAP(norm_y)
        self.color = (int(color_tuple[0]*255), int(color_tuple[1]*255), int(color_tuple[2]*255))
        self.highlight_color = tuple(min(c + 40, 255) for c in self.color)
        
        # Créer le corps physique
        if is_static:
            self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        else:
            moment = pymunk.moment_for_circle(mass, 0, radius)
            self.body = pymunk.Body(mass, moment)
        
        self.body.position = position
        
        # Créer la forme
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = 0.9
        self.shape.friction = 0.4
        self.shape.collision_type = 2  # Type 2 = cercle cible
        
        # Ajouter au monde physique
        space.add(self.body, self.shape)
        
        # Stocker une référence à l'espace
        self.space = space
        
    def explode(self):
        if not self.exploded:
            self.exploded = True
            # Enlever du monde physique
            self.space.remove(self.body, self.shape)
            
    def update(self, dt):
        if self.exploded and self.explosion_progress < 1.0:
            self.explosion_progress += dt / self.explosion_duration
            
    def is_fully_exploded(self):
        return self.exploded and self.explosion_progress >= 1.0
            
    def draw(self, surface, draw_options=None):
        if not self.exploded:
            # Dessiner les cercles avec un effet de lueur
            glow_radius = self.radius * 1.1
            
            # Surface de lueur avec transparence
            glow = pygame.Surface((int(glow_radius * 2), int(glow_radius * 2)), pygame.SRCALPHA)
            glow_color = (*self.color, 100)  # Ajouter transparence
            pygame.draw.circle(glow, glow_color, (int(glow_radius), int(glow_radius)), int(glow_radius))
            
            # Appliquer un flou (simulation)
            for i in range(3):
                pygame.draw.circle(glow, (*self.color, 30), 
                                  (int(glow_radius), int(glow_radius)), 
                                  int(glow_radius - i))
            
            # Positionner la lueur
            pos = self.body.position
            surface.blit(glow, (int(pos.x - glow_radius), int(pos.y - glow_radius)))
            
            # Cercle principal
            pygame.draw.circle(surface, self.color, (int(pos.x), int(pos.y)), int(self.radius))
            
            # Reflet (effet 3D)
            highlight_pos = (int(pos.x - self.radius * 0.3), int(pos.y - self.radius * 0.3))
            highlight_size = self.radius * 0.4
            pygame.draw.circle(surface, self.highlight_color, highlight_pos, int(highlight_size))
        elif self.explosion_progress < 1.0:
            # Animation d'explosion
            pos = self.body.position
            progress = self.explosion_progress
            
            # Cercle qui se dilate et s'estompe
            alpha = int(255 * (1 - progress))
            expanded_radius = self.radius * (1 + progress * 2)
            
            # Surface avec transparence
            s = pygame.Surface((int(expanded_radius * 2), int(expanded_radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), 
                             (int(expanded_radius), int(expanded_radius)), 
                             int(expanded_radius))
            
            surface.blit(s, (int(pos.x - expanded_radius), int(pos.y - expanded_radius)))

class Ball:
    """Balles qui rebondissent et peuvent exploser les cercles"""
    def __init__(self, space, position, radius, mass=1.0, velocity=(0, 0)):
        self.radius = radius
        self.position = position
        self.mass = mass
        
        # Créer corps physique
        moment = pymunk.moment_for_circle(mass, 0, radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = position
        self.body.velocity = velocity
        
        # Créer forme
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = 0.95  # Très rebondissant
        self.shape.friction = 0.2
        self.shape.collision_type = 1  # Type 1 = balle
        
        # Couleur basée sur la vitesse
        norm_speed = min(1.0, np.linalg.norm(velocity) / 2000)
        color_tuple = COLORMAP(norm_speed)
        self.base_color = (int(color_tuple[0]*255), int(color_tuple[1]*255), int(color_tuple[2]*255))
        self.color = self.base_color
        
        # Traînée de mouvement
        self.past_positions = []
        self.max_trail_length = 20
        
        # Effet lumineux
        self.glow_radius = radius * 1.2
        self.glow_color = (*self.base_color, 100)  # Avec transparence
        
        # Ajouter au monde physique
        space.add(self.body, self.shape)
        
    def update(self, dt):
        # Mettre à jour la couleur basée sur la vitesse
        speed = np.linalg.norm(self.body.velocity)
        norm_speed = min(1.0, speed / 2000)
        color_tuple = COLORMAP(norm_speed)
        self.color = (int(color_tuple[0]*255), int(color_tuple[1]*255), int(color_tuple[2]*255))
        
        # Mettre à jour la traînée
        self.past_positions.append((int(self.body.position.x), int(self.body.position.y)))
        if len(self.past_positions) > self.max_trail_length:
            self.past_positions.pop(0)
            
    def draw(self, surface, draw_options=None):
        # Dessiner la traînée
        if len(self.past_positions) > 1:
            for i in range(len(self.past_positions) - 1):
                alpha = int(255 * (i / len(self.past_positions)))
                trail_width = int(self.radius * (i / len(self.past_positions)) * 1.5)
                if trail_width > 0:
                    pygame.draw.line(surface, 
                                   (*self.color, alpha), 
                                   self.past_positions[i], 
                                   self.past_positions[i+1], 
                                   trail_width)
        
        # Dessiner l'effet de lueur
        glow = pygame.Surface((int(self.glow_radius * 2), int(self.glow_radius * 2)), pygame.SRCALPHA)
        pygame.draw.circle(glow, self.glow_color, 
                         (int(self.glow_radius), int(self.glow_radius)), 
                         int(self.glow_radius))
        
        pos = self.body.position
        surface.blit(glow, (int(pos.x - self.glow_radius), int(pos.y - self.glow_radius)))
        
        # Dessiner la balle
        pygame.draw.circle(surface, self.color, 
                         (int(pos.x), int(pos.y)), 
                         int(self.radius))
        
        # Ajouter un reflet (effet 3D)
        highlight_pos = (int(pos.x - self.radius * 0.3), int(pos.y - self.radius * 0.3))
        highlight_size = self.radius * 0.3
        pygame.draw.circle(surface, WHITE, highlight_pos, int(highlight_size))

class Simulation:
    """Classe principale pour gérer la simulation et l'enregistrement vidéo"""
    def __init__(self, width=WIDTH, height=HEIGHT, fps=FPS, output_path="tiktok_simulation.mp4"):
        pygame.init()
        pygame.mixer.init(44100, -16, 2, 512)
        pygame.mixer.set_num_channels(17)

        self.width = width
        self.height = height
        self.fps = fps
        self.output_path = output_path
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("TikTok Ball Simulation")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Configurer l'espace physique
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        
        # Options de dessin
        self.draw_options.flags = pymunk.SpaceDebugDrawOptions.DRAW_SHAPES
        
        # Créer les murs
        self.create_boundaries()
        
        # Listes d'objets
        self.balls = []
        self.targets = []
        self.particles = []
        
        # Compteur de frames pour la vidéo
        self.frame_count = 0
        
        # Configuration audio
        self.setup_audio()
        
        # Configurer la détection de collision
        self.setup_collision_handlers()
        
        # Fourwriter pour l'enregistrement vidéo
        self.video_writer = None
        
        # Variables pour le timing et les événements
        self.time_elapsed = 0
        self.next_ball_time = 0
        self.next_target_time = 0
        self.next_event_time = 0
        self.next_note_time = 0
        
        # Configurer l'enregistrement vidéo
        self.setup_video_writer()
        
        # Configurer l'enregistrement audio
        self.audio_file = "temp_audio.wav"
        self.audio_frames = []
        
    def setup_audio(self):
        """Configure le système audio"""
        # Charger les sons pour différents événements
        self.sounds_dir = "sounds"
        if not os.path.exists(self.sounds_dir):
            os.makedirs(self.sounds_dir)
            
        # Créer des notes de musique si elles n'existent pas
        self.notes = []
        self.create_synth_notes()
        
        # Notes pour une mélodie pentatonique (agréable quelle que soit la combinaison)
        self.pentatonic_notes = [0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24]  # Do, Ré, Mi, Sol, La sur plusieurs octaves
        
        # Musique de fond
        self.background_music = None
        try:
            self.background_music = pygame.mixer.Sound("sounds/background.wav")
            self.background_music.set_volume(0.3)  # Volume plus bas pour la musique de fond
        except:
            print("Pas de musique de fond trouvée, continuons sans...")
            
        # Canal pour la musique de fond
        self.bg_channel = pygame.mixer.Channel(0)
        
    def create_synth_notes(self):
        """Crée des notes de synthétiseur pour les rebonds et explosions"""
        # Paramètres pour la génération de notes
        sample_rate = 44100
        max_amp = 0.8
        note_duration = 0.5  # en secondes
        
        # Fréquences de base (gamme pentatonique majeure en Do)
        base_freqs = [
            261.63,  # Do
            293.66,  # Ré
            329.63,  # Mi
            392.00,  # Sol
            440.00,  # La
            523.25,  # Do (octave supérieure)
            587.33,  # Ré (octave supérieure)
            659.25,  # Mi (octave supérieure)
            783.99,  # Sol (octave supérieure)
            880.00,  # La (octave supérieure)
            1046.50  # Do (2 octaves au-dessus)
        ]
        
        for i, freq in enumerate(base_freqs):
            note_path = os.path.join(self.sounds_dir, f"note_{i}.wav")
            
            # Si la note n'existe pas déjà, la créer
            if not os.path.exists(note_path):
                # Générer une onde sinusoïdale avec une enveloppe ADSR
                # (Attack, Decay, Sustain, Release)
                num_samples = int(sample_rate * note_duration)
                samples = np.zeros(num_samples, dtype=np.float32)
                
                # Paramètres ADSR (en pourcentage de la durée totale)
                attack = 0.05
                decay = 0.1
                sustain_level = 0.7
                release = 0.2
                
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
                
                # Générer l'onde sinusoïdale et appliquer l'enveloppe
                for j in range(num_samples):
                    t = j / sample_rate
                    # Ajouter une légère modulation pour un son plus riche
                    mod = 1.0 + 0.005 * math.sin(2 * math.pi * 5 * t)
                    samples[j] = max_amp * math.sin(2 * math.pi * freq * mod * t) * envelope[j]
                
                # Ajouter un peu d'harmoniques pour un son plus riche
                harmonics = [0.5, 0.25, 0.125]
                harmonic_freqs = [2, 3, 4]  # 2x, 3x, 4x la fréquence fondamentale
                
                for amp, mult in zip(harmonics, harmonic_freqs):
                    for j in range(num_samples):
                        t = j / sample_rate
                        samples[j] += amp * max_amp * math.sin(2 * math.pi * freq * mult * t) * envelope[j]
                
                # Normaliser pour éviter l'écrêtage
                max_val = np.max(np.abs(samples))
                if max_val > 0:
                    samples = samples / max_val * 0.9
                
                # Convertir en 16 bits
                samples = (samples * 32767).astype(np.int16)
                
                # Créer un fichier WAV stéréo
                stereo_samples = np.column_stack((samples, samples))
                
                from scipy.io import wavfile
                try:
                    wavfile.write(note_path, sample_rate, stereo_samples)
                    print(f"Note créée: {note_path}")
                except ImportError:
                    print("scipy non disponible, utilisation de sons par défaut")
                    # Si scipy n'est pas disponible, on crée un son simple avec pygame
                    sound_array = np.zeros((num_samples, 2), dtype=np.int16)
                    for j in range(num_samples):
                        t = j / sample_rate
                        val = int(32767 * 0.5 * math.sin(2 * math.pi * freq * t))
                        sound_array[j][0] = val
                        sound_array[j][1] = val
                    
                    pygame.sndarray.make_sound(sound_array).save(note_path)
            
            # Charger la note
            try:
                note = pygame.mixer.Sound(note_path)
                note.set_volume(0.7)  # Volume de la note
                self.notes.append(note)
                print(f"Note chargée: {note_path}")
            except:
                print(f"Impossible de charger la note: {note_path}")
                # Créer un son de remplacement si le chargement échoue
                dummy_array = np.zeros((int(44100 * 0.3), 2), dtype=np.int16)
                for j in range(dummy_array.shape[0]):
                    t = j / 44100
                    val = int(32767 * 0.5 * math.sin(2 * math.pi * freq * t))
                    dummy_array[j][0] = val
                    dummy_array[j][1] = val
                
                note = pygame.sndarray.make_sound(dummy_array)
                note.set_volume(0.7)
                self.notes.append(note)
        
        # Sons pour les explosions (plus graves et plus longs)
        self.explosion_sounds = []
        for i in range(3):  # 3 variations d'explosion
            freq = 120 + i * 30  # Fréquences plus basses pour les explosions
            explosion_path = os.path.join(self.sounds_dir, f"explosion_{i}.wav")
            
            if not os.path.exists(explosion_path):
                # Sons plus longs pour les explosions
                explosion_duration = 0.7
                num_samples = int(sample_rate * explosion_duration)
                samples = np.zeros(num_samples, dtype=np.float32)
                
                # Paramètres ADSR plus longs pour les explosions
                attack = 0.05
                decay = 0.2
                sustain_level = 0.5
                release = 0.5
                
                attack_samples = int(attack * num_samples)
                decay_samples = int(decay * num_samples)
                release_samples = int(release * num_samples)
                sustain_samples = num_samples - attack_samples - decay_samples - release_samples
                
                envelope = np.zeros(num_samples)
                envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
                envelope[attack_samples:attack_samples+decay_samples] = np.linspace(1, sustain_level, decay_samples)
                envelope[attack_samples+decay_samples:attack_samples+decay_samples+sustain_samples] = sustain_level
                envelope[attack_samples+decay_samples+sustain_samples:] = np.linspace(sustain_level, 0, release_samples)
                
                # Générer un son plus complexe pour l'explosion
                for j in range(num_samples):
                    t = j / sample_rate
                    # Son de base
                    samples[j] = max_amp * math.sin(2 * math.pi * freq * t) * envelope[j]
                    # Ajouter du bruit pour un effet d'explosion
                    samples[j] += 0.3 * max_amp * random.uniform(-1, 1) * envelope[j]
                    # Ajouter des harmoniques
                    for h in range(1, 5):
                        samples[j] += (0.2 / h) * max_amp * math.sin(2 * math.pi * freq * h * t) * envelope[j]
                
                # Normaliser
                max_val = np.max(np.abs(samples))
                if max_val > 0:
                    samples = samples / max_val * 0.9
                
                # Convertir en 16 bits
                samples = (samples * 32767).astype(np.int16)
                
                # Créer un fichier WAV stéréo
                stereo_samples = np.column_stack((samples, samples))
                
                try:
                    from scipy.io import wavfile
                    wavfile.write(explosion_path, sample_rate, stereo_samples)
                except ImportError:
                    pygame.sndarray.make_sound(stereo_samples).save(explosion_path)
            
            # Charger le son d'explosion
            try:
                explosion = pygame.mixer.Sound(explosion_path)
                explosion.set_volume(0.8)  # Volume plus élevé pour les explosions
                self.explosion_sounds.append(explosion)
            except:
                print(f"Impossible de charger le son d'explosion: {explosion_path}")
                # Son d'explosion par défaut
                dummy_array = np.zeros((int(44100 * 0.5), 2), dtype=np.int16)
                for j in range(dummy_array.shape[0]):
                    t = j / 44100
                    val = int(32767 * 0.5 * math.sin(2 * math.pi * freq * t))
                    dummy_array[j][0] = val
                    dummy_array[j][1] = val
                
                explosion = pygame.sndarray.make_sound(dummy_array)
                explosion.set_volume(0.8)
                self.explosion_sounds.append(explosion)
        
        # Créer des canaux pour jouer plusieurs sons simultanément
        self.note_channels = [pygame.mixer.Channel(i+1) for i in range(16)]  # Canaux 1-16 pour les notes
        self.current_channel = 0
            
    def play_note(self, note_index=None):
        """Joue une note de musique aléatoire ou spécifique"""
        if not self.notes:
            return
            
        if note_index is None:
            # Choisir une note de la gamme pentatonique
            note_index = random.choice(self.pentatonic_notes)
            
        # S'assurer que l'index est dans la plage
        note_index = note_index % len(self.notes)
        
        # Utiliser un canal circulaire pour permettre plusieurs notes simultanées
        channel = self.note_channels[self.current_channel]
        self.current_channel = (self.current_channel + 1) % len(self.note_channels)
        
        # Jouer la note
        channel.play(self.notes[note_index])
            
    def play_explosion_sound(self):
        """Joue un son d'explosion aléatoire"""
        if not self.explosion_sounds:
            return
            
        # Choisir un son d'explosion aléatoire
        sound = random.choice(self.explosion_sounds)
        
        # Utiliser un canal disponible
        channel = self.note_channels[self.current_channel]
        self.current_channel = (self.current_channel + 1) % len(self.note_channels)
        
        # Jouer le son
        channel.play(sound)
        
    def setup_video_writer(self):
        """Configure l'enregistreur vidéo"""
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            self.output_path, 
            fourcc, 
            self.fps, 
            (self.width, self.height)
        )
        
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
        
    def on_ball_hit_wall(self, arbiter, space, data):
        """Gère la collision entre une balle et un mur"""
        # Récupérer la balle impliquée
        ball_shape = arbiter.shapes[0] if arbiter.shapes[0].collision_type == 1 else arbiter.shapes[1]
        
        # Récupérer la vitesse de la balle
        for ball in self.balls:
            if ball.shape == ball_shape:
                # Calculer la force de l'impact
                velocity_magnitude = np.linalg.norm(ball.body.velocity)
                
                # Ne jouer une note que si l'impact est suffisamment fort
                if velocity_magnitude > 300:
                    # Mapper la vitesse à une note
                    # Plus la balle est rapide, plus la note est aiguë
                    note_index = min(int(velocity_magnitude / 200), len(self.pentatonic_notes) - 1)
                    self.play_note(self.pentatonic_notes[note_index])
                
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
                if ball.shape == shape:
                    velocity_magnitude = np.linalg.norm(ball.body.velocity)
                    total_velocity += velocity_magnitude
                    balls_involved.append(ball)
        
        # Ne jouer une note que si l'impact est suffisamment fort
        if total_velocity > 500 and len(balls_involved) == 2:
            # Mapper la vitesse totale à une note
            note_index = min(int(total_velocity / 300), len(self.pentatonic_notes) - 1)
            self.play_note(self.pentatonic_notes[note_index])
        
        # Continuer avec la collision normale
        return True
        
    def on_ball_hit_target(self, arbiter, space, data):
        """Gère la collision entre une balle et une cible"""
        # Récupérer les formes impliquées
        ball_shape, target_shape = arbiter.shapes
        
        # Trouver la cible correspondante
        for target in self.targets:
            if target.shape == target_shape and not target.exploded:
                # Faire exploser la cible
                target.explode()
                
                # Jouer un son d'explosion
                self.play_explosion_sound()
                
                # Créer des particules d'explosion
                num_particles = random.randint(30, 50)
                for _ in range(num_particles):
                    particle = Particle(
                        target.body.position.x, 
                        target.body.position.y,
                        target.color
                    )
                    self.particles.append(particle)
                
                # Ajouter une impulsion à la balle pour effet dynamique
                ball = None
                for b in self.balls:
                    if b.shape == ball_shape:
                        ball = b
                        break
                
                if ball:
                    # Calculer la direction de rebond
                    direction = ball.body.position - target.body.position
                    impulse = direction.normalized() * 1000  # Force de l'impulsion
                    ball.body.apply_impulse_at_local_point(impulse)
                
                break
        
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
        
        # Créer la balle
        ball = Ball(
            self.space, 
            (x, y), 
            radius, 
            mass=mass, 
            velocity=(vx, vy)
        )
        self.balls.append(ball)
        
    def add_random_target(self):
        """Ajoute une cible avec des paramètres aléatoires"""
        # Position
        margin = 100
        x = random.uniform(margin, self.width - margin)
        y = random.uniform(margin, self.height - margin)
        
        # Éviter le chevauchement avec d'autres cibles
        for target in self.targets:
            dist = np.linalg.norm(np.array([x, y]) - np.array([target.body.position.x, target.body.position.y]))
            if dist < 150:  # Si trop proche, trouver une autre position
                return self.add_random_target()
        
        # Taille
        radius = random.uniform(40, 80)
        
        # Créer la cible
        target = CircleTarget(
            self.space, 
            (x, y), 
            radius, 
            is_static=True
        )
        self.targets.append(target)
        
    def update(self, dt):
        """Met à jour l'état de la simulation"""
        # Mettre à jour le temps écoulé
        self.time_elapsed += dt
        
        # Événements périodiques
        if self.time_elapsed >= self.next_ball_time:
            self.add_random_ball()
            self.next_ball_time = self.time_elapsed + random.uniform(0.5, 2.0)
            
        if self.time_elapsed >= self.next_target_time and len(self.targets) < 20:
            self.add_random_target()
            self.next_target_time = self.time_elapsed + random.uniform(1.0, 3.0)
            
        if self.time_elapsed >= self.next_event_time:
            self.trigger_special_event()
            self.next_event_time = self.time_elapsed + random.uniform(5.0, 10.0)
            
        # Jouer des notes musicales périodiquement pour créer une ambiance
        if self.time_elapsed >= self.next_note_time:
            # Jouer une note aléatoire de temps en temps (indépendamment des collisions)
            if random.random() < 0.3:  # 30% de chance
                self.play_note()
            self.next_note_time = self.time_elapsed + random.uniform(1.0, 3.0)
        
        # Mettre à jour les objets
        for ball in self.balls:
            ball.update(dt)
            
        for target in self.targets:
            target.update(dt)
            
        # Mettre à jour les particules
        for particle in self.particles:
            particle.update(dt)
            
        # Supprimer les particules mortes
        self.particles = [p for p in self.particles if not p.is_dead()]
        
        # Supprimer les cibles complètement explosées
        self.targets = [t for t in self.targets if not t.is_fully_exploded()]
        
        # Supprimer les balles sorties de l'écran
        balls_to_remove = []
        for ball in self.balls:
            pos = ball.body.position
            if pos.y > self.height + 100 or pos.x < -100 or pos.x > self.width + 100:
                self.space.remove(ball.body, ball.shape)
                balls_to_remove.append(ball)
                
        for ball in balls_to_remove:
            self.balls.remove(ball)
            
        # Mettre à jour la physique
        self.space.step(dt)
        
    def trigger_special_event(self):
        """Déclenche un événement spécial aléatoire"""
        event_type = random.choice([
            "ball_shower",
            "explode_all",
            "gravity_change",
            "big_ball",
            "musical_scale"  # Nouvel événement musical
        ])
        
        if event_type == "ball_shower":
            # Faire pleuvoir plusieurs balles
            for _ in range(random.randint(5, 10)):
                self.add_random_ball()
                
        elif event_type == "explode_all":
            # Faire exploser toutes les cibles
            for target in self.targets:
                if not target.exploded:
                    target.explode()
                    
                    # Jouer un son d'explosion
                    self.play_explosion_sound()
                    
                    # Créer des particules d'explosion
                    num_particles = random.randint(20, 30)
                    for _ in range(num_particles):
                        particle = Particle(
                            target.body.position.x, 
                            target.body.position.y,
                            target.color
                        )
                        self.particles.append(particle)
                        
        elif event_type == "gravity_change":
            # Changer la gravité temporairement
            original_gravity = self.space.gravity
            self.space.gravity = (random.uniform(-500, 500), random.uniform(-500, 1500))
            
            # Jouer une séquence de notes ascendantes ou descendantes selon la gravité
            if self.space.gravity[1] < 0:  # Gravité vers le haut
                # Jouer une gamme ascendante
                for i in range(5):
                    self.play_note(self.pentatonic_notes[i])
                    time.sleep(0.1)
            else:  # Gravité vers le bas
                # Jouer une gamme descendante
                for i in range(4, -1, -1):
                    self.play_note(self.pentatonic_notes[i])
                    time.sleep(0.1)
            
            # Rétablir après quelques secondes
            pygame.time.set_timer(pygame.USEREVENT, 3000)  # 3 secondes
            
        elif event_type == "big_ball":
            # Créer une très grosse balle
            x = random.uniform(self.width * 0.1, self.width * 0.9)
            y = -100
            radius = random.uniform(80, 120)
            mass = radius * 0.5
            
            vx = random.uniform(-200, 200)
            vy = random.uniform(100, 300)
            
            # Jouer une note grave pour signaler l'arrivée d'une grosse balle
            self.play_note(0)  # Note grave
            
            ball = Ball(
                self.space, 
                (x, y), 
                radius, 
                mass=mass, 
                velocity=(vx, vy)
            )
            self.balls.append(ball)
            
        elif event_type == "musical_scale":
            # Jouer une gamme musicale ascendante complète
            for note in self.pentatonic_notes:
                self.play_note(note)
                time.sleep(0.15)  # Pause entre les notes
        
    def draw(self):
        """Dessine tous les éléments à l'écran"""
        # Remplir l'arrière-plan
        self.screen.fill(BACKGROUND_COLOR)
        
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
            
        self.screen.blit(gradient_surface, (0, 0))
        
        # Ajouter un effet de grille
        grid_spacing = 100
        grid_color = (50, 50, 70, 20)  # Avec transparence
        
        grid_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        for x in range(0, self.width, grid_spacing):
            pygame.draw.line(grid_surface, grid_color, (x, 0), (x, self.height))
            
        for y in range(0, self.height, grid_spacing):
            pygame.draw.line(grid_surface, grid_color, (0, y), (self.width, y))
            
        self.screen.blit(grid_surface, (0, 0))
        
        # Dessiner les cibles
        for target in self.targets:
            target.draw(self.screen)
            
        # Dessiner les balles
        for ball in self.balls:
            ball.draw(self.screen)
            
        # Dessiner les particules
        for particle in self.particles:
            particle.draw(self.screen)
            
        # Afficher le temps restant
        remaining_time = max(0, VIDEO_DURATION - self.time_elapsed)
        font = pygame.font.SysFont('Arial', 36)
        time_text = font.render(f"{int(remaining_time)}", True, WHITE)
        self.screen.blit(time_text, (self.width - 70, 30))
        
        # Afficher des hashtags TikTok
        hashtag_font = pygame.font.SysFont('Arial', 30)
        hashtags = ["#PhysicsSimulation", "#Satisfying", "#TikTokTrend"]
        
        for i, hashtag in enumerate(hashtags):
            hashtag_text = hashtag_font.render(hashtag, True, WHITE)
            self.screen.blit(hashtag_text, (20, 30 + i * 40))
            
        # Mettre à jour l'écran
        pygame.display.flip()
        
    def capture_frame(self):
        """Capture le frame actuel pour la vidéo"""
        # Convertir la surface pygame en image OpenCV
        pygame_surface = pygame.surfarray.array3d(self.screen)
        # Réorganiser les canaux BGR -> RGB pour OpenCV
        cv2_frame = np.swapaxes(pygame_surface, 0, 1)
        # Convertir de RGB à BGR (format OpenCV)
        cv2_frame = cv2.cvtColor(cv2_frame, cv2.COLOR_RGB2BGR)
        # Écrire le frame dans la vidéo
        self.video_writer.write(cv2_frame)
        
    def run(self):
        """Exécute la simulation et enregistre la vidéo"""
        # Initialiser les temps pour les événements
        self.next_ball_time = 0
        self.next_target_time = 1.0
        self.next_event_time = 5.0
        self.next_note_time = 0.5
        
        # Ajouter quelques cibles au départ
        for _ in range(10):
            self.add_random_target()
            
        # Lancer la musique de fond si disponible
        if self.background_music:
            self.bg_channel.play(self.background_music, loops=-1)  # Boucle infinie
            
        print("Démarrage de la simulation...")
        
        # Boucle principale
        while self.running and self.frame_count < TOTAL_FRAMES:
            # Gestionnaire d'événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                elif event.type == pygame.USEREVENT:
                    # Remettre la gravité normale après un événement
                    self.space.gravity = (0, GRAVITY)
                    # Jouer une gamme descendante pour signaler le retour à la normale
                    for i in range(4, -1, -1):
                        self.play_note(self.pentatonic_notes[i])
                        time.sleep(0.1)
            
            # Calcul du temps delta
            dt = 1.0 / self.fps
            
            # Mise à jour de la simulation
            self.update(dt)
            
            # Dessin
            self.draw()
            
            # Capture du frame pour la vidéo
            self.capture_frame()
            
            # Incrémenter le compteur de frames
            self.frame_count += 1
            
            # Afficher la progression
            if self.frame_count % 60 == 0:
                print(f"Progression : {self.frame_count}/{TOTAL_FRAMES} frames ({self.frame_count/TOTAL_FRAMES*100:.1f}%)")
                
            # Limitation des FPS (seulement pour l'aperçu)
            self.clock.tick(self.fps)
            
        # Finaliser la vidéo
        self.video_writer.release()
        pygame.quit()
        
        print(f"Vidéo générée avec succès : {self.output_path}")


# Exécution principale
if __name__ == "__main__":
    # Créer un dossier pour la sortie si nécessaire
    output_dir = "videos"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, f"tiktok_ball_simulation_{int(time.time())}.mp4")
    
    # Lancer la simulation
    sim = Simulation(output_path=output_path)
    sim.run()