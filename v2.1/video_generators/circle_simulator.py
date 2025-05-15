# video_generators/circle_simulator.py
"""
Générateur de vidéo basé sur des cercles qui utilise la nouvelle architecture
"""

import os
import time
import logging
import numpy as np
import pygame
import pygame.gfxdraw  # Ajouté pour l'anti-aliasing
import random
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import json
import subprocess
import shutil
import threading
from queue import Queue, Full

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

class CircleSimulator(IVideoGenerator):
    """
    Simulateur de passages à travers des cercles qui génère une vidéo
    et produit des événements audio à des moments clés
    """
    def __init__(self, width = 1080, height = 1920, fps = 60, duration = 30.0, 
                 output_path = "output/circle_video.mp4", temp_dir = "temp", frames_dir = "frames", 
                 min_radius = 100, gap_radius = 20, nb_rings = 5, thickness = 15, gap_angle = 60, 
                 rotation_speed = 60, color_palette = [ "#FF0050", "#00F2EA",  "#FFFFFF",  "#FE2C55", "#25F4EE"],
                 # Nouveaux paramètres pour les balles
                 balls = 1, text_balls = None, on_balls_text = True, max_text_length = 10,
                 # Paramètres pour éviter l'écran noir
                 use_gpu_acceleration = True,
                 direct_frames = False,
                 performance_mode = "balanced",
                 render_scale = 1.0,
                 debug = True):
        """Initialise le simulateur de cercles"""
        # Paramètres par défaut
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = duration
        self.output_path = output_path
        self.temp_dir = temp_dir
        self.frames_dir = os.path.join(self.temp_dir, frames_dir)
        self.debug = debug
        
        # Paramètres du jeu
        self.center = None  # Sera initialisé plus tard
        self.gravity = None  # Sera initialisé plus tard
        self.min_radius = min_radius
        self.gap_radius = gap_radius
        self.nb_rings = nb_rings
        self.thickness = thickness
        self.gap_angle = gap_angle
        self.rotation_speed = rotation_speed
        
        # Nouveaux paramètres pour les balles
        self.balls_count = max(1, balls)  # Au moins une balle
        self.text_balls = text_balls if text_balls else []
        self.on_balls_text = on_balls_text
        self.max_text_length = max_text_length
        self.use_gpu_acceleration = use_gpu_acceleration
        
        # Paramètres pour éviter l'écran noir
        self.direct_frames = direct_frames
        self.performance_mode = performance_mode
        self.render_scale = render_scale
        
        # Objets du jeu
        self.rings: list[Ring] = []
        self.balls = []  # Liste de balles au lieu d'une seule balle
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
        
        # Effet de secousse d'écran
        self.screen_shake = ScreenShake()
        
        # Effet de vignette pour un look plus cinématique
        self.vignette_intensity = 0.3

        # Font pour le texte
        self.font = None
        self.legend_font = None
    
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
            
            # Vérifier que le nombre de textes correspond au nombre de balles
            if self.text_balls and len(self.text_balls) != self.balls_count:
                logger.warning(f"Le nombre de textes ({len(self.text_balls)}) ne correspond pas au nombre de balles ({self.balls_count}). Ajustement automatique.")
                # Ajuster le nombre de balles pour correspondre au nombre de textes
                if len(self.text_balls) > 0:
                    self.balls_count = len(self.text_balls)
                else:
                    self.text_balls = [""] * self.balls_count
            elif not self.text_balls:
                # Créer des textes vides par défaut
                self.text_balls = [""] * self.balls_count
            
            # Calculer les valeurs dérivées
            self.center = pygame.math.Vector2(self.width // 2, self.height // 2)
            self.gravity = pygame.math.Vector2(0, 400)
            
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
            
            # Initialiser la police pour les textes
            pygame.font.init()
            self.font = pygame.font.SysFont("Arial", 20, bold=True)
            self.legend_font = pygame.font.SysFont("Arial", 24, bold=True)
            
            logger.info(f"Simulateur configuré: {self.width}x{self.height}, {self.fps} FPS, {self.duration}s, {self.balls_count} balles")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du simulateur: {e}")
            import traceback
            traceback.print_exc()
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
        if hasattr(trend_data, 'recommended_settings') and 'color_palette' in trend_data.recommended_settings:
            self.color_palette = trend_data.recommended_settings['color_palette']
            self.color_rgb_cache = {color: self._hex_to_rgb(color) for color in self.color_palette}
            logger.info(f"Palette de couleurs appliquée: {self.color_palette}")
        
        # Appliquer le BPM pour la vitesse de rotation
        if hasattr(trend_data, 'timing_trends') and 'beat_frequency' in trend_data.timing_trends:
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
        """Initialise les objets du jeu (anneaux, balles, etc.)"""
        # Réinitialiser les objets
        self.rings: list[Ring] = []
        self.balls = []  # Liste de balles au lieu d'une seule
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
                color=colors[i % len(colors)],
                simulator=self  # Passer une référence au simulateur
            )
            self.rings.append(ring)
        
        # Le premier anneau (le plus intérieur) est un arc qui tourne, les autres sont des cercles
        self.rings[0].state = "arc"
        
        # Initialisation des balles avec des positions et vitesses différentes
        for i in range(self.balls_count):
            # Calculer un angle différent pour chaque balle
            angle = (360 / self.balls_count) * i
            rad_angle = np.radians(angle)
            
            # Position initiale basée sur l'angle
            start_pos = pygame.math.Vector2(
                self.center.x + np.cos(rad_angle) * 50,
                self.center.y + np.sin(rad_angle) * 50
            )
            
            # Vitesse initiale perpendiculaire à la position
            start_vel = pygame.math.Vector2(
                np.cos(rad_angle + np.pi/2) * 150,
                np.sin(rad_angle + np.pi/2) * 150
            )
            
            # Couleur différente pour chaque balle
            ball_color = colors[i % len(colors)]
            
            # Texte pour cette balle
            text = self.text_balls[i] if i < len(self.text_balls) else ""
            if len(text) > self.max_text_length:
                text = text[:self.max_text_length - 3] + "..."
            
            # Création de la balle
            ball = Ball(
                pos=start_pos,
                vel=start_vel,
                radius=20,
                color=ball_color,
                text=text,
                font=self.font,
                on_text=self.on_balls_text
            )
            self.balls.append(ball)
    
    def _collect_audio_event(self, event: AudioEvent) -> None:
        """
        Collecte un événement audio
        
        Args:
            event: Événement audio à collecter
        """
        self.audio_events.append(event)
    
    def _create_vignette(self, surface):
        w, h = surface.get_size()
        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        max_radius = int(min(w, h) * 0.5)

        # Dessiner le dégradé radial
        for r in range(1, max_radius, 2):
            alpha = int(255 * self.vignette_intensity * (r / max_radius))
            pygame.gfxdraw.filled_circle(
                vignette,
                w // 2, h // 2,
                max_radius - r,
                (0, 0, 0, alpha)
            )

        # Ici, on superpose le noir semi-transparent au lieu de multiplier
        surface.blit(vignette, (0, 0))

    
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
    
    def generate_direct_frames(self) -> bool:
        """Génère les frames directement en PNG, puis assemblage vidéo"""
        try:
            
            # Initialisation Pygame
            pygame.init()
            self._initialize_game()
            
            # Dimensions de rendu avec scaling
            w, h = int(self.width * self.render_scale), int(self.height * self.render_scale)

            # Surfaces de rendu
            render_surf = pygame.Surface((w, h))
            display_surf = pygame.Surface((w, h))
            
            # Variables pour mesurer le temps
            dt = 1.0 / self.fps
            clock = pygame.time.Clock()
            
            # Boucle principale de rendu
            logger.info(f"Début du rendu des frames ({self.total_frames} frames prévues)")
            
            for i in range(self.total_frames):
                # Mise à jour des objets du jeu
                self.screen_shake.update(dt)
                
                for ring in self.rings:
                    ring.update(dt, [ball.pos for ball in self.balls])
                    for e in ring.events:
                        self._collect_audio_event(e)
                    ring.events.clear()
                
                # Mise à jour des balles
                for ball in self.balls:
                    ball.update(dt, self.gravity, (w, h))
                
                # Vérification des collisions
                for ball in self.balls:
                    for idx, ring in enumerate(self.rings):
                        ring.check_collision(ball, i*dt, self._collect_audio_event)
                        if idx == self.current_level and ring.state == 'arc':
                            to_ball = ball.pos - ring.center
                            ang = (-np.degrees(np.arctan2(to_ball.y, to_ball.x))) % 360
                            if ring.is_in_gap(ang) and abs(to_ball.length() - ring.inner_radius) < ball.radius * 1.5:
                                ring.trigger_disappear(i*dt, self._collect_audio_event)
                                self.current_level += 1
                                if self.current_level < len(self.rings):
                                    self.rings[self.current_level].activate(i*dt, self._collect_audio_event)
                                else:
                                    self.game_won = True
                                    self.screen_shake.start(intensity=8, duration=0.5)
                
                # Rendu principal
                render_surf.fill((15, 15, 25))
                
                # Dessiner les objets
                for ring in reversed(self.rings):
                    ring.draw(render_surf)
                
                for ball in self.balls:
                    ball.draw(render_surf)
                
                # Dessiner la légende si nécessaire
                self._draw_legend(render_surf)
                
                # Effets post-processing
                display_surf.fill((15, 15, 25))
                
                # Appliquer la secousse d'écran
                self.screen_shake.apply(render_surf, display_surf)
                display_surf = render_surf

                # Appliquer la vignette
                # self._create_vignette(display_surf)
                
                # Afficher les statistiques de performance
                current_fps = clock.get_fps()
                if i % 30 == 0:
                    self._draw_fps_counter(display_surf, current_fps)
                    self._draw_frame_counter(display_surf, i, self.total_frames)
                
                # Sauvegarder la frame en PNG
                frame_filename = os.path.join(self.frames_dir, f"frame_{i:06d}.png")
                pygame.image.save(display_surf, frame_filename)
                
                if i % 10 == 0:
                    logger.info(f"Frame {i}/{self.total_frames} générée")
                
                self.current_frame = i
                
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
    
    def generate(self) -> Optional[str]:
        """
        Génère la vidéo de simulation en utilisant un pipe FFmpeg ou des frames directes
        Returns:
            Chemin de la vidéo générée, ou None en cas d'échec
        """
        # Dimensions de rendu
        w, h = int(self.width * self.render_scale), int(self.height * self.render_scale)

        # 1) Initialisation Pygame et fenêtre
        pygame.init()
        self._initialize_game()
        screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption("Circle Simulator – Aperçu Pipe FFmpeg")

        # 2) Si direct_frames, on génère d'abord les PNG
        if self.direct_frames:
            logger.info("Mode direct_frames activé")
            if self.generate_direct_frames():
                return self.output_path
            logger.warning("Échec du mode direct, bascule en pipe FFmpeg")

        # 3) Préparation FFmpeg
        ffmpeg_bin = getattr(self, 'ffmpeg_path', None) or shutil.which('ffmpeg')
        if not ffmpeg_bin or not os.path.isfile(ffmpeg_bin):
            logger.error("FFmpeg introuvable")
            pygame.quit()
            return None

        # Construction de la commande (h264_nvenc ou libx264)
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
            '-b:v', getattr(self, 'ffmpeg_bitrate','8000k'),
            '-maxrate', getattr(self, 'ffmpeg_bitrate','8000k'),
            '-bufsize', getattr(self, 'ffmpeg_bufsize','16000k'),
            '-threads','0','-pix_fmt','yuv420p',
            self.output_path
        ]
        logger.info(f"FFmpeg: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        # 4) Thread d’envoi des frames
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

        # 5) Boucle de rendu + affichage + envoi
        render_surf = pygame.Surface((w,h))
        display_surf = pygame.Surface((w,h))
        dt = 1.0/self.fps
        clock = pygame.time.Clock()

        for i in range(self.total_frames):
            render_surf.fill((15,15,25))
            # — Update simulation (anneaux, balles, collisions)
            self.screen_shake.update(dt)
            for ring in self.rings:
                ring.update(dt, [b.pos for b in self.balls])
                for e in ring.events:
                    self._collect_audio_event(e)
                ring.events.clear()
            for ball in self.balls:
                ball.update(dt, self.gravity, (w,h))
            # … (logique de trigger_disappear, etc.)
            for ball in self.balls:
                ball.update(dt, self.gravity, (w, h))

            # collision avec chaque anneau, pour CHAQUE balle
            for ball in self.balls:
                for idx, ring in [(idx, ring) for idx, ring in enumerate(self.rings) if ring.state == "arc"]:
                    collided = ring.check_collision(ball, i*dt, self._collect_audio_event)
                    to_ball = ball.pos - ring.center
                    ang = (-np.degrees(np.arctan2(to_ball.y, to_ball.x))) % 360
                    if ring.is_in_gap(ang) and abs(to_ball.length() - ring.inner_radius) < ball.radius * 1.5:
                        ring.trigger_disappear(i*dt, self._collect_audio_event)
                        self.current_level += 1
                        if self.current_level < len(self.rings):
                            self.rings[self.current_level].activate(i*dt, self._collect_audio_event)
                        else:
                            self.game_won = True

                # --- debug : afficher la trouée de l'anneau actif ---
                if ring.state == "arc" and self.debug:
                    # récupère les angles de début et fin de la trouée
                    gap_start, gap_end = ring.get_gap_angles()

                    # rayon où tracer les lignes (au niveau du bord intérieur)
                    r = ring.inner_radius
                    cx, cy = ring.center.x, ring.center.y

                    # convertit en radians
                    a1 = np.radians(gap_start)
                    a2 = np.radians(gap_end)
                    a3 = np.radians(ang)

                    # calcule les deux points sur le cercle intérieur
                    x1 = cx + r * np.cos(a1)
                    y1 = cy - r * np.sin(a1)   # Pygame a l'axe Y vers le bas
                    x2 = cx + r * np.cos(a2)
                    y2 = cy - r * np.sin(a2)

                    # calcuel de l'angle 
                    x3 = cx + r * np.cos(a3)
                    y3 = cy - r * np.sin(a3)

                    # trace deux lignes radiales en vert vif
                    pygame.draw.line(render_surf, (0,255,0), (cx, cy), (x1, y1), 3)
                    pygame.draw.line(render_surf, (0,255,0), (cx, cy), (x2, y2), 3)

                    # angle
                    pygame.draw.line(render_surf, (0,0,255), (ball.pos.x, ball.pos.y), (x3, y3), 2)

            # — Dessin hors écran
            for ring in reversed(self.rings): ring.draw(render_surf)
            for ball in self.balls: ball.draw(render_surf)
            self._draw_legend(render_surf)

            # — Post-processing
            display_surf.fill((15,15,25))
            self.screen_shake.apply(render_surf, display_surf)

            # self._create_vignette(display_surf)
            if i % 30 == 0:
                self._draw_fps_counter(display_surf, clock.get_fps())
                self._draw_frame_counter(display_surf, i, self.total_frames)

            # — 5a) Affichage en direct
            screen.blit(display_surf, (0,0))
            pygame.display.flip()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    return None

            # — 5b) Envoi à FFmpeg
            raw = pygame.image.tostring(display_surf, 'RGB')
            try:
                q.put_nowait(raw)
            except Full:
                _ = q.get(); q.put(raw)

            self.current_frame = i
            clock.tick(120)

        # 6) Finalisation
        q.put(None)
        try:
            proc.wait(timeout=30)
        except:
            proc.kill()
        pygame.quit()

        # 7) Vérification du résultat
        if os.path.exists(self.output_path) and os.path.getsize(self.output_path)>1000:
            logger.info(f"Vidéo OK → {self.output_path}")
            return self.output_path

        # Fallback en direct si tout échoue
        if self.generate_direct_frames():
            return self.output_path

        return None


    def _create_video_from_frames(self) -> Optional[str]:
        """
        Crée une vidéo à partir des frames générés
        
        Returns:
            Chemin de la vidéo créée, ou None en cas d'échec
        """
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
            elif 'h264_amf' in encoders_list and self.use_gpu_acceleration:
                # AMD GPU
                cmd.extend([
                    '-c:v', 'h264_amf',
                    '-quality', 'balanced',
                    '-rc', 'cqp',
                    '-qp_i', '22',
                    '-qp_p', '24'
                ])
            elif 'h264_qsv' in encoders_list and self.use_gpu_acceleration:
                # Intel GPU
                cmd.extend([
                    '-c:v', 'h264_qsv',
                    '-preset', 'medium',
                    '-global_quality', '23'
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
            
            # Méthode alternative (code original)
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
    
    def __init__(self, pos, vel, color, size, life, glow=False):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.glow = glow  # Particule avec effet de halo
    
    def update(self, dt):
        self.pos += self.vel * dt
        self.life -= dt
        
        # Ralentissement progressif (friction)
        self.vel *= 0.98
        
        return self.life > 0
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        color = (*self.color[:3], alpha)
        
        # Créer une surface pour la particule avec alpha
        particle_surf = pygame.Surface((int(self.size*2.5), int(self.size*2.5)), pygame.SRCALPHA)
        
        # Si la particule doit briller, ajouter un halo
        if self.glow:
            # Halo externe
            glow_radius = int(self.size * 2)
            glow_color = (*self.color[:3], alpha // 3)
            pygame.gfxdraw.filled_circle(particle_surf, glow_radius//2, glow_radius//2, glow_radius//2, glow_color)
            pygame.gfxdraw.aacircle(particle_surf, glow_radius//2, glow_radius//2, glow_radius//2, glow_color)
        
        # Dessiner la particule avec anti-aliasing
        pygame.gfxdraw.filled_circle(particle_surf, int(self.size), int(self.size), int(self.size), color)
        pygame.gfxdraw.aacircle(particle_surf, int(self.size), int(self.size), int(self.size), color)
        
        surface.blit(particle_surf, (int(self.pos.x - self.size), int(self.pos.y - self.size)))


class Ball:
    """Balle qui rebondit dans les anneaux"""
    
    def __init__(self, pos, vel, radius=20, color=(255, 255, 255), elasticity=1.02, text="", font=None, on_text=True):
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
        
        # Paramètres pour une traînée plus longue et visible
        self.trail_length = 15  # Plus de points dans la traînée
        self.trail_fade = 2.0   # Disparition plus lente
        
        # Texte à afficher sur la balle
        self.text = text
        self.font = font
        self.on_text = on_text  # Afficher le texte sur la balle ou non
        self.text_surface = None
        
        # Prérendre le texte s'il y en a un
        if self.text and self.font and self.on_text:
            self.text_surface = self.font.render(self.text, True, (255, 255, 255))
    
    def update(self, dt, gravity, screen_dimensions):
        self.prev_pos = pygame.math.Vector2(self.pos)
        self.vel += gravity * dt
        self.pos += self.vel * dt
        
        # Récupérer les dimensions de l'écran
        screen_width, screen_height = screen_dimensions
        
        # Limiter la vitesse maximale pour éviter les problèmes de physique
        max_speed = 1000  # Vitesse maximale en pixels/seconde
        if self.vel.length() > max_speed:
            self.vel = self.vel.normalize() * max_speed
        
        # Rebond sur les bords horizontaux
        if self.pos.x - self.radius < 0:
            self.pos.x = self.radius
            self.vel.x = -self.vel.x * self.elasticity
            self.hit_flash = 0.1
            self.create_impact_particles(pygame.math.Vector2(1, 0))
        elif self.pos.x + self.radius > screen_width:
            self.pos.x = screen_width - self.radius
            self.vel.x = -self.vel.x * self.elasticity
            self.hit_flash = 0.1
            self.create_impact_particles(pygame.math.Vector2(-1, 0))
        
        # Rebond sur les bords verticaux
        if self.pos.y - self.radius < 0:
            self.pos.y = self.radius
            self.vel.y = -self.vel.y * self.elasticity
            self.hit_flash = 0.1
            self.create_impact_particles(pygame.math.Vector2(0, 1))
        elif self.pos.y + self.radius > screen_height:
            self.pos.y = screen_height - self.radius
            self.vel.y = -self.vel.y * self.elasticity
            self.hit_flash = 0.1
            self.create_impact_particles(pygame.math.Vector2(0, -1))
        
        # Ajouter la position actuelle à la traînée
        self.trail.append((pygame.math.Vector2(self.pos), self.hit_flash > 0))
        
        # Limiter la taille de la traînée
        if len(self.trail) > self.trail_length:
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
        impact_speed = self.vel.length() * 0.3  # Augmenté pour plus d'effet
        
        # Plus de particules pour un effet plus spectaculaire
        for _ in range(20):
            # Direction aléatoire autour de la normale réfléchie
            angle = random.uniform(-np.pi/2, np.pi/2)
            rot_normal = pygame.math.Vector2(
                normal.x * np.cos(angle) - normal.y * np.sin(angle),
                normal.x * np.sin(angle) + normal.y * np.cos(angle)
            )
            
            # Vitesse aléatoire
            vel = rot_normal * random.uniform(impact_speed * 0.5, impact_speed * 2.0)
            
            # Couleur basée sur la couleur de la balle avec variation aléatoire
            r, g, b = self.color
            color_var = random.randint(-30, 30)
            color = (
                min(255, max(0, r + color_var + 50)),
                min(255, max(0, g + color_var + 50)),
                min(255, max(0, b + color_var + 50)),
                255
            )
            
            # Taille et durée de vie aléatoires
            size = random.uniform(2, 6)
            life = random.uniform(0.3, 0.7)
            
            # 30% de chance d'avoir une particule brillante
            glow = random.random() < 0.3
            
            # Ajouter la particule
            self.impact_particles.append(Particle(impact_point, vel, color, size, life, glow))
    
    def draw(self, surface):
        # Dessiner la traînée avec effet de dégradé et anti-aliasing
        for i, (pos, is_flash) in enumerate(self.trail):
            alpha = int(200 * (i / len(self.trail)) ** self.trail_fade)
            size = int(self.radius * (0.3 + 0.7 * i / len(self.trail)))
            
            # Couleur de traînée (normale ou flash)
            if is_flash:
                trail_color = (255, 255, 255, alpha)
            else:
                r, g, b = self.color
                brightness = int(50 * (i / len(self.trail)))
                trail_color = (min(255, r + brightness), min(255, g + brightness), min(255, b + brightness), alpha)
            
            # Dessiner avec anti-aliasing
            if size > 0:
                pygame.gfxdraw.filled_circle(surface, int(pos.x), int(pos.y), size, trail_color)
                pygame.gfxdraw.aacircle(surface, int(pos.x), int(pos.y), size, trail_color)
        
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
            flash_intensity = self.hit_flash / 0.1
            flash_color = (
                min(255, draw_color[0] + int(150 * flash_intensity)),
                min(255, draw_color[1] + int(150 * flash_intensity)),
                min(255, draw_color[2] + int(150 * flash_intensity))
            )
            
            # Dessiner un cercle plus grand pour le flash avec anti-aliasing
            glow_radius = int(self.radius * 1.3)
            pygame.gfxdraw.filled_circle(surface, int(self.pos.x), int(self.pos.y), glow_radius, (*flash_color, 100))
            pygame.gfxdraw.aacircle(surface, int(self.pos.x), int(self.pos.y), glow_radius, (*flash_color, 150))
        
        # Dessiner la balle principale avec anti-aliasing
        pygame.gfxdraw.filled_circle(surface, int(self.pos.x), int(self.pos.y), int(self.radius), draw_color)
        pygame.gfxdraw.aacircle(surface, int(self.pos.x), int(self.pos.y), int(self.radius), draw_color)
        
        # Ajouter le reflet pour donner du volume
        highlight_pos = (int(self.pos.x - self.radius * 0.3), int(self.pos.y - self.radius * 0.3))
        highlight_radius = int(self.radius * 0.4)
        
        # Dessiner le reflet avec anti-aliasing
        pygame.gfxdraw.filled_circle(surface, highlight_pos[0], highlight_pos[1], highlight_radius, (255, 255, 255, 100))
        pygame.gfxdraw.aacircle(surface, highlight_pos[0], highlight_pos[1], highlight_radius, (255, 255, 255, 120))
        
        # Dessiner le texte sur la balle si activé
        if self.text and self.on_text and self.text_surface:
            text_width, text_height = self.text_surface.get_size()
            text_pos = (int(self.pos.x - text_width // 2), int(self.pos.y - text_height // 2))
            
            # Ajouter un petit fond noir avec transparence pour améliorer la lisibilité
            text_bg = pygame.Surface((text_width + 6, text_height + 4), pygame.SRCALPHA)
            text_bg.fill((0, 0, 0, 150))
            surface.blit(text_bg, (text_pos[0] - 3, text_pos[1] - 2))
            
            # Dessiner le texte
            surface.blit(self.text_surface, text_pos)


class Ring:
    """Anneau avec trouée pour le passage de la balle"""
    
    def __init__(self, center, outer_radius, thickness, gap_angle=0, rotation_speed=0, color=(255, 100, 100), simulator=None):
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
        self.simulator = simulator  # Référence au simulateur pour les effets globaux
        
        # Paramètres d'animation
        self.pulse_timer = 0
        self.pulse_period = 1.5  # Période de pulsation en secondes
        self.pulse_amount = 0.2  # Amplitude de pulsation (% de variation)
        
        # Variation de couleur pour une animation plus dynamique
        self.color_shift_timer = 0
        self.color_shift_period = 3.0  # Période de variation de couleur
        self.color_hue_shift = 0  # Décalage de teinte
        
        # Événements à collecter
        self.events = []
    
    def get_simulator(self):
        """Récupère la référence au simulateur principal"""
        return self.simulator
    
    def hsv_to_rgb(self, h, s, v):
        """Convertit HSV en RGB pour les animations de couleur"""
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
        
        return int(r * 255), int(g * 255), int(b * 255)
    
    def get_animated_color(self):
        """Obtient la couleur animée en fonction du temps"""
        # Convertir RGB en HSV
        r, g, b = self.color
        
        # Trouver la teinte dominante (approx.)
        max_val = max(r, g, b)
        if max_val == 0:
            h, s, v = 0, 0, 0
        else:
            delta = max_val - min(r, g, b)
            s = delta / max_val
            v = max_val / 255.0
            
            if delta == 0:
                h = 0
            elif max_val == r:
                h = 60 * (((g - b) / delta) % 6)
            elif max_val == g:
                h = 60 * ((b - r) / delta + 2)
            else:
                h = 60 * ((r - g) / delta + 4)
        
        # Appliquer le décalage de teinte et l'animation de pulsation
        h = (h + self.color_hue_shift) % 360
        v = v * (1 + np.sin(2 * np.pi * self.pulse_timer / self.pulse_period) * self.pulse_amount)
        v = min(1.0, max(0.3, v))  # Limiter la luminosité
        
        # Convertir en RGB
        return self.hsv_to_rgb(h, s, v)
    
    def update(self, dt, ball_positions=None):
        # Mise à jour des timers d'animation
        self.pulse_timer = (self.pulse_timer + dt) % self.pulse_period
        self.color_shift_timer = (self.color_shift_timer + dt) % self.color_shift_period

        # Animation du décalage de teinte
        if self.state == "arc":
            self.color_hue_shift = (self.color_hue_shift + 15 * dt) % 360
        
        if self.state == "arc":
            # Mettre à jour la rotation de l'arc
            self.arc_start = (self.arc_start + self.rotation_speed * dt) % 360
            
            # Mise à jour du halo quand une balle est proche
            if ball_positions:
                # Identifier la balle la plus proche
                min_dist = float('inf')
                closest_ball_pos = None
                
                for ball_pos in ball_positions:
                    dist = (ball_pos - self.center).length()
                    if dist < min_dist:
                        min_dist = dist
                        closest_ball_pos = ball_pos
                
                if closest_ball_pos:
                    # Intensité basée sur la distance de la balle au bord intérieur
                    proximity = max(0, 1 - abs(min_dist - self.inner_radius) / (self.thickness * 2))
                    self.glow_intensity = proximity * 0.8  # Max 80% d'intensité
            
        elif self.state == "disappearing":
            # Mettre à jour le timer de disparition
            self.disappear_timer -= dt
            if self.disappear_timer <= 0:
                self.state = "gone"
            
            # Générer des particules pendant la disparition
            if random.random() < 20 * dt:  # Augmenté pour plus de particules
                self.create_particle(has_glow=True)
        
        # Mettre à jour les particules
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def create_particle(self, has_glow=False):
        """Crée une particule avec des effets améliorés"""
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
        vel = dir_vec * random.uniform(100, 300)  # Vitesse augmentée
        
        # Utiliser la couleur animée pour plus de dynamisme
        base_color = self.get_animated_color()
        
        # Variation de couleur
        color_var = 50
        color = (
            min(255, max(0, base_color[0] + random.randint(-color_var, color_var))),
            min(255, max(0, base_color[1] + random.randint(-color_var, color_var))),
            min(255, max(0, base_color[2] + random.randint(-color_var, color_var))),
            255
        )
        
        # Taille et durée de vie aléatoires
        size = random.uniform(3, 8)  # Particules plus grosses
        life = random.uniform(0.5, 1.5)
        
        # Créer et ajouter la particule
        self.particles.append(Particle(pos, vel, color, size, life, glow=has_glow))
    
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
            
            # Créer beaucoup de particules pour l'activation
            for _ in range(30):
                self.create_particle(has_glow=True)
    
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
            
            # Démarrer une secousse d'écran
            if self.simulator and hasattr(self.simulator, 'screen_shake'):
                self.simulator.screen_shake.start(intensity=10, duration=0.4)
            
            # Générer beaucoup de particules immédiatement
            for _ in range(150):  # Augmenté pour plus d'effet
                self.create_particle(has_glow=True)
    
    def get_gap_angles(self):
        """
        Récupère les angles de début et fin de la trouée
        
        Returns:
            Tuple (angle_début, angle_fin)
        """
        gap_start = -(self.arc_start + self.gap_angle) % 360
        gap_end = -self.arc_start % 360
        
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
                
                # Effet de secousse d'écran basé sur la vitesse d'impact
                impact_force = abs(dot_product) / 200  # Normalisation de la force
                if self.simulator and hasattr(self.simulator, 'screen_shake') and impact_force > 0.2:
                    screen_shake_intensity = min(10, impact_force * 3)
                    self.simulator.screen_shake.start(
                        intensity=screen_shake_intensity, 
                        duration=min(0.2, impact_force * 0.1)
                    )
                
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
        Dessine l'anneau sur une surface avec anti-aliasing et effets améliorés
        
        Args:
            surface: Surface pygame sur laquelle dessiner
        """
        if self.state == "gone":
            # Ne rien dessiner si l'anneau a disparu
            pass
        elif self.state == "circle":
            # Obtenir la couleur animée
            animated_color = self.get_animated_color()
            
            # Dessine un cercle complet avec effet de halo si activé
            if self.glow_intensity > 0:
                # Dessine un halo autour de l'anneau
                for i in range(5):
                    alpha = int(100 * self.glow_intensity) - i * 20
                    if alpha <= 0:
                        continue
                    glow_color = (*animated_color, alpha)
                    
                    # Dessiner les halos externes et internes avec anti-aliasing
                    # Halo externe
                    outer_rad = self.outer_radius + i*2
                    pygame.gfxdraw.aacircle(surface, int(self.center.x), int(self.center.y), outer_rad, glow_color)
                    
                    # Halo interne
                    inner_rad = self.inner_radius - i*2
                    if inner_rad > 0:
                        pygame.gfxdraw.aacircle(surface, int(self.center.x), int(self.center.y), inner_rad, glow_color)
            
            # Dessiner l'anneau principal avec anti-aliasing
            # Pour un anneau, nous dessinons deux cercles: externe et interne
            pygame.gfxdraw.aacircle(surface, int(self.center.x), int(self.center.y), self.outer_radius, animated_color)
            
            # Remplir l'anneau avec la couleur
            for r in range(self.thickness):
                rad = self.inner_radius + r
                pygame.gfxdraw.circle(surface, int(self.center.x), int(self.center.y), rad, animated_color)
            
            # Dessiner le cercle interne pour créer le trou de l'anneau
            pygame.gfxdraw.aacircle(surface, int(self.center.x), int(self.center.y), self.inner_radius, animated_color)
            
        elif self.state in ["arc", "disappearing"]:
            # Obtenir la couleur animée
            animated_color = self.get_animated_color()
            
            # Ajuster l'alpha si en train de disparaître
            if self.state == "disappearing":
                alpha = int(255 * self.disappear_timer)
                animated_color = (*animated_color[:3], alpha)
            
            # Dessiner l'arc avec des points anti-aliasés (technique alternative)
            start_angle = np.radians(self.arc_start + self.gap_angle)
            end_angle = np.radians(self.arc_start + 360)
            
            # Si l'arc fait un tour presque complet, dessiner avec plus de points
            # pour une meilleure qualité
            num_points = 120  # Plus de points pour un arc plus lisse
            
            for r in range(self.thickness):
                radius = self.inner_radius + r
                points = []
                
                # Calculer les points de l'arc
                for i in range(num_points + 1):
                    angle = start_angle + (end_angle - start_angle) * (i / num_points)
                    x = self.center.x + radius * np.cos(angle)
                    y = self.center.y + radius * np.sin(angle)
                    points.append((int(x), int(y)))
                
                # Dessiner l'arc avec des lignes AA
                if len(points) > 1:
                    for i in range(len(points) - 1):
                        x1, y1 = points[i]
                        x2, y2 = points[i + 1]
                        pygame.gfxdraw.line(surface, x1, y1, x2, y2, animated_color)
            
            # Dessiner le halo si nécessaire
            if self.glow_intensity > 0 and self.state == "arc":
                glow_color = (*animated_color[:3], int(100 * self.glow_intensity))
                glow_radius = self.inner_radius + self.thickness // 2
                
                for i in range(3):  # Trois couches de halo
                    alpha = int(80 * self.glow_intensity) - i * 20
                    if alpha <= 0:
                        continue
                        
                    glow_color = (*animated_color[:3], alpha)
                    glow_radius = self.inner_radius + self.thickness // 2 + i * 3
                    
                    # Dessiner le halo avec des points
                    for i in range(num_points + 1):
                        angle = start_angle + (end_angle - start_angle) * (i / num_points)
                        x = self.center.x + glow_radius * np.cos(angle)
                        y = self.center.y + glow_radius * np.sin(angle)
                        pygame.gfxdraw.circle(surface, int(x), int(y), 1, glow_color)
        
        # Dessiner les particules
        for particle in self.particles:
            particle.draw(surface)