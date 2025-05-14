# video_generators/circle_simulator.py
"""
Générateur de vidéo basé sur des cercles qui utilise la nouvelle architecture
"""

import os
import time
import logging
import numpy as np
import pygame
import random
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import json
import subprocess

from core.interfaces import IVideoGenerator, TrendData, AudioEvent, VideoMetadata

logger = logging.getLogger("TikSimPro")

class CircleSimulator(IVideoGenerator):
    """
    Simulateur de passages à travers des cercles qui génère une vidéo
    et produit des événements audio à des moments clés
    """
    def __init__(self, width = 1080, height = 1920, fps = 60, duration = 30.0, 
                 output_path = "output/circle_video.mp4", temp_dir = "temp", frames_dir = "frames", 
                 min_radius = 100, gap_radius = 20, nb_rings = 5, thickness = 15, gap_angle = 60, 
                 rotation_speed = 60, color_palette = [ "#FF0050", "#00F2EA",  "#FFFFFF",  "#FE2C55", "#25F4EE"] ):
        """Initialise le simulateur de cercles"""
        # Paramètres par défaut
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = duration
        self.output_path = output_path
        self.temp_dir = temp_dir
        self.frames_dir = os.path.join(self.temp_dir, frames_dir)
        
        # Paramètres du jeu
        self.center = None  # Sera initialisé plus tard
        self.gravity = None  # Sera initialisé plus tard
        self.min_radius = min_radius
        self.gap_radius = gap_radius
        self.nb_rings = nb_rings
        self.thickness = thickness
        self.gap_angle = gap_angle
        self.rotation_speed = rotation_speed
        
        # Objets du jeu
        self.rings = []
        self.ball = None
        self.current_level = 0
        self.game_won = False
        
        # Palette de couleurs (par défaut)
        self.color_palette = color_palette
        self.color_rgb_cache = {}  # Sera rempli plus tard
        
        # Gestion des événements audio
        self.audio_events = []
        
        # État de la simulation
        self.current_frame = 0
        self.simulation_running = False
        self.simulation_start_time = 0
        
        # Métadonnées de la vidéo générée
        self.metadata = None
    
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
            
            # Calculer les valeurs dérivées
            self.center = pygame.math.Vector2(self.width // 2, self.height // 2)
            self.gravity = pygame.math.Vector2(0, 400)
            
            # Créer les répertoires nécessaires
            os.makedirs(self.temp_dir, exist_ok=True)
            os.makedirs(self.frames_dir, exist_ok=True)
            
            # Créer le répertoire de sortie
            output_dir = os.path.dirname(self.output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Précalculer la palette de couleurs
            self.color_rgb_cache = {color: self._hex_to_rgb(color) for color in self.color_palette}
            
            # Calculer le nombre total de frames
            self.total_frames = int(self.fps * self.duration)
            
            logger.info(f"Simulateur configuré: {self.width}x{self.height}, {self.fps} FPS, {self.duration}s")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du simulateur: {e}")
            return False
    
    def set_output_path(self, path: str) -> None:
        """
        Définit le chemin de sortie pour la vidéo
        
        Args:
            path: Chemin du fichier de sortie
        """
        self.output_path = path
        # Créer le répertoire de sortie si nécessaire
        output_dir = os.path.dirname(path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    def apply_trend_data(self, trend_data: TrendData) -> None:
        """
        Applique les données de tendances au générateur
        
        Args:
            trend_data: Données de tendances à appliquer
        """
        # Appliquer la palette de couleurs
        if 'color_palette' in trend_data.recommended_settings:
            self.color_palette = trend_data.recommended_settings['color_palette']
            self.color_rgb_cache = {color: self._hex_to_rgb(color) for color in self.color_palette}
            logger.info(f"Palette de couleurs appliquée: {self.color_palette}")
        
        # Appliquer le BPM pour la vitesse de rotation
        if 'beat_frequency' in trend_data.timing_trends:
            beat_frequency = trend_data.timing_trends['beat_frequency']
            # Convertir en vitesse de rotation (un tour complet tous les N beats)
            self.rotation_speed = int(360 * (1.0 / beat_frequency) / 4)  # Un tour tous les 4 beats
            logger.info(f"Vitesse de rotation appliquée: {self.rotation_speed} (BPM: {60/beat_frequency})")
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """
        Convertit une couleur hexadécimale en RGB
        
        Args:
            hex_color: Couleur au format hexadécimal (#RRGGBB)
            
        Returns:
            Tuple RGB (r, g, b)
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _initialize_game(self) -> None:
        """Initialise les objets du jeu (anneaux, balle, etc.)"""
        # Réinitialiser les objets
        self.rings = []
        self.audio_events = []
        self.current_level = 0
        self.game_won = False
        
        # Convertir les couleurs hexadécimales en RGB
        colors = [self._hex_to_rgb(color) for color in self.color_palette]
        
        # Créer les anneaux
        for i in range(self.nb_rings):
            ring_radius = self.min_radius + i * (self.thickness + self.gap_radius)
            rotation_dir = 1 if i % 2 == 0 else -1  # Alternance du sens de rotation
            
            ring = Ring(
                self.center, 
                outer_radius=ring_radius,
                thickness=self.thickness,
                gap_angle=self.gap_angle,
                rotation_speed=self.rotation_speed * rotation_dir,
                color=colors[i % len(colors)]
            )
            self.rings.append(ring)
        
        # Le premier anneau (le plus intérieur) est un arc qui tourne, les autres sont des cercles
        self.rings[0].state = "arc"
        
        # Initialisation de la balle au centre
        self.ball = Ball(
            pos=self.center,
            vel=pygame.math.Vector2(150, 0),
            radius=20,
            color=(200, 220, 255)  # Bleu clair pour contraste
        )
    
    def _collect_audio_event(self, event: AudioEvent) -> None:
        """
        Collecte un événement audio
        
        Args:
            event: Événement audio à collecter
        """
        self.audio_events.append(event)
    
    def generate(self) -> Optional[str]:
        """
        Génère la vidéo de simulation en utilisant un pipe FFmpeg avec encodage matériel si disponible
        Returns:
            Chemin de la vidéo générée, ou None en cas d'échec
        """
        try:
            import subprocess, shutil, threading
            from queue import Queue, Full

            # Initialisation Pygame et jeu
            pygame.init()
            self._initialize_game()

            # Détection du binaire FFmpeg
            ffmpeg_bin = getattr(self, 'ffmpeg_path', None) or shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
            if not ffmpeg_bin or not os.path.isfile(ffmpeg_bin):
                logger.error("FFmpeg introuvable : ajoutez-le au PATH ou configurez 'ffmpeg_path'.")
                pygame.quit()
                return None

            # Échelle de rendu
            scale = getattr(self, 'video_scale', 1.0)
            w, h = int(self.width * scale), int(self.height * scale)

            # Détection unique des encodeurs disponibles
            encoders_list = subprocess.check_output([ffmpeg_bin, '-hide_banner', '-encoders']).decode()
            # Priorité au NVENC si présent, sinon fallback CPU
            if 'h264_nvenc' in encoders_list:
                encoder = 'h264_nvenc'
            else:
                encoder = 'libx264'
            preset = 'p1' if encoder != 'libx264' else 'ultrafast'

                        # Construction dynamique de la commande FFmpeg
            bitrate = getattr(self, 'ffmpeg_bitrate', '8000k')
            bufsize = getattr(self, 'ffmpeg_bufsize', '16000k')  # généralement 2× le bitrate
            cmd = [
                ffmpeg_bin,
                '-y',
                '-f', 'rawvideo',
                '-pix_fmt', 'rgb24',
                '-s', f'{w}x{h}',
                '-r', str(self.fps),
                '-i', '-',
                '-c:v', encoder,
                '-preset', preset,
                '-rc', 'cbr',
                '-b:v', bitrate,
                '-maxrate', bitrate,
                '-bufsize', bufsize,
                '-threads', '0',
                '-pix_fmt', 'yuv420p',
                self.output_path
            ]

            # Démarrage du processus FFmpeg
            # Démarrage du processus FFmpeg
            ffmpeg_proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

            # Thread d'encodage
            q = Queue(maxsize=500)
            def worker():
                while True:
                    d = q.get()
                    if d is None: break
                    try: ffmpeg_proc.stdin.write(d)
                    except: break
                ffmpeg_proc.stdin.close()
            t = threading.Thread(target=worker,daemon=True)
            t.start()

                        # Surface et loop
            surf = pygame.Surface((w, h))
                        # Boucle de rendu et envoi des données via pipe
            surf = pygame.Surface((w, h))
            dt = 1.0 / self.fps
            for i in range(self.total_frames):
                # logique
                for ring in self.rings:
                    ring.update(dt, self.ball.pos)
                    for e in ring.events:
                        self._collect_audio_event(e)
                    ring.events.clear()
                self.ball.update(dt, self.gravity)
                for idx, ring in enumerate(self.rings):
                    ring.check_collision(self.ball, i*dt, self._collect_audio_event)
                    if idx == self.current_level and ring.state == 'arc':
                        to_ball = self.ball.pos - ring.center
                        ang = (-np.degrees(np.arctan2(to_ball.y, to_ball.x))) % 360
                        if ring.is_in_gap(ang) and abs(to_ball.length() - ring.inner_radius) < self.ball.radius * 1.5:
                            ring.trigger_disappear(i*dt, self._collect_audio_event)
                            self.current_level += 1
                            if self.current_level < len(self.rings):
                                self.rings[self.current_level].activate(i*dt, self._collect_audio_event)
                            else:
                                self.game_won = True
                # rendu
                surf.fill((15, 15, 25))
                for ring in reversed(self.rings):
                    ring.draw(surf)
                self.ball.draw(surf)

                # conversion rapide sans lock : pygame.image.tostring
                data = pygame.image.tostring(surf, 'RGB')
                try:
                    q.put_nowait(data)
                except Full:
                    # file pleine, on drop l'ancienne
                    _ = q.get()
                    q.put(data)

            # fin du flux

            # fin
            q.put(None); t.join(); ffmpeg_proc.wait(); pygame.quit();
            return self.output_path
        except Exception as e:
            logger.error(f"Erreur génération pipe FFmpeg: {e}")
            import traceback; traceback.print_exc()
            pygame.quit(); return None

    def _create_video_from_frames(self) -> Optional[str]:
        """
        Crée une vidéo à partir des frames générés
        
        Returns:
            Chemin de la vidéo créée, ou None en cas d'échec
        """
        try:
            from moviepy.editor import ImageSequenceClip
            
            # Créer la vidéo à partir des frames
            clip = ImageSequenceClip(self.frames_dir, fps=self.fps)
            
            # Écrire la vidéo
            clip.write_videofile(
                self.output_path,
                codec='libx264',
                fps=self.fps,
                audio=False,  # Pas d'audio pour l'instant
                threads=8,
                preset='faster',
                bitrate='3000k'
            )
            
            # Fermer le clip
            clip.close()
            
            return self.output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la vidéo: {e}")
            
            # Méthode alternative avec ffmpeg
            try:
                import subprocess
                frame_pattern = os.path.join(self.frames_dir, "frame_%06d.png")
                
                # Construire la commande ffmpeg
                cmd = [
                    'ffmpeg', '-y',
                    '-framerate', str(self.fps),
                    '-i', frame_pattern,
                    '-c:v', 'libx264',
                    '-profile:v', 'high',
                    '-crf', '23',
                    '-pix_fmt', 'yuv420p',
                    self.output_path
                ]
                
                # Exécuter la commande
                subprocess.run(cmd, check=True)
                
                return self.output_path
                
            except Exception as e2:
                logger.error(f"Erreur lors de la création alternative de la vidéo: {e2}")
                return None
    
    def get_audio_events(self) -> List[AudioEvent]:
        """
        Récupère les événements audio générés pendant la simulation
        
        Returns:
            Liste des événements audio
        """
        return self.audio_events
    
    def get_metadata(self) -> VideoMetadata:
        """
        Récupère les métadonnées de la vidéo générée
        
        Returns:
            Métadonnées de la vidéo
        """
        if not self.metadata:
            # Créer des métadonnées par défaut si non disponibles
            self.metadata = VideoMetadata(
                width=self.width,
                height=self.height,
                fps=self.fps,
                duration=self.duration,
                frame_count=self.current_frame,
                file_path=self.output_path,
                creation_timestamp=time.time()
            )
        
        return self.metadata


class Particle:
    """Particule pour les effets visuels"""
    
    def __init__(self, pos, vel, color, size, life):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
    
    def update(self, dt):
        self.pos += self.vel * dt
        self.life -= dt
        return self.life > 0
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        color = (*self.color[:3], alpha)
        
        # Créer une surface pour la particule avec alpha
        particle_surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, color, (self.size, self.size), self.size)
        
        surface.blit(particle_surf, (self.pos.x - self.size, self.pos.y - self.size))


class Ball:
    """Balle qui rebondit dans les anneaux"""
    
    def __init__(self, pos, vel, radius=20, color=(255, 255, 255), elasticity=1.02):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.radius = radius
        self.color = color
        self.elasticity = elasticity
        self.collision = False
        self.in_gap = False
        self.hit_flash = 0
        self.prev_pos = pygame.math.Vector2(pos)
        self.trail = []
        self.impact_particles = []
    
    def update(self, dt, gravity):
        self.prev_pos = pygame.math.Vector2(self.pos)
        self.vel += gravity * dt
        self.pos += self.vel * dt
        
        # Ajouter la position actuelle à la traînée
        self.trail.append((pygame.math.Vector2(self.pos), self.hit_flash > 0))
        
        # Limiter la taille de la traînée
        if len(self.trail) > 10:
            self.trail.pop(0)
        
        # Mettre à jour le timer de flash
        if self.hit_flash > 0:
            self.hit_flash -= dt
        
        # Mettre à jour les particules d'impact
        self.impact_particles = [p for p in self.impact_particles if p.update(dt)]
        
        # Réinitialiser les états de collision
        self.collision = False
        self.in_gap = False
    
    def create_impact_particles(self, normal):
        """Crée des particules lors d'un impact"""
        impact_point = self.pos - normal * self.radius
        impact_speed = self.vel.length() * 0.2
        
        for _ in range(10):
            # Direction aléatoire autour de la normale réfléchie
            angle = random.uniform(-np.pi/3, np.pi/3)
            rot_normal = pygame.math.Vector2(
                normal.x * np.cos(angle) - normal.y * np.sin(angle),
                normal.x * np.sin(angle) + normal.y * np.cos(angle)
            )
            
            # Vitesse aléatoire
            vel = rot_normal * random.uniform(impact_speed * 0.5, impact_speed * 1.5)
            
            # Couleur blanche avec une teinte de la couleur de la balle
            r, g, b = self.color
            color = (
                min(255, r + 100),
                min(255, g + 100),
                min(255, b + 100),
                255
            )
            
            # Taille et durée de vie aléatoires
            size = random.uniform(2, 5)
            life = random.uniform(0.2, 0.4)
            
            # Ajouter la particule
            self.impact_particles.append(Particle(impact_point, vel, color, size, life))
    
    def draw(self, surface):
        # Dessiner la traînée
        for i, (pos, is_flash) in enumerate(self.trail):
            alpha = int(150 * (i / len(self.trail)))
            size = self.radius * (0.3 + 0.7 * i / len(self.trail))
            
            # Couleur de traînée (normale ou flash)
            if is_flash:
                trail_color = (255, 255, 255, alpha)
            else:
                trail_color = (*self.color, alpha)
            
            # Créer une surface avec transparence pour la traînée
            trail_surf = pygame.Surface((int(size*2), int(size*2)), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, trail_color, (int(size), int(size)), int(size))
            surface.blit(trail_surf, (pos.x - size, pos.y - size))
        
        # Dessiner les particules d'impact
        for particle in self.impact_particles:
            particle.draw(surface)
            
        # Déterminer la couleur en fonction de l'état
        draw_color = self.color
        if self.collision:
            draw_color = (255, 100, 100)  # Rouge en cas de collision
        elif self.in_gap:
            draw_color = (100, 255, 100)  # Vert si dans la trouée
        
        # Flash blanc lors d'un impact
        if self.hit_flash > 0:
            flash_color = (
                min(255, draw_color[0] + int(150 * (self.hit_flash / 0.1))),
                min(255, draw_color[1] + int(150 * (self.hit_flash / 0.1))),
                min(255, draw_color[2] + int(150 * (self.hit_flash / 0.1)))
            )
            pygame.draw.circle(surface, flash_color, self.pos, self.radius * 1.1)
        
        # Dessiner la balle
        pygame.draw.circle(surface, draw_color, self.pos, self.radius)
        
        # Ajouter un reflet pour donner du volume
        highlight_pos = (self.pos.x - self.radius * 0.3, self.pos.y - self.radius * 0.3)
        highlight_radius = self.radius * 0.4
        highlight_surf = pygame.Surface((highlight_radius*2, highlight_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(highlight_surf, (255, 255, 255, 100), (highlight_radius, highlight_radius), highlight_radius)
        surface.blit(highlight_surf, (highlight_pos[0] - highlight_radius, highlight_pos[1] - highlight_radius))


class Ring:
    """Anneau avec trouée pour le passage de la balle"""
    
    def __init__(self, center, outer_radius, thickness, gap_angle=0, rotation_speed=0, color=(255, 100, 100)):
        self.center = center
        self.outer_radius = outer_radius
        self.thickness = thickness
        self.inner_radius = outer_radius - thickness
        self.gap_angle = gap_angle
        self.rotation_speed = rotation_speed
        self.arc_start = 0
        self.color = color
        self.state = "circle"  # "circle", "arc", "disappearing", "gone"
        self.disappear_timer = 1.0
        self.particles = []
        self.glow_intensity = 0
        
        # Événements à collecter
        self.events = []
    
    def update(self, dt, ball_pos=None):
        if self.state == "arc":
            # Mettre à jour la rotation de l'arc
            self.arc_start = (self.arc_start + self.rotation_speed * dt) % 360
            
            # Mise à jour du halo quand la balle est proche
            if ball_pos:
                dist_to_ball = (ball_pos - self.center).length()
                # Intensité basée sur la distance de la balle au bord intérieur
                proximity = max(0, 1 - abs(dist_to_ball - self.inner_radius) / (self.thickness * 2))
                self.glow_intensity = proximity * 0.8  # Max 80% d'intensité
            
        elif self.state == "disappearing":
            # Mettre à jour le timer de disparition
            self.disappear_timer -= dt
            if self.disappear_timer <= 0:
                self.state = "gone"
            
            # Générer des particules pendant la disparition
            if random.random() < 15 * dt:
                self.create_particle()
        
        # Mettre à jour les particules
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def create_particle(self):
        # Choisir un angle aléatoire
        angle = random.uniform(0, np.pi * 2)
        radius = random.uniform(self.inner_radius, self.outer_radius)
        
        # Position basée sur le centre et l'angle
        pos = (
            self.center.x + np.cos(angle) * radius,
            self.center.y + np.sin(angle) * radius
        )
        
        # Vecteur de vélocité s'éloignant du centre
        dir_vec = pygame.math.Vector2(np.cos(angle), np.sin(angle))
        vel = dir_vec * random.uniform(50, 250)
        
        # Variation de couleur
        color_var = 50
        base_color = self.color
        color = (
            min(255, max(0, base_color[0] + random.randint(-color_var, color_var))),
            min(255, max(0, base_color[1] + random.randint(-color_var, color_var))),
            min(255, max(0, base_color[2] + random.randint(-color_var, color_var))),
            255
        )
        
        # Taille et durée de vie aléatoires
        size = random.uniform(2, 6)
        life = random.uniform(0.5, 1.5)
        
        # Créer et ajouter la particule
        self.particles.append(Particle(pos, vel, color, size, life))
    
    def activate(self, current_time, event_collector=None):
        """
        Active l'anneau (passe de cercle à arc)
        
        Args:
            current_time: Temps actuel de la simulation
            event_collector: Fonction de collecte d'événements
        """
        if self.state == "circle":
            self.state = "arc"
            
            # Créer un événement sonore d'activation
            event = AudioEvent(
                event_type="activation",
                time=current_time,
                position=(self.center.x, self.center.y)
            )
            
            # Ajouter l'événement à la liste locale
            self.events.append(event)
            
            # Si un collecteur est fourni, l'utiliser aussi
            if event_collector:
                event_collector(event)
    
    def trigger_disappear(self, current_time, event_collector=None):
        """
        Déclenche la disparition de l'anneau
        
        Args:
            current_time: Temps actuel de la simulation
            event_collector: Fonction de collecte d'événements
        """
        if self.state == "arc":
            self.state = "disappearing"
            
            # Créer un événement sonore d'explosion
            event = AudioEvent(
                event_type="explosion",
                time=current_time,
                position=(self.center.x, self.center.y),
                params={"size": "large"}
            )
            
            # Ajouter l'événement à la liste locale
            self.events.append(event)
            
            # Si un collecteur est fourni, l'utiliser aussi
            if event_collector:
                event_collector(event)
            
            # Générer beaucoup de particules immédiatement
            for _ in range(100):
                self.create_particle()
    
    def get_gap_angles(self):
        """
        Récupère les angles de début et fin de la trouée
        
        Returns:
            Tuple (angle_début, angle_fin)
        """
        gap_start = self.arc_start % 360
        gap_end = (self.arc_start + self.gap_angle) % 360
        return gap_start, gap_end
    
    def is_in_gap(self, angle):
        """
        Vérifie si un angle est dans la trouée
        
        Args:
            angle: Angle à vérifier
            
        Returns:
            True si l'angle est dans la trouée, False sinon
        """
        if self.state != "arc" or self.gap_angle == 0:
            return False
            
        gap_start, gap_end = self.get_gap_angles()
        angle = angle % 360
        
        if gap_start <= gap_end:
            return gap_start <= angle <= gap_end
        else:
            return angle >= gap_start or angle <= gap_end
    
    def check_collision(self, ball: Ball, current_time, event_collector=None):
        """
        Vérifie s'il y a collision entre la balle et l'anneau
        
        Args:
            ball: Balle à vérifier
            current_time: Temps actuel de la simulation
            event_collector: Fonction de collecte d'événements
            
        Returns:
            True s'il y a collision, False sinon
        """
        if self.state in ["disappearing", "gone"]:
            return False
            
        # Vecteur du centre vers la balle
        to_ball = ball.pos - self.center
        dist = to_ball.length()
        
        # Calcul de l'angle de la balle par rapport au centre
        angle = (-np.degrees(np.arctan2(to_ball.y, to_ball.x))) % 360
        
        # Vérifie si la balle traverse la trouée
        if self.state == "arc" and self.is_in_gap(angle) and dist + ball.radius >= self.inner_radius and dist - ball.radius <= self.outer_radius:
            ball.in_gap = True
            
            # Créer un événement sonore de passage uniquement quand on traverse la trouée
            if dist > self.inner_radius and dist < self.inner_radius + ball.radius + 10:
                event = AudioEvent(
                    event_type="passage",
                    time=current_time,
                    position=(ball.pos.x, ball.pos.y),
                    params={"note": 3, "octave": 1}
                )
                
                # Ajouter l'événement à la liste locale
                self.events.append(event)
                
                # Si un collecteur est fourni, l'utiliser aussi
                if event_collector:
                    event_collector(event)
                
            return False
        
        # Vérifie si la balle touche la bordure du cercle
        if dist + ball.radius >= self.inner_radius and dist - ball.radius <= self.outer_radius:
            # Collision avec le bord intérieur
            if abs(dist - self.inner_radius) <= ball.radius:
                # La normale pointe vers l'extérieur (du centre vers la balle)
                normal = to_ball.normalize()
                # Calcul du rebond normal
                dot_product = ball.vel.dot(normal)
                
                # Reflète la vitesse
                ball.vel = ball.vel - 2 * dot_product * normal * ball.elasticity
                
                # Effets visuels
                ball.hit_flash = 0.1
                ball.create_impact_particles(normal)
                self.glow_intensity = 0.5
                ball.collision = True
                
                # Créer un événement sonore de rebond
                # Déterminer la note en fonction de la vitesse
                velocity_magnitude = ball.vel.length()
                note_index = min(int(velocity_magnitude / 150), 6)  # 0-6 pour Do-Si
                octave = min(int(velocity_magnitude / 300), 2)      # 0-2 pour les octaves
                
                event = AudioEvent(
                    event_type="note",
                    time=current_time,
                    position=(ball.pos.x, ball.pos.y),
                    params={"note": note_index, "octave": octave}
                )
                
                # Ajouter l'événement à la liste locale
                self.events.append(event)
                
                # Si un collecteur est fourni, l'utiliser aussi
                if event_collector:
                    event_collector(event)
                
                return True

        return False
    
    def draw(self, surface):
        """
        Dessine l'anneau sur une surface
        
        Args:
            surface: Surface pygame sur laquelle dessiner
        """
        if self.state == "gone":
            # Ne rien dessiner si l'anneau a disparu
            pass
        elif self.state == "circle":
            # Dessine un cercle complet avec effet de halo si activé
            if self.glow_intensity > 0:
                # Dessine un halo autour de l'anneau
                for i in range(5):
                    alpha = int(100 * self.glow_intensity) - i * 20
                    if alpha <= 0:
                        continue
                    glow_color = (*self.color, alpha)
                    
                    # Crée une surface avec transparence
                    outer_glow = pygame.Surface((self.outer_radius*2 + i*4, self.outer_radius*2 + i*4), pygame.SRCALPHA)
                    pygame.draw.circle(outer_glow, glow_color, (outer_glow.get_width()//2, outer_glow.get_height()//2), 
                                      self.outer_radius + i*2, 2)
                    surface.blit(outer_glow, (self.center.x - outer_glow.get_width()//2, self.center.y - outer_glow.get_height()//2))
                    
                    inner_glow = pygame.Surface((self.inner_radius*2 + i*4, self.inner_radius*2 + i*4), pygame.SRCALPHA)
                    pygame.draw.circle(inner_glow, glow_color, (inner_glow.get_width()//2, inner_glow.get_height()//2), 
                                      self.inner_radius - i*2, 2)
                    surface.blit(inner_glow, (self.center.x - inner_glow.get_width()//2, self.center.y - inner_glow.get_height()//2))
            
            # Dessine l'anneau principal
            pygame.draw.circle(surface, self.color, self.center, self.outer_radius, self.thickness)
            
        elif self.state in ["arc", "disappearing"]:
            # Dessine un arc avec trouée
            start_rad = np.radians(self.arc_start + self.gap_angle)
            end_rad = np.radians(self.arc_start + 360)
            
            rect = pygame.Rect(0, 0, self.outer_radius*2, self.outer_radius*2)
            rect.center = self.center
            
            # Ajuster l'alpha si en train de disparaître
            if self.state == "disappearing":
                alpha = int(255 * self.disappear_timer)
                color = (*self.color[:3], alpha)
                
                # Créer une surface avec alpha
                surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.arc(surf, color, 
                               pygame.Rect(0, 0, rect.width, rect.height), 
                               start_rad, end_rad, self.thickness)
                surface.blit(surf, rect.topleft)
            else:
                # Dessine un halo autour de l'arc si activé
                if self.glow_intensity > 0:
                    # Dessine un halo autour de l'arc
                    glow_color = (*self.color, int(100 * self.glow_intensity))
                    glow_surf = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
                    pygame.draw.arc(glow_surf, 
                                   glow_color, 
                                   pygame.Rect(5, 5, rect.width, rect.height), 
                                   start_rad, end_rad, self.thickness + 5)
                    surface.blit(glow_surf, (rect.topleft[0] - 5, rect.topleft[1] - 5))
                
                # Dessine l'arc principal
                pygame.draw.arc(surface, self.color, rect, start_rad, end_rad, self.thickness)
        
        # Dessiner les particules
        for particle in self.particles:
            particle.draw(surface)