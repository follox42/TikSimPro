# video_generators/infinite_circle_simulator.py
"""
Générateur de vidéo basé sur des cercles infinis qui se recyclent
Version avec système de recyclage et rétrécissement progressif
"""

import os
import time
import logging
import numpy as np
import pygame
import pygame.gfxdraw
import random
import math
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import json
import subprocess
import shutil
import threading
from queue import Queue, Full

BACKGROUND = (15, 15, 25)

from core.interfaces import IVideoGenerator, TrendData, AudioEvent, VideoMetadata

logger = logging.getLogger("TikSimPro")

class ScreenShake:
    """Effet de secousse d'écran pour les impacts forts"""
    def __init__(self):
        self.intensity = 0
        self.duration = 0
        self.offset = pygame.math.Vector2(0, 0)
    
    def start(self, intensity=5, duration=0.3):
        self.intensity = intensity
        self.duration = duration
    
    def update(self, dt):
        if self.duration > 0:
            self.duration -= dt
            if self.duration <= 0:
                self.intensity = 0
                self.offset = pygame.math.Vector2(0, 0)
            else:
                self.offset.x = random.uniform(-self.intensity, self.intensity)
                self.offset.y = random.uniform(-self.intensity, self.intensity)
        
    def apply(self, surface, target_surface):
        if self.duration > 0:
            target_surface.blit(surface, (self.offset.x, self.offset.y))
        else:
            target_surface.blit(surface, (0, 0))

class InfiniteCircleSimulator(IVideoGenerator):
    """
    Simulateur de cercles infinis avec recyclage et rétrécissement progressif
    """
    def __init__(self, width=1080, height=1920, fps=60, duration=30.0, 
                 output_path="output/infinite_circle_video.mp4", temp_dir="temp", frames_dir="frames",
                 # Paramètres du système infini
                 ring_count=50,  # Nombre constant de cercles
                 max_passages=1000,  # Maximum de passages avant arrêt
                 min_radius=80,  # Rayon minimum des cercles
                 max_radius=200,  # Rayon maximum initial
                 thickness=15,  # Épaisseur des anneaux
                 gap_angle=60,  # Angle de la trouée
                 rotation_speed=60,  # Vitesse de rotation
                 shrink_factor=0.95,  # Facteur de rétrécissement à chaque recyclage
                 recycling_speed=200,  # Vitesse de déplacement lors du recyclage
                 spacing=80,  # Espacement entre les cercles
                 # Paramètres des balles
                 balls=1,
                 text_balls=None,
                 on_balls_text=True,
                 max_text_length=10,
                 # Paramètres visuels
                 question_text="Infinite Challenge!",
                 color_palette=["#FF0050", "#00F2EA", "#FFFFFF", "#FE2C55", "#25F4EE"],
                 use_gpu_acceleration=True,
                 direct_frames=False,
                 performance_mode="balanced",
                 render_scale=1.0,
                 debug=True,
                 screen_scale=1.0,
                 gravity=400,
                 elasticity=1.02):
        """Initialise le simulateur de cercles infinis"""
        
        # Paramètres de base
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = duration
        self.output_path = output_path
        self.temp_dir = temp_dir
        self.frames_dir = os.path.join(self.temp_dir, frames_dir)
        self.debug = debug
        self.screen_scale = screen_scale
        
        # Paramètres du système infini
        self.ring_count = ring_count
        self.max_passages = max_passages
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.thickness = thickness
        self.gap_angle = gap_angle
        self.rotation_speed = rotation_speed
        self.shrink_factor = shrink_factor
        self.recycling_speed = recycling_speed
        self.spacing = spacing
        
        # État du système
        self.passages_count = 0
        self.recycling_active = True
        self.rings = []
        self.recycling_rings = []  # Anneaux en cours de recyclage
        
        # Paramètres des balles
        self.balls_count = max(1, balls)
        self.text_balls = text_balls if text_balls else []
        self.on_balls_text = on_balls_text
        self.max_text_length = max_text_length
        self.balls = []
        
        # Paramètres visuels
        self.question_text = question_text
        self.color_palette = color_palette
        self.color_rgb_cache = {}
        self.use_gpu_acceleration = use_gpu_acceleration
        self.direct_frames = direct_frames
        self.performance_mode = performance_mode
        self.render_scale = render_scale
        
        # Paramètres physiques
        self.center = None
        self.gravity = pygame.math.Vector2(0, gravity)
        self.elasticity = elasticity
        
        # Gestion des événements audio
        self.audio_events = []
        
        # État de la simulation
        self.current_frame = 0
        self.simulation_running = False
        self.simulation_start_time = 0
        
        # Métadonnées de la vidéo générée
        self.metadata = None
        
        # Effet de secousse d'écran
        self.screen_shake = ScreenShake()
        
        # Font pour le texte
        self.font = None
        self.legend_font = None
        self.question_font = None
        
        # Animation de recyclage
        self.recycling_animation_duration = 2.0  # Durée de l'animation de recyclage
        
        # Système de particules pour les effets
        self.global_particles = []
        
        # Compteur de passage affiché
        self.passage_counter_flash = 0
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure le générateur avec des paramètres spécifiques"""
        try:
            # Appliquer les paramètres fournis
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            # Vérifier la cohérence des paramètres
            if self.text_balls and len(self.text_balls) != self.balls_count:
                logger.warning(f"Le nombre de textes ({len(self.text_balls)}) ne correspond pas au nombre de balles ({self.balls_count}). Ajustement automatique.")
                if len(self.text_balls) > 0:
                    self.balls_count = len(self.text_balls)
                else:
                    self.text_balls = [""] * self.balls_count
            elif not self.text_balls:
                self.text_balls = [""] * self.balls_count
            
            # Calculer les valeurs dérivées
            self.center = pygame.math.Vector2(self.width // 2, self.height // 2)
            
            # Créer les répertoires nécessaires
            os.makedirs(self.temp_dir, exist_ok=True)
            os.makedirs(self.frames_dir, exist_ok=True)
            
            # Nettoyer le répertoire des frames si utilisation directe
            if self.direct_frames:
                for file in os.listdir(self.frames_dir):
                    file_path = os.path.join(self.frames_dir, file)
                    if os.path.isfile(file_path) and file.startswith("frame_"):
                        os.remove(file_path)
            
            # Créer le répertoire de sortie
            output_dir = os.path.dirname(self.output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Précalculer la palette de couleurs
            self.color_rgb_cache = {color: self._hex_to_rgb(color) for color in self.color_palette}
            
            # Calculer le nombre total de frames
            self.total_frames = int(self.fps * self.duration)
            
            # Initialiser les polices
            pygame.font.init()
            self.font = pygame.font.SysFont("Arial", 20, bold=True)
            self.legend_font = pygame.font.SysFont("Arial", 24, bold=True)
            self.question_font = pygame.font.SysFont("Arial", 50, bold=True)
            
            logger.info(f"Simulateur infini configuré: {self.ring_count} cercles, max {self.max_passages} passages")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du simulateur infini: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def set_output_path(self, path: str) -> None:
        """Définit le chemin de sortie pour la vidéo"""
        self.output_path = path
        output_dir = os.path.dirname(path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    def apply_trend_data(self, trend_data: TrendData) -> None:
        """Applique les données de tendances au générateur"""
        # Appliquer la palette de couleurs
        if hasattr(trend_data, 'recommended_settings') and 'color_palette' in trend_data.recommended_settings:
            self.color_palette = trend_data.recommended_settings['color_palette']
            self.color_rgb_cache = {color: self._hex_to_rgb(color) for color in self.color_palette}
            logger.info(f"Palette de couleurs appliquée: {self.color_palette}")
        
        # Appliquer le BPM pour la vitesse de rotation
        if hasattr(trend_data, 'timing_trends') and 'beat_frequency' in trend_data.timing_trends:
            beat_frequency = trend_data.timing_trends['beat_frequency']
            self.rotation_speed = int(360 * (1.0 / beat_frequency) / 4)
            logger.info(f"Vitesse de rotation appliquée: {self.rotation_speed}")
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convertit une couleur hexadécimale en RGB valide pour pygame"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16) 
            b = int(hex_color[4:6], 16)
            return (r, g, b)
        except (ValueError, IndexError):
            # Fallback vers blanc si erreur de conversion
            return (255, 255, 255)
    
    def _initialize_game(self) -> None:
        """Initialise les objets du jeu (anneaux infinis, balles, etc.)"""
        # Réinitialiser les objets
        self.rings = []
        self.recycling_rings = []
        self.balls = []
        self.audio_events = []
        self.passages_count = 0
        self.recycling_active = True
        self.global_particles = []
        
        # Convertir les couleurs hexadécimales en RGB
        colors = [self._hex_to_rgb(color) for color in self.color_palette]
        
        # Créer les anneaux infinis initiaux
        for i in range(self.ring_count):
            # Position radiale basée sur l'index
            ring_radius = self.min_radius + (i * self.spacing)
            
            # Direction de rotation alternée
            rotation_dir = 1 if i % 2 == 0 else -1
            
            # Couleur cyclique
            color = colors[i % len(colors)]
            
            # Angle initial aléatoire
            start_angle = random.randint(0, 360)
            
            ring = InfiniteRing(
                center=self.center,
                radius=ring_radius,
                thickness=self.thickness,
                gap_angle=self.gap_angle,
                rotation_speed=self.rotation_speed * rotation_dir,
                color=color,
                start_angle=start_angle,
                ring_id=i,
                simulator=self
            )
            
            self.rings.append(ring)
        
        # Initialiser les balles
        for i in range(self.balls_count):
            # Position initiale différente pour chaque balle
            angle = (360 / self.balls_count) * i
            rad_angle = np.radians(angle)
            
            start_pos = pygame.math.Vector2(
                self.center.x + np.cos(rad_angle) * 50,
                self.center.y + np.sin(rad_angle) * 50
            )
            
            start_vel = pygame.math.Vector2(
                random.randint(200, 350),
                random.randint(200, 350)
            )
            
            ball_color = colors[i % len(colors)]
            text = self.text_balls[i] if i < len(self.text_balls) else ""
            if len(text) > self.max_text_length:
                text = text[:self.max_text_length - 3] + "..."
            
            ball = InfiniteBall(
                pos=start_pos,
                vel=start_vel,
                radius=20,
                color=ball_color,
                elasticity=self.elasticity,
                text=text,
                font=self.font,
                on_text=self.on_balls_text,
                simulator=self
            )
            self.balls.append(ball)
    
    def _collect_audio_event(self, event: AudioEvent) -> None:
        """Collecte un événement audio"""
        self.audio_events.append(event)
    
    def _recycle_ring(self, ring):
        """Recycle un anneau en le rétrécissant et le repositionnant"""
        if not self.recycling_active:
            return
        
        # Incrémenter le compteur de passages
        self.passages_count += 1
        self.passage_counter_flash = 0.5  # Flash du compteur
        
        logger.info(f"Recyclage de l'anneau {ring.ring_id}, passage {self.passages_count}/{self.max_passages}")
        
        # Vérifier si on a atteint le maximum
        if self.passages_count >= self.max_passages:
            self.recycling_active = False
            logger.info("Maximum de passages atteint, arrêt du recyclage")
            
            # Créer un événement audio de fin
            end_event = AudioEvent(
                event_type="victory",
                time=self.current_frame / self.fps,
                position=(self.center.x, self.center.y),
                params={"end_reason": "max_passages_reached"}
            )
            self._collect_audio_event(end_event)
            return
        
        # Calculer le nouveau rayon (rétrécissement)
        new_radius = ring.radius * self.shrink_factor
        
        # Vérifier que le rayon n'est pas trop petit
        if new_radius < self.min_radius:
            new_radius = self.min_radius
        
        # Créer un nouvel anneau recyclé
        recycled_ring = InfiniteRing(
            center=self.center,
            radius=new_radius,
            thickness=self.thickness,
            gap_angle=self.gap_angle,
            rotation_speed=ring.rotation_speed,
            color=ring.color,
            start_angle=random.randint(0, 360),
            ring_id=ring.ring_id,
            simulator=self,
            is_recycling=True,
            recycling_start_time=self.current_frame / self.fps
        )
        
        # Ajouter à la liste des anneaux en recyclage
        self.recycling_rings.append(recycled_ring)
        
        # Supprimer l'ancien anneau de la liste principale
        if ring in self.rings:
            self.rings.remove(ring)
        
        # Créer des particules d'effet de recyclage
        self._create_recycling_particles(ring.center, ring.radius, ring.color)
        
        # Événement audio de recyclage
        recycle_event = AudioEvent(
            event_type="passage",
            time=self.current_frame / self.fps,
            position=(ring.center.x, ring.center.y),
            params={"passage_count": self.passages_count}
        )
        self._collect_audio_event(recycle_event)
        
        # Secousse d'écran
        self.screen_shake.start(intensity=5, duration=0.2)
    
    def _create_recycling_particles(self, center, radius, color):
        """Crée des particules d'effet lors du recyclage"""
        for _ in range(50):
            # Position aléatoire sur le cercle
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(radius - self.thickness, radius)
            
            pos = (
                center.x + math.cos(angle) * distance,
                center.y + math.sin(angle) * distance
            )
            
            # Vitesse dirigée vers le centre (effet d'implosion)
            vel = pygame.math.Vector2(center.x - pos[0], center.y - pos[1])
            vel = vel.normalize() * random.uniform(100, 300)
            
            # Couleur avec variation (RGB seulement)
            r, g, b = self._ensure_valid_color(color)
            color_var = 30
            particle_color = (
                max(0, min(255, r + random.randint(-color_var, color_var))),
                max(0, min(255, g + random.randint(-color_var, color_var))),
                max(0, min(255, b + random.randint(-color_var, color_var)))
            )
            
            # Propriétés de la particule
            size = random.uniform(3, 8)
            life = random.uniform(0.8, 1.5)
            glow = True
            
            self.global_particles.append(InfiniteParticle(pos, vel, particle_color, size, life, glow))
    
    def _draw_passage_counter(self, surface):
        """Dessine le compteur de passages"""
        if not hasattr(self, 'counter_font'):
            self.counter_font = pygame.font.SysFont("Arial", 36, bold=True)
        
        counter_text = f"Passages: {self.passages_count}/{self.max_passages}"
        
        # Couleur avec effet de flash
        if self.passage_counter_flash > 0:
            flash_intensity = self.passage_counter_flash / 0.5
            color = (
                255,
                int(255 * (1 - flash_intensity)),
                int(255 * (1 - flash_intensity))
            )
        else:
            color = (255, 255, 255)
        
        # Rendu du texte avec ombre
        shadow_surface = self.counter_font.render(counter_text, True, (0, 0, 0))
        text_surface = self.counter_font.render(counter_text, True, color)
        
        # Position en bas à droite
        text_width = text_surface.get_width()
        x = self.width - text_width - 20
        y = self.height - 60
        
        # Dessiner l'ombre puis le texte
        surface.blit(shadow_surface, (x + 2, y + 2))
        surface.blit(text_surface, (x, y))
    
    def _draw_question_text(self, surface):
        """Dessine la question en haut de l'écran"""
        if not self.question_text:
            return
        
        text_lines = self.question_text.splitlines()
        
        for idx, line in enumerate(text_lines):
            # Rendu avec ombre
            shadow_surface = self.question_font.render(line, True, (0, 0, 0))
            text_surface = self.question_font.render(line, True, (255, 255, 255))
            
            # Position centrée en haut
            text_width = text_surface.get_width()
            x = (self.width // 2) - (text_width // 2)
            y = 50 + idx * 60
            
            # Dessiner l'ombre puis le texte
            surface.blit(shadow_surface, (x + 2, y + 2))
            surface.blit(text_surface, (x, y))
    
    def _draw_legend(self, surface):
        """Dessine une légende si l'affichage du texte sur les balles est désactivé"""
        if not self.on_balls_text and any(ball.text for ball in self.balls):
            legend_height = 40 * len(self.balls)
            legend_width = 200
            legend_x = 20
            legend_y = 20
            
            # Créer un fond semi-transparent pour la légende
            legend_surface = pygame.Surface((legend_width, legend_height), pygame.SRCALPHA)
            legend_surface.fill((0, 0, 0, 150))
            
            # Dessiner les entrées de la légende
            for i, ball in enumerate(self.balls):
                if ball.text:
                    # Dessiner un cercle de la couleur de la balle
                    circle_x = 20
                    circle_y = 20 + i * 40
                    pygame.gfxdraw.filled_circle(legend_surface, circle_x, circle_y, 10, ball.color)
                    pygame.gfxdraw.aacircle(legend_surface, circle_x, circle_y, 10, ball.color)
                    
                    # Dessiner le texte associé
                    text_surface = self.legend_font.render(ball.text, True, (255, 255, 255))
                    legend_surface.blit(text_surface, (circle_x + 20, circle_y - 10))
            
            # Appliquer la légende sur la surface principale
            surface.blit(legend_surface, (legend_x, legend_y))
    
    def _draw_fps_counter(self, surface, fps):
        """Affiche un compteur de FPS à l'écran"""
        fps_text = f"FPS: {fps:.1f}"
        fps_surface = self.font.render(fps_text, True, (255, 255, 0))
        surface.blit(fps_surface, (10, int(self.height * self.render_scale) - 30))
    
    def _draw_frame_counter(self, surface, current_frame, total_frames):
        """Affiche un compteur de frames à l'écran"""
        frame_text = f"Frame: {current_frame}/{total_frames}"
        frame_surface = self.font.render(frame_text, True, (255, 255, 0))
        surface.blit(frame_surface, (10, int(self.height * self.render_scale) - 60))
    
    def generate(self) -> Optional[str]:
        """Génère la vidéo de simulation infinie"""
        # Dimensions de rendu
        w, h = int(self.width * self.render_scale), int(self.height * self.render_scale)
        screen_w, screen_h = int(self.width * self.screen_scale), int(self.height * self.screen_scale)

        # Initialisation Pygame et fenêtre
        pygame.init()
        self._initialize_game()
        screen = pygame.display.set_mode((screen_w, screen_h))
        pygame.display.set_caption("Infinite Circle Simulator")

        # Mode direct frames si demandé
        if self.direct_frames:
            logger.info("Mode direct_frames activé")
            if self.generate_direct_frames():
                return self.output_path
            logger.warning("Échec du mode direct, bascule en pipe FFmpeg")

        # Préparation FFmpeg
        ffmpeg_bin = getattr(self, 'ffmpeg_path', None) or shutil.which('ffmpeg')
        if not ffmpeg_bin or not os.path.isfile(ffmpeg_bin):
            logger.error("FFmpeg introuvable")
            pygame.quit()
            return None

        # Construction de la commande FFmpeg
        enc = subprocess.check_output([ffmpeg_bin, '-hide_banner', '-encoders']).decode()
        if 'h264_nvenc' in enc and self.use_gpu_acceleration:
            encoder, preset = 'h264_nvenc', 'p1'
            extra = ['-tune', 'hq', '-rc', 'vbr', '-qmin', '1', '-qmax', '51']
        else:
            encoder, preset, extra = 'libx264', 'ultrafast', []

        cmd = [
            ffmpeg_bin, '-y',
            '-f', 'rawvideo', '-vcodec', 'rawvideo',
            '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(self.fps),
            '-i', '-',
            '-c:v', encoder, '-preset', preset
        ] + extra + [
            '-b:v', getattr(self, 'ffmpeg_bitrate', '8000k'),
            '-maxrate', getattr(self, 'ffmpeg_bitrate', '8000k'),
            '-bufsize', getattr(self, 'ffmpeg_bufsize', '16000k'),
            '-threads', '0', '-pix_fmt', 'yuv420p',
            self.output_path
        ]
        
        logger.info(f"FFmpeg: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        # Thread d'envoi des frames
        q = Queue(maxsize=500)
        def sender():
            while True:
                data = q.get()
                if data is None:
                    break
                try:
                    proc.stdin.write(data)
                except:
                    break
            proc.stdin.close()
        threading.Thread(target=sender, daemon=True).start()

        # Boucle de rendu
        render_surf = pygame.Surface((w, h))
        display_surf = pygame.Surface((w, h))
        dt = 1.0 / self.fps
        clock = pygame.time.Clock()

        for i in range(self.total_frames):
            current_time = i * dt
            self.current_frame = i
            
            # Mise à jour de la simulation
            self.screen_shake.update(dt)
            
            # Mise à jour du flash du compteur
            if self.passage_counter_flash > 0:
                self.passage_counter_flash -= dt
            
            # Mise à jour des anneaux principaux
            for ring in self.rings[:]:  # Copie pour éviter les modifications pendant l'itération
                ring.update(dt, [ball.pos for ball in self.balls])
                
                # Vérifier si l'anneau doit être recyclé
                for ball in self.balls:
                    if ring.check_passage(ball.pos, ball.radius):
                        self._recycle_ring(ring)
                        break
            
            # Mise à jour des anneaux en recyclage
            for recycling_ring in self.recycling_rings[:]:
                recycling_ring.update(dt, [ball.pos for ball in self.balls])
                
                # Vérifier si l'animation de recyclage est terminée
                if recycling_ring.recycling_complete():
                    # Ajouter l'anneau recyclé à la liste principale
                    self.rings.append(recycling_ring)
                    self.recycling_rings.remove(recycling_ring)
            
            # Mise à jour des balles
            for ball in self.balls:
                ball.update(dt, self.gravity, (w, h), self.rings + self.recycling_rings, current_time, self._collect_audio_event)
            
            # Mise à jour des particules globales
            self.global_particles = [p for p in self.global_particles if p.update(dt)]
            
            # Rendu
            render_surf.fill(BACKGROUND)
            
            # Dessiner les anneaux (recyclage en premier pour qu'ils soient derrière)
            for ring in self.recycling_rings:
                ring.draw(render_surf)
            
            for ring in self.rings:
                ring.draw(render_surf)
            
            # Dessiner les particules globales
            for particle in self.global_particles:
                particle.draw(render_surf)
            
            # Dessiner les balles
            for ball in self.balls:
                ball.draw(render_surf)
            
            # Dessiner l'interface
            self._draw_question_text(render_surf)
            self._draw_passage_counter(render_surf)
            self._draw_legend(render_surf)
            
            # Post-processing
            display_surf.fill(BACKGROUND)
            self.screen_shake.apply(render_surf, display_surf)

            if self.debug:
                if i % 30 == 0:
                    self._draw_fps_counter(display_surf, clock.get_fps())
                    self._draw_frame_counter(display_surf, i, self.total_frames)

            # Affichage en direct
            if screen_w != w or screen_h != h:
                scaled_display = pygame.transform.scale(display_surf, (screen_w, screen_h))
                screen.blit(scaled_display, (0, 0))
            else:
                screen.blit(display_surf, (0, 0))
                
            pygame.display.flip()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    return None

            # Envoi à FFmpeg
            raw = pygame.image.tostring(display_surf, 'RGB')
            try:
                q.put_nowait(raw)
            except Full:
                _ = q.get()
                q.put(raw)

            clock.tick(120)

        # Finalisation
        q.put(None)
        try:
            proc.wait(timeout=30)
        except:
            proc.kill()
        pygame.quit()

        # Vérification du résultat
        if os.path.exists(self.output_path) and os.path.getsize(self.output_path) > 1000:
            logger.info(f"Vidéo OK → {self.output_path}")
            return self.output_path

        return None

    def generate_direct_frames(self) -> bool:
        """Génère les frames directement en PNG, puis assemblage vidéo"""
        try:
            # Initialisation Pygame
            pygame.init()
            self._initialize_game()
            
            # Dimensions de rendu avec scaling
            w, h = int(self.width * self.render_scale), int(self.height * self.render_scale)

            # Surface de rendu
            render_surf = pygame.Surface((w, h))
            
            # Variables pour mesurer le temps
            dt = 1.0 / self.fps
            clock = pygame.time.Clock()
            
            # Boucle principale de rendu
            logger.info(f"Début du rendu des frames ({self.total_frames} frames prévues)")
            
            for i in range(self.total_frames):
                current_time = i * dt
                self.current_frame = i
                
                # Mise à jour de la simulation (même logique que generate())
                self.screen_shake.update(dt)
                
                if self.passage_counter_flash > 0:
                    self.passage_counter_flash -= dt
                
                # Mise à jour des anneaux principaux
                for ring in self.rings[:]:
                    ring.update(dt, [ball.pos for ball in self.balls])
                    
                    for ball in self.balls:
                        if ring.check_passage(ball.pos, ball.radius):
                            self._recycle_ring(ring)
                            break
                
                # Mise à jour des anneaux en recyclage
                for recycling_ring in self.recycling_rings[:]:
                    recycling_ring.update(dt, [ball.pos for ball in self.balls])
                    
                    if recycling_ring.recycling_complete():
                        self.rings.append(recycling_ring)
                        self.recycling_rings.remove(recycling_ring)
                
                # Mise à jour des balles
                for ball in self.balls:
                    ball.update(dt, self.gravity, (w, h), self.rings + self.recycling_rings, current_time, self._collect_audio_event)
                
                # Mise à jour des particules globales
                self.global_particles = [p for p in self.global_particles if p.update(dt)]
                
                # Rendu
                render_surf.fill(BACKGROUND)
                
                # Dessiner les objets
                for ring in self.recycling_rings:
                    ring.draw(render_surf)
                
                for ring in self.rings:
                    ring.draw(render_surf)
                
                for particle in self.global_particles:
                    particle.draw(render_surf)
                
                for ball in self.balls:
                    ball.draw(render_surf)
                
                # Dessiner l'interface
                self._draw_question_text(render_surf)
                self._draw_passage_counter(render_surf)
                self._draw_legend(render_surf)
                
                # Afficher les statistiques de performance
                if self.debug:
                    current_fps = clock.get_fps()
                    if i % 30 == 0:
                        self._draw_fps_counter(render_surf, current_fps)
                        self._draw_frame_counter(render_surf, i, self.total_frames)
                
                # Sauvegarder la frame en PNG
                frame_filename = os.path.join(self.frames_dir, f"frame_{i:06d}.png")
                pygame.image.save(render_surf, frame_filename)
                
                if i % 10 == 0:
                    logger.info(f"Frame {i}/{self.total_frames} générée")
                
                # Mise à jour du clock
                clock.tick()
            
            pygame.quit()
            
            # Assemblage des frames en vidéo avec FFmpeg
            logger.info("Assemblage des frames en vidéo...")
            return self._create_video_from_frames()
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération directe des frames: {e}")
            import traceback
            traceback.print_exc()
            pygame.quit()
            return False

    def _create_video_from_frames(self) -> Optional[str]:
        """Crée une vidéo à partir des frames générés"""
        try:
            # Détection FFmpeg
            ffmpeg_bin = getattr(self, 'ffmpeg_path', None) or shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
            if not ffmpeg_bin or not os.path.isfile(ffmpeg_bin):
                logger.error("FFmpeg introuvable : ajoutez-le au PATH ou configurez 'ffmpeg_path'.")
                return False
            
            frame_pattern = os.path.join(self.frames_dir, "frame_%06d.png")
            
            # Construire la commande ffmpeg
            cmd = [
                ffmpeg_bin, '-y',
                '-framerate', str(self.fps),
                '-i', frame_pattern
            ]
            
            # Ajout des paramètres d'encodage selon GPU
            encoders_list = subprocess.check_output([ffmpeg_bin, '-hide_banner', '-encoders']).decode()
            
            if 'h264_nvenc' in encoders_list and self.use_gpu_acceleration:
                # NVIDIA GPU
                cmd.extend([
                    '-c:v', 'h264_nvenc',
                    '-preset', 'p1',
                    '-tune', 'hq',
                    '-rc', 'vbr',
                    '-cq', '23',
                    '-qmin', '1',
                    '-qmax', '51'
                ])
            else:
                # CPU fallback
                cmd.extend([
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', '23'
                ])
            
            # Paramètres communs
            cmd.extend([
                '-pix_fmt', 'yuv420p',
                self.output_path
            ])
            
            # Exécuter la commande
            logger.info(f"Exécution de FFmpeg: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logger.info(f"Vidéo créée avec succès: {self.output_path}")
            return self.output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la vidéo: {e}")
            return None
    
    def get_audio_events(self) -> List[AudioEvent]:
        """Récupère les événements audio générés pendant la simulation"""
        return self.audio_events
    
    def get_metadata(self) -> VideoMetadata:
        """Récupère les métadonnées de la vidéo générée"""
        if not self.metadata:
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


class InfiniteParticle:
    """Particule pour les effets visuels du système infini"""
    
    def __init__(self, pos, vel, color, size, life, glow=False):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.color = self._ensure_valid_color(color)
        self.size = size
        self.life = life
        self.max_life = life
        self.glow = glow
    
    def _ensure_valid_color(self, color) -> Tuple[int, int, int]:
        """S'assure qu'une couleur est valide pour pygame"""
        try:
            if isinstance(color, (tuple, list)):
                if len(color) >= 3:
                    r, g, b = color[0], color[1], color[2]
                    r = max(0, min(255, int(r)))
                    g = max(0, min(255, int(g)))
                    b = max(0, min(255, int(b)))
                    return (r, g, b)
            return (255, 255, 255)
        except (ValueError, TypeError, OverflowError):
            return (255, 255, 255)
    
    def update(self, dt):
        self.pos += self.vel * dt
        self.life -= dt
        
        # Ralentissement progressif
        self.vel *= 0.98
        
        return self.life > 0
    
    def draw(self, surface):
        """Dessine la particule avec couleur pygame valide"""
        if self.life <= 0:
            return
            
        # Facteur d'opacité basé sur la vie restante
        life_factor = self.life / self.max_life
        
        # Ajuster la taille selon la vie
        current_size = int(self.size * life_factor)
        if current_size <= 0:
            return
        
        # Position entière pour éviter les erreurs
        pos_x = int(self.pos.x)
        pos_y = int(self.pos.y)
        
        try:
            # Si la particule doit briller, dessiner un halo
            if self.glow and current_size > 2:
                # Halo externe (plus grand, même couleur)
                glow_radius = current_size + 2
                pygame.gfxdraw.filled_circle(surface, pos_x, pos_y, glow_radius, self.color)
                pygame.gfxdraw.aacircle(surface, pos_x, pos_y, glow_radius, self.color)
            
            # Dessiner la particule principale
            pygame.gfxdraw.filled_circle(surface, pos_x, pos_y, current_size, self.color)
            pygame.gfxdraw.aacircle(surface, pos_x, pos_y, current_size, self.color)
            
        except (ValueError, OverflowError):
            # En cas d'erreur avec les couleurs ou les positions, ignorer cette particule
            pass


class InfiniteBall:
    """Balle pour le système infini (similaire à Ball mais adaptée)"""

    def __init__(self, pos, vel, radius=20, color=(255, 255, 255), elasticity=1.05, 
                 text="", font=None, on_text=True, simulator=None):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.radius = radius
        self.color = self._ensure_valid_color(color)
        self.elasticity = elasticity
        self.simulator = simulator
        
        # Effets visuels
        self.hit_flash = 0.0
        self.collision = False
        self.in_gap = False
        
        # Traînée
        self.trail = []
        self.max_trail = 15
        self.trail_fade = 2.0
        
        # Texte
        self.text = text
        self.font = font
        self.on_text = on_text
        self.text_surface = None
        
        # Prérendre le texte s'il y en a un
        if self.text and self.font and self.on_text:
            self.text_surface = self.font.render(self.text, True, (255, 255, 255))
        
        # Particules d'impact
        self.impact_particles = []

    def _ensure_valid_color(self, color) -> Tuple[int, int, int]:
        """S'assure qu'une couleur est valide pour pygame"""
        try:
            if isinstance(color, (tuple, list)):
                if len(color) >= 3:
                    r, g, b = color[0], color[1], color[2]
                    r = max(0, min(255, int(r)))
                    g = max(0, min(255, int(g)))
                    b = max(0, min(255, int(b)))
                    return (r, g, b)
            return (255, 255, 255)
        except (ValueError, TypeError, OverflowError):
            return (255, 255, 255)

    def create_impact_particles(self, normal):
        """Crée des particules lors d'un impact"""
        impact_point = self.pos - normal * self.radius
        impact_speed = self.vel.length() * 0.3
        
        for _ in range(15):
            angle = random.uniform(-np.pi/2, np.pi/2)
            rot_normal = pygame.math.Vector2(
                normal.x * np.cos(angle) - normal.y * np.sin(angle),
                normal.x * np.sin(angle) + normal.y * np.cos(angle)
            )
            
            vel = rot_normal * random.uniform(impact_speed * 0.5, impact_speed * 2.0)
            
            r, g, b = self.color
            color_var = random.randint(-30, 30)
            color = (
                min(255, max(0, r + color_var + 50)),
                min(255, max(0, g + color_var + 50)),
                min(255, max(0, b + color_var + 50)),
                255
            )
            
            size = random.uniform(2, 6)
            life = random.uniform(0.3, 0.7)
            glow = random.random() < 0.3
            
            self.impact_particles.append(InfiniteParticle(impact_point, vel, color, size, life, glow))

    def update(self, dt, gravity, screen_size, rings, current_time, event_collector):
        """Mise à jour de la balle (similaire à Ball.update mais adaptée)"""
        w, h = screen_size
        
        # Appliquer la gravité
        self.vel += gravity * dt
        
        # Limiter la vitesse maximale
        max_speed = 4000
        if self.vel.length() > max_speed:
            self.vel = self.vel.normalize() * max_speed
        
        # Mouvement simple (peut être amélioré avec CCD si nécessaire)
        self.pos += self.vel * dt
        
        # Collisions avec les bords d'écran
        collision_occurred = False
        
        if self.pos.x - self.radius <= 0:
            self.pos.x = self.radius + 1
            self.vel.x = -self.vel.x * self.elasticity
            self.hit_flash = 0.1
            self.create_impact_particles(pygame.math.Vector2(1, 0))
            collision_occurred = True
        elif self.pos.x + self.radius >= w:
            self.pos.x = w - self.radius - 1
            self.vel.x = -self.vel.x * self.elasticity
            self.hit_flash = 0.1
            self.create_impact_particles(pygame.math.Vector2(-1, 0))
            collision_occurred = True
        
        if self.pos.y - self.radius <= 0:
            self.pos.y = self.radius + 1
            self.vel.y = -self.vel.y * self.elasticity
            self.hit_flash = 0.1
            self.create_impact_particles(pygame.math.Vector2(0, 1))
            collision_occurred = True
        elif self.pos.y + self.radius >= h:
            self.pos.y = h - self.radius - 1
            self.vel.y = -self.vel.y * self.elasticity
            self.hit_flash = 0.1
            self.create_impact_particles(pygame.math.Vector2(0, -1))
            collision_occurred = True
        
        if collision_occurred and self.simulator:
            self.simulator.screen_shake.start(intensity=3, duration=0.1)
        
        # Collisions avec les anneaux (version simplifiée)
        for ring in rings:
            if ring.state in ["gone"]:
                continue
            
            dist = (self.pos - ring.center).length()
            
            # Collision avec le bord extérieur
            if (dist + self.radius > ring.radius - ring.thickness/2 and 
                dist - self.radius < ring.radius + ring.thickness/2):
                
                # Vérifier si on est dans la trouée
                to_ball = self.pos - ring.center
                angle = (-math.degrees(math.atan2(to_ball.y, to_ball.x))) % 360
                
                if ring.is_in_gap(angle):
                    self.in_gap = True
                    continue
                
                # Calculer la normale et rebond
                normal = (self.pos - ring.center).normalize()
                
                # Repositionner la balle
                if dist > ring.radius:
                    self.pos = ring.center + normal * (ring.radius + ring.thickness/2 + self.radius)
                else:
                    self.pos = ring.center + normal * (ring.radius - ring.thickness/2 - self.radius)
                
                # Rebond
                dot_product = self.vel.dot(normal)
                self.vel = self.vel - 2 * dot_product * normal * self.elasticity
                
                # Effets
                self.hit_flash = 0.1
                self.collision = True
                self.create_impact_particles(normal)
                
                # Événement audio
                velocity_magnitude = self.vel.length()
                note_index = min(int(velocity_magnitude / 150), 6)
                octave = min(int(velocity_magnitude / 300), 2)
                
                event = AudioEvent(
                    event_type="note",
                    time=current_time,
                    position=(self.pos.x, self.pos.y),
                    params={"note": note_index, "octave": octave}
                )
                event_collector(event)
                
                break
        
        # Effets visuels
        self.trail.append(pygame.math.Vector2(self.pos))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)
        
        self.impact_particles = [p for p in self.impact_particles if p.update(dt)]
        
        if self.hit_flash > 0:
            self.hit_flash -= dt
        
        # Réinitialiser les états
        self.collision = False
        self.in_gap = False

    def draw(self, surface):
        """Rendu de la balle avec couleurs pygame valides"""
        # Dessiner la traînée
        for i, pos in enumerate(self.trail):
            if len(self.trail) > 0:
                alpha_factor = i / len(self.trail)
                size = int(self.radius * (0.4 + 0.6 * alpha_factor))
                
                if self.hit_flash > 0:
                    trail_color = (255, 255, 255)
                else:
                    r, g, b = self.color
                    brightness = int(50 * alpha_factor)
                    trail_color = (
                        max(0, min(255, r + brightness)), 
                        max(0, min(255, g + brightness)), 
                        max(0, min(255, b + brightness))
                    )
                
                if size > 0:
                    # S'assurer que la couleur est valide
                    safe_color = self.simulator._ensure_valid_color(trail_color) if self.simulator else trail_color
                    pygame.gfxdraw.filled_circle(surface, int(pos.x), int(pos.y), size, safe_color)
                    pygame.gfxdraw.aacircle(surface, int(pos.x), int(pos.y), size, safe_color)
        
        # Dessiner les particules d'impact
        for particle in self.impact_particles:
            particle.draw(surface)
        
        # Dessiner la balle principale
        draw_color = self.color
        
        if self.collision:
            draw_color = (255, 100, 100)
        elif self.in_gap:
            draw_color = (100, 255, 100)
        
        # S'assurer que la couleur de base est valide
        safe_draw_color = self.simulator._ensure_valid_color(draw_color) if self.simulator else draw_color
        
        # Flash blanc lors d'un impact
        if self.hit_flash > 0:
            flash_intensity = self.hit_flash / 0.1
            flash_color = (
                max(0, min(255, safe_draw_color[0] + int(150 * flash_intensity))),
                max(0, min(255, safe_draw_color[1] + int(150 * flash_intensity))),
                max(0, min(255, safe_draw_color[2] + int(150 * flash_intensity)))
            )
            
            glow_radius = int(self.radius * 1.3)
            safe_flash_color = self.simulator._ensure_valid_color(flash_color) if self.simulator else flash_color
            pygame.gfxdraw.filled_circle(surface, int(self.pos.x), int(self.pos.y), glow_radius, safe_flash_color)
            pygame.gfxdraw.aacircle(surface, int(self.pos.x), int(self.pos.y), glow_radius, safe_flash_color)
        
        # Cercle principal avec anti-aliasing
        pygame.gfxdraw.filled_circle(surface, int(self.pos.x), int(self.pos.y), int(self.radius), safe_draw_color)
        pygame.gfxdraw.aacircle(surface, int(self.pos.x), int(self.pos.y), int(self.radius), safe_draw_color)
        
        # Reflet pour donner du volume
        highlight_pos = (int(self.pos.x - self.radius * 0.3), int(self.pos.y - self.radius * 0.3))
        highlight_radius = int(self.radius * 0.4)
        highlight_color = (255, 255, 255)
        pygame.gfxdraw.filled_circle(surface, highlight_pos[0], highlight_pos[1], highlight_radius, highlight_color)
        pygame.gfxdraw.aacircle(surface, highlight_pos[0], highlight_pos[1], highlight_radius, highlight_color)
        
        # Dessiner le texte sur la balle si activé
        if self.text and self.on_text and self.text_surface:
            text_width, text_height = self.text_surface.get_size()
            text_pos = (int(self.pos.x - text_width // 2), int(self.pos.y - text_height // 2))
            
            # Fond noir semi-transparent pour améliorer la lisibilité
            text_bg = pygame.Surface((text_width + 6, text_height + 4), pygame.SRCALPHA)
            text_bg.fill((0, 0, 0, 150))
            surface.blit(text_bg, (text_pos[0] - 3, text_pos[1] - 2))
            
            # Dessiner le texte
            surface.blit(self.text_surface, text_pos)


class InfiniteRing:
    """Anneau pour le système infini avec recyclage"""

    def __init__(self, center, radius, thickness, gap_angle=60, rotation_speed=60, 
                 color=(255, 100, 100), start_angle=0, ring_id=0, simulator=None,
                 is_recycling=False, recycling_start_time=0):
        self.center = center
        self.radius = radius
        self.thickness = thickness
        self.gap_angle = gap_angle
        self.rotation_speed = rotation_speed
        self.color = color
        self.start_angle = start_angle
        self.ring_id = ring_id
        self.simulator = simulator
        
        # État de recyclage
        self.is_recycling = is_recycling
        self.recycling_start_time = recycling_start_time
        self.recycling_duration = 2.0  # Durée de l'animation de recyclage
        
        # État de l'anneau
        self.state = "active"  # "active", "passed", "recycling", "gone"
        self.current_angle = start_angle
        
        # Effets visuels
        self.glow_intensity = 0.0
        self.pulse_timer = 0.0
        self.particles = []
        
        # Animation de couleur
        self.color_shift_timer = 0.0
        self.color_hue_shift = 0.0
        
        # Position de recyclage (pour l'animation)
        self.recycling_progress = 0.0
        self.original_radius = radius
        
    def update(self, dt, ball_positions=None):
        """Mise à jour de l'anneau infini"""
        # Rotation de l'anneau
        self.current_angle = (self.current_angle + self.rotation_speed * dt) % 360
        
        # Timers d'animation
        self.pulse_timer = (self.pulse_timer + dt) % 1.5
        self.color_shift_timer = (self.color_shift_timer + dt) % 3.0
        self.color_hue_shift = (self.color_hue_shift + 30 * dt) % 360
        
        # Animation de recyclage
        if self.is_recycling:
            elapsed = (time.time() - self.recycling_start_time) if hasattr(time, 'time') else 0
            self.recycling_progress = min(1.0, elapsed / self.recycling_duration)
            
            # Animation de "respawn" (apparition progressive)
            if self.recycling_progress < 0.5:
                # Phase d'apparition
                alpha_factor = self.recycling_progress * 2
                self.glow_intensity = 1.0 * alpha_factor
            else:
                # Phase de stabilisation
                self.glow_intensity = 1.0 - (self.recycling_progress - 0.5) * 2
        
        # Halo en fonction de la proximité des balles
        if ball_positions and not self.is_recycling:
            min_dist = float('inf')
            for ball_pos in ball_positions:
                dist = (ball_pos - self.center).length()
                if dist < min_dist:
                    min_dist = dist
            
            # Intensité basée sur la proximité
            proximity = max(0, 1 - abs(min_dist - self.radius) / (self.thickness * 3))
            self.glow_intensity = proximity * 0.6
        
        # Mettre à jour les particules
        self.particles = [p for p in self.particles if p.update(dt)]
        
        # Générer des particules occasionnelles pour l'effet
        if random.random() < 0.02:  # 2% de chance par frame
            self._create_particle()
    
    def _create_particle(self):
        """Crée une particule pour les effets visuels"""
        angle = random.uniform(0, math.pi * 2)
        
        pos = (
            self.center.x + math.cos(angle) * self.radius,
            self.center.y + math.sin(angle) * self.radius
        )
        
        # Vitesse tangentielle
        vel = pygame.math.Vector2(
            -math.sin(angle) * self.rotation_speed,
            math.cos(angle) * self.rotation_speed
        )
        
        # Couleur avec variation
        r, g, b = self.color
        color_var = 20
        color = (
            min(255, max(0, r + random.randint(-color_var, color_var))),
            min(255, max(0, g + random.randint(-color_var, color_var))),
            min(255, max(0, b + random.randint(-color_var, color_var))),
            255
        )
        
        size = random.uniform(2, 5)
        life = random.uniform(0.5, 1.0)
        glow = random.random() < 0.3
        
        self.particles.append(InfiniteParticle(pos, vel, color, size, life, glow))
    
    def check_passage(self, ball_pos, ball_radius):
        """Vérifie si une balle a traversé l'anneau (dans la trouée)"""
        if self.state != "active" or self.is_recycling:
            return False
        
        # Distance de la balle au centre
        dist = (ball_pos - self.center).length()
        
        # Vérifier si la balle est à la bonne distance radiale
        if abs(dist - self.radius) > ball_radius + self.thickness:
            return False
        
        # Vérifier si la balle est dans la trouée
        to_ball = ball_pos - self.center
        angle = (-math.degrees(math.atan2(to_ball.y, to_ball.x))) % 360
        
        return self.is_in_gap(angle)
    
    def is_in_gap(self, angle):
        """Vérifie si un angle est dans la trouée"""
        gap_start = self.current_angle
        gap_end = (self.current_angle + self.gap_angle) % 360
        
        angle = angle % 360
        
        # Gestion du cas où la trouée traverse la ligne 0/360
        if gap_start <= gap_end:
            return gap_start <= angle <= gap_end
        else:
            return angle >= gap_start or angle <= gap_end
    
    def recycling_complete(self):
        """Vérifie si l'animation de recyclage est terminée"""
        return self.is_recycling and self.recycling_progress >= 1.0
    
    def _ensure_valid_color(self, color) -> Tuple[int, int, int]:
        """
        S'assure qu'une couleur est valide pour pygame (tuple RGB d'entiers 0-255)
        
        Args:
            color: Couleur sous différents formats possibles
            
        Returns:
            Tuple RGB valide (r, g, b)
        """
        try:
            # Si c'est déjà un tuple/liste de 3 ou 4 éléments
            if isinstance(color, (tuple, list)):
                if len(color) >= 3:
                    # Prendre seulement RGB (ignorer alpha)
                    r, g, b = color[0], color[1], color[2]
                    # Convertir en entiers et clampter à 0-255
                    r = max(0, min(255, int(r)))
                    g = max(0, min(255, int(g)))
                    b = max(0, min(255, int(b)))
                    return (r, g, b)
            
            # Si c'est un objet pygame.Color
            if hasattr(color, 'r') and hasattr(color, 'g') and hasattr(color, 'b'):
                return (int(color.r), int(color.g), int(color.b))
            
            # Fallback vers une couleur par défaut
            return (255, 255, 255)
            
        except (ValueError, TypeError, OverflowError):
            # En cas d'erreur, retourner blanc
            return (255, 255, 255)
    
    def _hsv_to_rgb(self, h, s, v):
        """Convertit HSV en RGB valide pour pygame"""
        h = h % 360
        h_i = int(h / 60)
        f = h / 60 - h_i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        
        if h_i == 0:
            r, g, b = v, t, p
        elif h_i == 1:
            r, g, b = q, v, p
        elif h_i == 2:
            r, g, b = p, v, t
        elif h_i == 3:
            r, g, b = p, q, v
        elif h_i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        
        # S'assurer que les valeurs sont dans la plage correcte
        final_color = (
            max(0, min(255, int(r * 255))), 
            max(0, min(255, int(g * 255))), 
            max(0, min(255, int(b * 255)))
        )
        return self._ensure_valid_color(final_color)
    
    def get_animated_color(self):
        """Obtient la couleur animée en fonction du temps"""
        r, g, b = self.color
        
        # Animation de pulsation
        pulse_factor = 1.0 + math.sin(2 * math.pi * self.pulse_timer / 1.5) * 0.2
        
        # Animation de teinte pour le recyclage
        if self.is_recycling:
            # Effet arc-en-ciel pendant le recyclage
            hue_shift = self.recycling_progress * 360
            return self._hsv_to_rgb((hue_shift + self.color_hue_shift) % 360, 0.8, pulse_factor)
        else:
            # Couleur normale avec légère variation
            final_color = (
                max(0, min(255, int(r * pulse_factor))),
                max(0, min(255, int(g * pulse_factor))),
                max(0, min(255, int(b * pulse_factor)))
            )
            return self._ensure_valid_color(final_color)
    
    def _hsv_to_rgb(self, h, s, v):
        """Convertit HSV en RGB valide pour pygame"""
        h = h % 360
        h_i = int(h / 60)
        f = h / 60 - h_i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        
        if h_i == 0:
            r, g, b = v, t, p
        elif h_i == 1:
            r, g, b = q, v, p
        elif h_i == 2:
            r, g, b = p, v, t
        elif h_i == 3:
            r, g, b = p, q, v
        elif h_i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        
        # S'assurer que les valeurs sont dans la plage correcte
        final_color = (
            max(0, min(255, int(r * 255))), 
            max(0, min(255, int(g * 255))), 
            max(0, min(255, int(b * 255)))
        )
        return self._ensure_valid_color(final_color)
    
    def draw_filled_arc(self, surface, center, inner_radius, outer_radius, start_angle, end_angle, color):
        """Dessine un arc rempli entre deux rayons"""
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        num_segments = max(5, int(abs(end_angle - start_angle) / 5))
        angle_step = (end_rad - start_rad) / num_segments
        
        points = []
        
        # Bord extérieur
        for i in range(num_segments + 1):
            angle = start_rad + i * angle_step
            x = center[0] + outer_radius * math.cos(angle)
            y = center[1] - outer_radius * math.sin(angle)
            points.append((x, y))
        
        # Bord intérieur (ordre inverse)
        for i in range(num_segments, -1, -1):
            angle = start_rad + i * angle_step
            x = center[0] + inner_radius * math.cos(angle)
            y = center[1] - inner_radius * math.sin(angle)
            points.append((x, y))
        
        # Dessiner le polygone
        if len(points) >= 3:
            pygame.gfxdraw.filled_polygon(surface, points, color)
            pygame.gfxdraw.aapolygon(surface, points, color)
    
    def draw(self, surface):
        """Rendu de l'anneau infini avec couleurs pygame valides"""
        if self.state == "gone":
            return
        
        cx, cy = int(self.center.x), int(self.center.y)
        radius = int(self.radius)
        thickness = int(self.thickness)
        col_rgb = self.get_animated_color()
        
        # Facteur d'opacité pour l'animation de recyclage
        if self.is_recycling:
            if self.recycling_progress < 0.5:
                alpha_factor = self.recycling_progress * 2
            else:
                alpha_factor = 1.0
        else:
            alpha_factor = 1.0
        
        # S'assurer que la couleur est valide pour pygame (RGB seulement)
        col = self._ensure_valid_color(col_rgb)
        
        # Dessiner l'anneau avec trouée
        inner_radius = radius - thickness // 2
        outer_radius = radius + thickness // 2
        
        # Calculer les angles de l'arc (tout sauf la trouée)
        arc_start = (self.current_angle + self.gap_angle) % 360
        arc_end = self.current_angle % 360
        
        # Gérer le cas où l'arc traverse 0°
        if arc_start > arc_end:
            # Dessiner en deux parties
            self.draw_filled_arc(surface, (cx, cy), inner_radius, outer_radius, arc_start, 360, col)
            self.draw_filled_arc(surface, (cx, cy), inner_radius, outer_radius, 0, arc_end, col)
        else:
            self.draw_filled_arc(surface, (cx, cy), inner_radius, outer_radius, arc_start, arc_end, col)
        
        # Halo lumineux
        if self.glow_intensity > 0:
            # Utiliser la même couleur que l'anneau pour éviter les erreurs
            halo_col = col
            
            # Plusieurs cercles pour créer l'effet de halo
            for r in range(inner_radius - 5, outer_radius + 5, 2):
                if r > 0:
                    try:
                        pygame.gfxdraw.aacircle(surface, cx, cy, r, halo_col)
                    except:
                        # En cas d'erreur, ignorer ce cercle de halo
                        pass
        
        # Dessiner les particules
        for particle in self.particles:
            particle.draw(surface)