# video_generators/circle_simulator.py
"""
Générateur de vidéo basé sur des cercles qui utilise la nouvelle architecture
Version fusionnée avec CCD et rendu amélioré
"""

import os
import time
import logging
import numpy as np
import pygame
import pygame.gfxdraw  # Ajouté pour l'anti-aliasing
import random
import math
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import json
import subprocess
import shutil
import threading
from queue import Queue, Full
import math, pygame, pygame.gfxdraw as aa

BACKGROUND = (15, 15, 25)          # même couleur que render_surf.fill

from core.format_data import IVideoGenerator, TrendData, AudioEvent, VideoMetadata

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
                 rotation_speed = 60, random_arc=True, color_palette = [ "#FF0050", "#00F2EA",  "#FFFFFF",  "#FE2C55", "#25F4EE"],
                 # Nouveaux paramètres pour les balles
                 balls = 1, text_balls = None, on_balls_text = True, max_text_length = 10,
                 # Paramètre pour la question en haut
                 question_text = "Who's the dumbest?",
                 # Paramètres pour éviter l'écran noir
                 use_gpu_acceleration = True,
                 direct_frames = False,
                 performance_mode = "balanced",
                 render_scale = 1.0,
                 all_arc = True,  # Nouveau paramètre (True par défaut comme demandé)
                 debug = True, screen_scale = 1.0,
                 start_angle = 30,
                 gap_speed = 10,
                 gravity=400,
                 elasticity=1.02):
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
        self.screen_scale = screen_scale
        self.start_angle = start_angle
        self.gap_speed = gap_speed
        self.elasticity = elasticity

        # Paramètres du jeu
        self.center = None  # Sera initialisé plus tard
        self.gravity = pygame.math.Vector2(0, gravity)
        self.min_radius = min_radius
        self.gap_radius = gap_radius
        self.nb_rings = nb_rings
        self.thickness = thickness
        self.gap_angle = gap_angle
        self.rotation_speed = rotation_speed
        self.random_arc = random_arc
        self.all_arc = all_arc  # Nouveau paramètre

        # Nouveaux paramètres pour les balles
        self.balls_count = max(1, balls)  # Au moins une balle
        self.text_balls = text_balls if text_balls else []
        self.on_balls_text = on_balls_text
        self.max_text_length = max_text_length
        self.use_gpu_acceleration = use_gpu_acceleration
        
        # Paramètre pour la question en haut
        self.question_text = question_text
        
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
        
        # Animation de victoire
        self.winner_ball = None
        self.victory_animation_time = 0
        self.victory_animation_duration = 3.0  # Durée de l'animation en secondes
        self.victory_particles = []
        self.victory_flash = 0
    
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
        self.winner_ball = None
        self.victory_animation_time = 0
        self.victory_particles = []
        
        # Convertir les couleurs hexadécimales en RGB
        colors = [self._hex_to_rgb(color) for color in self.color_palette]
        
        # Créer les anneaux
        for i in range(self.nb_rings):
            ring_radius = self.min_radius + i * (self.thickness + self.gap_radius)
            rotation_dir = 1 
            
            ring = Ring(
                self.center, 
                outer_radius=ring_radius,
                thickness=self.thickness,
                gap_angle=self.gap_angle,
                rotation_speed=self.rotation_speed * rotation_dir + self.gap_speed * i,
                color=colors[i % len(colors)],
                simulator=self,  # Passer une référence au simulateur
                random_start=self.random_arc,
                start_angle = self.start_angle
            )
            self.rings.append(ring)
        
        # Configurer les anneaux comme arcs si all_arc est activé
        if self.all_arc:
            # Tous les anneaux commencent comme des arcs
            for ring in self.rings:
                ring.state = "arc"
        else:
            # Seulement le premier anneau (le plus intérieur) est un arc
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
                random.randint(200, 350),
                random.randint(200, 350)
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
                elasticity=self.elasticity,
                text=text,
                font=self.font,
                on_text=self.on_balls_text,
                simulator=self  # Passer une référence au simulateur
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
    
    def _draw_question_text(self, surface):
        """Dessine la question en haut de l'écran"""
        if not self.question_text:
            return
            
        # Créer une police plus grande pour la question
        if not hasattr(self, 'question_font') or self.question_font is None:
            self.question_font = pygame.font.SysFont("Arial", 50, bold=True)
        texts = self.question_text.splitlines()
        
        text_surface = []
        shadow_surface = []
        
        for idx, line in enumerate(texts):
            text_surface.append(self.question_font.render(line, True, (255, 255, 255)))
            shadow_surface.append(self.question_font.render(line, True, (0, 0, 0)))
        
        text_x = []
        # Positionner le texte en haut au centre
        for text in text_surface:
            text_width = text.get_width()
            text_x.append((self.width // 2) - (text_width // 2))
        
        gap = 20
        # Dessiner l'ombre puis le texte
        for idx in reversed(range(len(text_surface))):
            idx_rev = len(text_surface) - idx - 1
            pos_y = self.height // 2 - self.rings[-1].outer_radius - 50 - idx * 50 - gap
            surface.blit(shadow_surface[idx_rev], (text_x[idx_rev] + 2, pos_y))
            surface.blit(text_surface[idx_rev], (text_x[idx_rev], pos_y - 2))
    
    def _draw_victory_animation(self, surface, current_time):
        """Dessine l'animation de victoire si une balle a gagné"""
        if not self.winner_ball or self.victory_animation_time <= 0:
            return
            
        # Calculer le temps écoulé de l'animation
        elapsed = current_time - self.victory_animation_time
        if elapsed > self.victory_animation_duration:
            return
            
        # Facteur d'animation (0 à 1)
        animation_factor = min(1.0, elapsed / self.victory_animation_duration)
        
        # Créer une police plus grande pour le message de victoire
        if not hasattr(self, 'victory_font') or self.victory_font is None:
            self.victory_font = pygame.font.SysFont("Arial", 80, bold=True)
        
        # Texte de victoire
        winner_name = self.winner_ball.text if self.winner_ball.text else "Ball"
        victory_text = f"{winner_name} wins!"
        
        # Effet de zoom et opacité
        scale = 0.5 + 1.0 * animation_factor
        alpha = int(255 * min(1.0, animation_factor * 2))
        
        # Rendu du texte
        text_surface = self.victory_font.render(victory_text, True, (255, 255, 255))
        
        # Créer une surface avec alpha pour pouvoir ajuster l'opacité
        scaled_width = int(text_surface.get_width() * scale)
        scaled_height = int(text_surface.get_height() * scale)
        
        # Surface temporaire pour le scaling
        temp_surface = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
        
        # Redimensionner et dessiner le texte
        pygame.transform.scale(text_surface, (scaled_width, scaled_height), temp_surface)
        
        # Ajuster l'alpha
        temp_surface.set_alpha(alpha)
        
        # Positionner au centre
        center_x = (self.width // 2) - (scaled_width // 2)
        center_y = (self.height // 2) - (scaled_height // 2)
        
        # Dessiner avec un effet de pulsation
        pulse = 1.0 + 0.1 * math.sin(elapsed * 10)
        pulse_width = int(scaled_width * pulse)
        pulse_height = int(scaled_height * pulse)
        
        # Dessiner le texte avec pulsation
        pulse_surface = pygame.transform.scale(temp_surface, (pulse_width, pulse_height))
        surface.blit(pulse_surface, 
                    (center_x - (pulse_width - scaled_width)//2, 
                     center_y - (pulse_height - scaled_height)//2))
        
        # Ajouter des particules pour l'effet de victoire
        if random.random() < 0.3:  # Contrôle la densité de particules
            for _ in range(5):
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(100, 300) * animation_factor
                pos_x = center_x + scaled_width/2 + math.cos(angle) * distance
                pos_y = center_y + scaled_height/2 + math.sin(angle) * distance
                
                # Vélocité s'éloignant du centre
                vel_x = math.cos(angle) * random.uniform(50, 200)
                vel_y = math.sin(angle) * random.uniform(50, 200)
                
                # Couleur aléatoire parmi la palette
                color = self._hex_to_rgb(random.choice(self.color_palette))
                
                # Créer une particule avec halo
                size = random.uniform(5, 15)
                life = random.uniform(0.5, 1.5)
                
                self.victory_particles.append(Particle(
                    (pos_x, pos_y), 
                    (vel_x, vel_y), 
                    color, size, life, True
                ))
        
        # Mettre à jour et dessiner les particules
        self.victory_particles = [p for p in self.victory_particles if p.update(1/self.fps)]
        for particle in self.victory_particles:
            particle.draw(surface)
        
        # Effet de flash global si l'animation vient de commencer
        if elapsed < 0.3:
            flash_alpha = int(255 * (1.0 - elapsed / 0.3))
            flash_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash_surface.fill((255, 255, 255, flash_alpha))
            surface.blit(flash_surface, (0, 0))

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
                
                # Mise à jour des balles avec le nouveau système CCD
                for ball in self.balls:
                    ball.update(dt, self.gravity, (w, h), self.rings, i*dt, self._collect_audio_event)
                
                # Vérification de passage dans la trouée pour progression du niveau
                for ball in self.balls:
                    if self.current_level < len(self.rings):
                        ring = self.rings[self.current_level]
                        if ring.state == 'arc':
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
                                    # Déclencher l'animation de victoire
                                    self.winner_ball = ball
                                    self.victory_animation_time = i*dt
                                    
                                    # Créer un événement audio pour la victoire
                                    victory_event = AudioEvent(
                                        event_type="victory",
                                        time=i*dt,
                                        position=(ball.pos.x, ball.pos.y),
                                        params={"ball_name": ball.text if ball.text else "Ball"}
                                    )
                                    self._collect_audio_event(victory_event)
                
                # Rendu principal
                render_surf.fill((15, 15, 25))
                
                # Dessiner les objets
                for ring in reversed(self.rings):
                    ring.draw(render_surf)
                
                for ball in self.balls:
                    ball.draw(render_surf)
                
                # Dessiner la légende si nécessaire
                self._draw_legend(render_surf)
                
                # Dessiner la question en haut
                self._draw_question_text(render_surf)
                
                # Dessiner l'animation de victoire si applicable
                self._draw_victory_animation(render_surf, i*dt)
                
                # Effets post-processing
                display_surf.fill((15, 15, 25))
                
                # Appliquer la secousse d'écran
                self.screen_shake.apply(render_surf, display_surf)
                display_surf = render_surf

                # Appliquer la vignette
                # self._create_vignette(display_surf)
                
                # Afficher les statistiques de performance
                if self.debug:
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
        screen_w, screen_h = int(self.width * self.screen_scale), int(self.height * self.screen_scale)

        # 1) Initialisation Pygame et fenêtre
        pygame.init()
        self._initialize_game()
        screen = pygame.display.set_mode((screen_w, screen_h))
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

        # 4) Thread d'envoi des frames
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
            
            # Mise à jour des balles avec CCD
            for ball in self.balls:
                ball.update(dt, self.gravity, (w, h), self.rings, i*dt, self._collect_audio_event)

            # Vérification de passage dans la trouée pour progression du niveau
            for ball in self.balls:
                if self.current_level < len(self.rings):
                    ring = self.rings[self.current_level]
                    if ring.state == 'arc':
                        to_ball = ball.pos - ring.center
                        ang = (-np.degrees(np.arctan2(to_ball.y, to_ball.x))) % 360
                        if ring.is_in_gap(ang) and abs(to_ball.length() - ring.inner_radius) < ball.radius * 1.5:
                            ring.trigger_disappear(i*dt, self._collect_audio_event)
                            self.current_level += 1
                            if self.current_level < len(self.rings):
                                self.rings[self.current_level].activate(i*dt, self._collect_audio_event)
                            else:
                                self.game_won = True
                                # Déclencher l'animation de victoire
                                self.winner_ball = ball
                                self.victory_animation_time = i*dt
                                self.screen_shake.start(intensity=10, duration=0.5)
                                
                                # Créer un événement audio pour la victoire
                                victory_event = AudioEvent(
                                    event_type="victory",
                                    time=i*dt,
                                    position=(ball.pos.x, ball.pos.y),
                                    params={"ball_name": ball.text if ball.text else "Ball"}
                                )
                                self._collect_audio_event(victory_event)

            # — Dessin hors écran
            for ring in reversed(self.rings): ring.draw(render_surf)
            for ball in self.balls: ball.draw(render_surf)
            
            # Dessiner la légende si nécessaire
            self._draw_legend(render_surf)
            
            # Dessiner la question en haut
            self._draw_question_text(render_surf)
            
            # Dessiner l'animation de victoire si applicable
            self._draw_victory_animation(render_surf, i*dt)

            # — Post-processing
            display_surf.fill((15,15,25))
            self.screen_shake.apply(render_surf, display_surf)

            if self.debug:
                # self._create_vignette(display_surf)
                if i % 30 == 0:
                    self._draw_fps_counter(display_surf, clock.get_fps())
                    self._draw_frame_counter(display_surf, i, self.total_frames)

            # — 5a) Affichage en direct
            if screen_w != w or screen_h != h:
                # Si les dimensions sont différentes, redimensionner avant d'afficher
                scaled_display = pygame.transform.scale(display_surf, (screen_w, screen_h))
                screen.blit(scaled_display, (0, 0))
            else:
                # Si les dimensions sont identiques, afficher directement
                screen.blit(display_surf, (0, 0))
                
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
    """Balle avec système de collision continue (CCD) et effets visuels améliorés"""

    def __init__(self, pos, vel, radius=20, color=(255, 255, 255), elasticity=1.05, 
                 text="", font=None, on_text=True, simulator=None):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.radius = radius
        self.color = color
        self.elasticity = elasticity
        self.simulator = simulator  # Référence au simulateur pour accès aux rings/events/shake
        
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

    def create_impact_particles(self, normal):
        """Crée des particules lors d'un impact"""
        impact_point = self.pos - normal * self.radius
        impact_speed = self.vel.length() * 0.3
        
        # Créer plusieurs particules
        for _ in range(15):
            # Direction aléatoire autour de la normale réfléchie
            angle = random.uniform(-np.pi/2, np.pi/2)
            rot_normal = pygame.math.Vector2(
                normal.x * np.cos(angle) - normal.y * np.sin(angle),
                normal.x * np.sin(angle) + normal.y * np.cos(angle)
            )
            
            # Vitesse aléatoire
            vel = rot_normal * random.uniform(impact_speed * 0.5, impact_speed * 2.0)
            
            # Couleur basée sur la couleur de la balle avec variation
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
            glow = random.random() < 0.3
            
            # Ajouter la particule
            self.impact_particles.append(Particle(impact_point, vel, color, size, life, glow))

    def update(self, dt, gravity, screen_size, rings, current_time, event_collector):
        """Mise à jour avec détection de collision par intersection de trajectoire"""
        w, h = screen_size
        
        # Appliquer la gravité
        self.vel += gravity * dt
        
        # Limiter la vitesse maximale
        max_speed = 4000
        if self.vel.length() > max_speed:
            self.vel = self.vel.normalize() * max_speed
        
        # Sous-diviser le mouvement en petites étapes
        steps = max(1, int(self.vel.length() * dt / 5))
        dt_step = dt / steps
        
        for _ in range(steps):
            # Sauvegarder la position actuelle
            old_pos = pygame.math.Vector2(self.pos)
            
            # Calculer la nouvelle position
            new_pos = old_pos + self.vel * dt_step
            
            # Vérifier les collisions avec les bords d'écran
            collision_occurred = False
            
            if new_pos.x - self.radius <= 0:
                new_pos.x = self.radius + 1
                self.vel.x = -self.vel.x * self.elasticity
                self.hit_flash = 0.1
                self.create_impact_particles(pygame.math.Vector2(1, 0))
                collision_occurred = True
                if self.simulator and hasattr(self.simulator, 'screen_shake'):
                    self.simulator.screen_shake.start(intensity=3, duration=0.1)
            elif new_pos.x + self.radius >= w:
                new_pos.x = w - self.radius - 1
                self.vel.x = -self.vel.x * self.elasticity
                self.hit_flash = 0.1
                self.create_impact_particles(pygame.math.Vector2(-1, 0))
                collision_occurred = True
                if self.simulator and hasattr(self.simulator, 'screen_shake'):
                    self.simulator.screen_shake.start(intensity=3, duration=0.1)
            
            if new_pos.y - self.radius <= 0:
                new_pos.y = self.radius + 1
                self.vel.y = -self.vel.y * self.elasticity
                self.hit_flash = 0.1
                self.create_impact_particles(pygame.math.Vector2(0, 1))
                collision_occurred = True
                if self.simulator and hasattr(self.simulator, 'screen_shake'):
                    self.simulator.screen_shake.start(intensity=3, duration=0.1)
            elif new_pos.y + self.radius >= h:
                new_pos.y = h - self.radius - 1
                self.vel.y = -self.vel.y * self.elasticity
                self.hit_flash = 0.1
                self.create_impact_particles(pygame.math.Vector2(0, -1))
                collision_occurred = True
                if self.simulator and hasattr(self.simulator, 'screen_shake'):
                    self.simulator.screen_shake.start(intensity=3, duration=0.1)
            
            # Si collision avec bord, appliquer la nouvelle position et continuer
            if collision_occurred:
                self.pos = new_pos
                continue
            
            # Vérifier les collisions avec les anneaux
            for ring in rings:
                if ring.state in ["disappearing", "gone"]:
                    continue
                
                # Calculer les distances avant et après le mouvement
                old_dist = (old_pos - ring.center).length()
                new_dist = (new_pos - ring.center).length()
                
                # Vérifier traversée du bord intérieur
                inner_radius = ring.inner_radius - self.radius
                if (old_dist <= inner_radius and new_dist > inner_radius) or (old_dist > inner_radius and new_dist <= inner_radius):
                    # Calcul du point d'intersection exact
                    impact_point, impact_time = self._calculate_circle_intersection(old_pos, new_pos, ring.center, inner_radius)
                    if impact_point:
                        # Vérifier si on est dans le gap
                        if ring.state == "arc":
                            to_impact = impact_point - ring.center
                            angle = (-math.degrees(math.atan2(to_impact.y, to_impact.x))) % 360
                            if ring.is_in_gap(angle):
                                self.in_gap = True
                                continue
                        
                        # Calculer la normale au point d'impact
                        to_impact = impact_point - ring.center
                        normal = -to_impact.normalize()
                        
                        # Repositionner au point d'impact
                        self.pos = impact_point
                        
                        # Calculer le rebond
                        dot_product = self.vel.dot(normal)
                        self.vel = self.vel - 2 * dot_product * normal * self.elasticity
                        
                        # Continuer le mouvement avec le temps restant
                        remaining_time = (1.0 - impact_time) * dt_step
                        if remaining_time > 0:
                            self.pos += self.vel * remaining_time
                        
                        # Effets
                        self.hit_flash = 0.1
                        self.collision = True
                        self.create_impact_particles(normal)
                        ring._handle_collision_effects(self, current_time, event_collector, dot_product, normal)
                        break
                
                # Vérifier traversée du bord extérieur
                outer_radius = ring.outer_radius + self.radius
                if (old_dist <= outer_radius and new_dist > outer_radius) or (old_dist > outer_radius and new_dist <= outer_radius):
                    # Calcul du point d'intersection exact
                    impact_point, impact_time = self._calculate_circle_intersection(old_pos, new_pos, ring.center, outer_radius)
                    if impact_point:
                        # Vérifier si on est dans le gap
                        if ring.state == "arc":
                            to_impact = impact_point - ring.center
                            angle = (-math.degrees(math.atan2(to_impact.y, to_impact.x))) % 360
                            if ring.is_in_gap(angle):
                                self.in_gap = True
                                continue
                        
                        # Calculer la normale au point d'impact (vers l'intérieur pour le bord extérieur)
                        to_impact = impact_point - ring.center
                        normal = -to_impact.normalize()
                        
                        # Repositionner au point d'impact
                        self.pos = impact_point
                        
                        # Calculer le rebond
                        dot_product = self.vel.dot(normal)
                        self.vel = self.vel - 2 * dot_product * normal * self.elasticity
                        
                        # Continuer le mouvement avec le temps restant
                        remaining_time = (1.0 - impact_time) * dt_step
                        if remaining_time > 0:
                            self.pos += self.vel * remaining_time
                        
                        # Effets
                        self.hit_flash = 0.1
                        self.collision = True
                        self.create_impact_particles(normal)
                        ring._handle_collision_effects(self, current_time, event_collector, dot_product, normal)
                        break
            else:
                # Aucune collision avec les anneaux, appliquer la nouvelle position
                self.pos = new_pos
        
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

    def _calculate_circle_intersection(self, start_pos, end_pos, circle_center, circle_radius):
        """Calcule le point d'intersection entre la trajectoire et un cercle"""
        # Vecteur de mouvement
        movement = end_pos - start_pos
        movement_length = movement.length()
        
        if movement_length == 0:
            return None, 0
        
        # Vecteur du centre du cercle au point de départ
        to_start = start_pos - circle_center
        
        # Équation quadratique pour intersection ligne-cercle
        # (start + t * movement - center)² = radius²
        a = movement.dot(movement)
        b = 2 * to_start.dot(movement)
        c = to_start.dot(to_start) - circle_radius * circle_radius
        
        discriminant = b * b - 4 * a * c
        
        if discriminant < 0:
            return None, 0  # Pas d'intersection
        
        discriminant = math.sqrt(discriminant)
        
        # Deux solutions possibles
        t1 = (-b - discriminant) / (2 * a)
        t2 = (-b + discriminant) / (2 * a)
        
        # Prendre la première intersection valide
        for t in [t1, t2]:
            if 0 <= t <= 1:  # Intersection sur le segment
                intersection_point = start_pos + movement * t
                return intersection_point, t
        
        return None, 0

    def draw(self, surface):
        """Rendu avec effets visuels améliorés"""
        # --- Dessiner la traînée ---
        for i, pos in enumerate(self.trail):
            alpha = int(200 * (i / len(self.trail)) ** self.trail_fade)
            size = int(self.radius * (0.4 + 0.6 * i / len(self.trail)))
            
            # Couleur de traînée
            if self.hit_flash > 0:
                trail_color = (255, 255, 255, alpha)
            else:
                r, g, b = self.color
                brightness = int(50 * (i / len(self.trail)))
                trail_color = (min(255, r + brightness), min(255, g + brightness), min(255, b + brightness), alpha)
            
            # Dessiner avec anti-aliasing
            if size > 0:
                pygame.gfxdraw.filled_circle(surface, int(pos.x), int(pos.y), size, trail_color)
                pygame.gfxdraw.aacircle(surface, int(pos.x), int(pos.y), size, trail_color)
        
        # --- Dessiner les particules d'impact ---
        for particle in self.impact_particles:
            particle.draw(surface)
        
        # --- Dessiner la balle principale ---
        draw_color = self.color
        
        # Modifier la couleur selon l'état
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
            
            # Dessiner un cercle plus grand pour le flash
            glow_radius = int(self.radius * 1.3)
            pygame.gfxdraw.filled_circle(surface, int(self.pos.x), int(self.pos.y), glow_radius, (*flash_color, 100))
            pygame.gfxdraw.aacircle(surface, int(self.pos.x), int(self.pos.y), glow_radius, (*flash_color, 150))
        
        # Cercle principal avec anti-aliasing
        pygame.gfxdraw.filled_circle(surface, int(self.pos.x), int(self.pos.y), int(self.radius), draw_color)
        pygame.gfxdraw.aacircle(surface, int(self.pos.x), int(self.pos.y), int(self.radius), draw_color)
        
        # Reflet pour donner du volume
        highlight_pos = (int(self.pos.x - self.radius * 0.3), int(self.pos.y - self.radius * 0.3))
        highlight_radius = int(self.radius * 0.4)
        pygame.gfxdraw.filled_circle(surface, highlight_pos[0], highlight_pos[1], highlight_radius, (255, 255, 255, 100))
        pygame.gfxdraw.aacircle(surface, highlight_pos[0], highlight_pos[1], highlight_radius, (255, 255, 255, 120))
        
        # --- Dessiner le texte sur la balle si activé ---
        if self.text and self.on_text and self.text_surface:
            text_width, text_height = self.text_surface.get_size()
            text_pos = (int(self.pos.x - text_width // 2), int(self.pos.y - text_height // 2))
            
            # Fond noir semi-transparent pour améliorer la lisibilité
            text_bg = pygame.Surface((text_width + 6, text_height + 4), pygame.SRCALPHA)
            text_bg.fill((0, 0, 0, 150))
            surface.blit(text_bg, (text_pos[0] - 3, text_pos[1] - 2))
            
            # Dessiner le texte
            surface.blit(self.text_surface, text_pos)


class Ring:
    """Anneau avec trouée et système de collision continue (CCD)"""

    def __init__(self, center, outer_radius, thickness, gap_angle=0, rotation_speed=0, 
                 color=(255, 100, 100), simulator=None, random_start=True, start_angle=None):
        self.center = center
        self.outer_radius = outer_radius
        self.thickness = thickness
        self.inner_radius = outer_radius - thickness
        self.gap_angle = gap_angle
        self.rotation_speed = rotation_speed
        self.simulator = simulator
        
        if random_start:
            self.arc_start = random.randint(0, 360)
        else:
            self.arc_start = start_angle or 0
        
        self.color = color
        self.state = "circle"  # "circle", "arc", "disappearing", "gone"
        self.disappear_timer = 1.0
        self.glow_intensity = 0.0
        
        # Paramètres d'animation
        self.pulse_timer = 0.0
        self.pulse_period = 1.5
        self.pulse_amount = 0.2
        self.color_shift_timer = 0.0
        self.color_shift_period = 3.0
        self.color_hue_shift = 0.0
        
        # Effets
        self.particles = []
        self.events = []
    
    # --- Utilitaires mathématiques ---
    @staticmethod
    def _quad_roots(a, b, c):
        """Résout l'équation quadratique ax² + bx + c = 0"""
        discriminant = b*b - 4*a*c
        if discriminant < 0:
            return None, None
        sqrt_disc = math.sqrt(discriminant)
        return (-b - sqrt_disc) / (2*a), (-b + sqrt_disc) / (2*a)
    
    def get_gap_angles(self):
        """Récupère les angles de début et fin de la trouée"""
        gap_start = self.arc_start % 360
        gap_end = (self.arc_start + self.gap_angle) % 360
        return gap_start, gap_end
    
    def is_in_gap(self, angle):
        """Vérifie si un angle est dans la trouée"""
        if self.state != "arc" or self.gap_angle == 0:
            return False
        
        gap_start, gap_end = self.get_gap_angles()
        angle = angle % 360
        
        # Gestion du cas où la trouée traverse la ligne 0/360
        if gap_start <= gap_end:
            return gap_start <= angle <= gap_end
        else:
            return angle >= gap_start or angle <= gap_end
    
    # --- Animation de couleur ---
    def hsv_to_rgb(self, h, s, v):
        """Convertit HSV en RGB"""
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
        r, g, b = self.color
        
        # Conversion RGB vers HSV approximative
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
        
        # Appliquer les animations
        h = (h + self.color_hue_shift) % 360
        v = v * (1 + np.sin(2 * np.pi * self.pulse_timer / self.pulse_period) * self.pulse_amount)
        v = min(1.0, max(0.3, v))
        
        return self.hsv_to_rgb(h, s, v)

    # --- Gestion des effets de collision ---
    def _handle_collision_effects(self, ball, current_time, event_collector, dot_product, normal):
        """Gère tous les effets de collision (visuels, sonores, etc.)"""
        # Effets visuels
        ball.hit_flash = 0.1
        ball.create_impact_particles(normal)
        ball.collision = True
        self.glow_intensity = 0.5
        
        # Secousse d'écran
        impact_force = abs(dot_product) / 200
        if self.simulator and hasattr(self.simulator, 'screen_shake') and impact_force > 0.2:
            self.simulator.screen_shake.start(
                intensity=min(10, impact_force * 3),
                duration=min(0.2, impact_force * 0.1)
            )
        
        # Créer des particules de l'anneau
        for _ in range(10):
            self.create_particle(has_glow=True)
        
        # Événement audio
        velocity_magnitude = ball.vel.length()
        note_index = min(int(velocity_magnitude / 150), 6)
        octave = min(int(velocity_magnitude / 300), 2)
        
        event = AudioEvent(
            event_type="note",
            time=current_time,
            position=(ball.pos.x, ball.pos.y),
            params={"note": note_index, "octave": octave}
        )
        
        self.events.append(event)
        if event_collector:
            event_collector(event)
    
    # --- Particules ---
    def create_particle(self, has_glow=False):
        """Crée une particule lors d'effets visuels"""
        angle = random.uniform(0, np.pi * 2)
        radius = random.uniform(self.inner_radius, self.outer_radius)
        
        # Position basée sur l'angle
        pos = (
            self.center.x + np.cos(angle) * radius,
            self.center.y + np.sin(angle) * radius
        )
        
        # Vitesse s'éloignant du centre
        dir_vec = pygame.math.Vector2(np.cos(angle), np.sin(angle))
        vel = dir_vec * random.uniform(100, 300)
        
        # Couleur animée avec variation
        base_color = self.get_animated_color()
        color_var = 50
        color = (
            min(255, max(0, base_color[0] + random.randint(-color_var, color_var))),
            min(255, max(0, base_color[1] + random.randint(-color_var, color_var))),
            min(255, max(0, base_color[2] + random.randint(-color_var, color_var))),
            255
        )
        
        # Propriétés aléatoires
        size = random.uniform(3, 8)
        life = random.uniform(0.5, 1.5)
        
        self.particles.append(Particle(pos, vel, color, size, life, glow=has_glow))
    
    # --- Gestion d'état ---
    def activate(self, current_time, event_collector=None):
        """Active l'anneau (passe de cercle à arc)"""
        if self.state == "circle":
            self.state = "arc"
            
            # Événement sonore
            event = AudioEvent(
                event_type="activation",
                time=current_time,
                position=(self.center.x, self.center.y)
            )
            self.events.append(event)
            if event_collector:
                event_collector(event)
            
            # Particules d'activation
            for _ in range(30):
                self.create_particle(has_glow=True)
    
    def trigger_disappear(self, current_time, event_collector=None):
        """Déclenche la disparition de l'anneau"""
        if self.state == "arc":
            self.state = "disappearing"
            
            # Événement sonore
            event = AudioEvent(
                event_type="explosion",
                time=current_time,
                position=(self.center.x, self.center.y),
                params={"size": "large"}
            )
            self.events.append(event)
            if event_collector:
                event_collector(event)
            
            # Secousse d'écran
            if self.simulator and hasattr(self.simulator, 'screen_shake'):
                self.simulator.screen_shake.start(intensity=10, duration=0.4)
            
            # Beaucoup de particules
            for _ in range(150):
                self.create_particle(has_glow=True)
    
    # --- Mise à jour ---
    def update(self, dt, ball_positions=None):
        """Mise à jour de l'anneau"""
        # Timers d'animation
        self.pulse_timer = (self.pulse_timer + dt) % self.pulse_period
        self.color_shift_timer = (self.color_shift_timer + dt) % self.color_shift_period
        
        # Animation de teinte pour les arcs
        if self.state == "arc":
            self.color_hue_shift = (self.color_hue_shift + 15 * dt) % 360
            
            # Rotation de l'arc
            self.arc_start = (self.arc_start + self.rotation_speed * dt) % 360
            
            # Halo en fonction de la proximité des balles
            if ball_positions:
                min_dist = float('inf')
                for ball_pos in ball_positions:
                    dist = (ball_pos - self.center).length()
                    if dist < min_dist:
                        min_dist = dist
                
                # Intensité basée sur la proximité
                proximity = max(0, 1 - abs(min_dist - self.inner_radius) / (self.thickness * 2))
                self.glow_intensity = proximity * 0.8
        
        # Disparition progressive
        elif self.state == "disappearing":
            self.disappear_timer -= dt
            if self.disappear_timer <= 0:
                self.state = "gone"
            
            # Générer des particules pendant la disparition
            if random.random() < 20 * dt:
                self.create_particle(has_glow=True)
        
        # Mettre à jour les particules
        self.particles = [p for p in self.particles if p.update(dt)]
    
    # --- Rendu amélioré ---
    def draw_filled_arc(self, surface, center, inner_radius, outer_radius, start_angle, end_angle, color):
        """Dessine un arc rempli entre deux rayons"""
        # Convertir en radians
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        # Nombre de segments pour une courbe lisse
        num_segments = max(5, int(abs(end_angle - start_angle) / 5))
        angle_step = (end_rad - start_rad) / num_segments
        
        # Points de l'arc
        points = []
        
        # Bord extérieur
        for i in range(num_segments + 1):
            angle = start_rad + i * angle_step
            x = center[0] + outer_radius * math.cos(angle)
            y = center[1] - outer_radius * math.sin(angle)  # Y inversé pour Pygame
            points.append((x, y))
        
        # Bord intérieur (ordre inverse)
        for i in range(num_segments, -1, -1):
            angle = start_rad + i * angle_step
            x = center[0] + inner_radius * math.cos(angle)
            y = center[1] - inner_radius * math.sin(angle)  # Y inversé pour Pygame
            points.append((x, y))
        
        # Dessiner le polygone
        if len(points) >= 3:
            pygame.gfxdraw.filled_polygon(surface, points, color)
            pygame.gfxdraw.aapolygon(surface, points, color)
    
    def draw(self, surface):
        """Rendu amélioré des cercles et arcs"""
        if self.state == "gone":
            return
        
        cx, cy = int(self.center.x), int(self.center.y)
        out_r = int(self.outer_radius)
        in_r = int(self.inner_radius)
        col_rgb = self.get_animated_color()
        
        # Facteur de fondu pour la disparition
        fade = self.disappear_timer if self.state == "disappearing" else 1.0
        alpha = int(255 * fade)
        col = (*col_rgb, alpha)
        
        # --- CERCLE COMPLET ---
        if self.state == "circle":
            # Surface temporaire pour éviter les artefacts
            temp_surface = pygame.Surface((out_r * 2, out_r * 2), pygame.SRCALPHA)
            
            # Cercle extérieur
            pygame.gfxdraw.filled_circle(temp_surface, out_r, out_r, out_r, col)
            pygame.gfxdraw.aacircle(temp_surface, out_r, out_r, out_r, col)
            
            # Trou intérieur
            pygame.gfxdraw.filled_circle(temp_surface, out_r, out_r, in_r, (0, 0, 0, 0))
            
            # Blitter sur la surface principale
            surface.blit(temp_surface, (cx - out_r, cy - out_r))
        
        # --- ARC AVEC TROUÉE ---
        elif self.state == "arc" or self.state == "disappearing":
            # Calculer les angles de l'arc (tout sauf la trouée)
            arc_start = (self.arc_start + self.gap_angle) % 360
            arc_end = self.arc_start % 360
            
            # Gérer le cas où l'arc traverse 0°
            if arc_start > arc_end:
                # Dessiner en deux parties
                self.draw_filled_arc(surface, (cx, cy), in_r, out_r, arc_start, 360, col)
                self.draw_filled_arc(surface, (cx, cy), in_r, out_r, 0, arc_end, col)
            else:
                self.draw_filled_arc(surface, (cx, cy), in_r, out_r, arc_start, arc_end, col)
        
        # --- HALO LUMINEUX ---
        if self.glow_intensity > 0 and alpha > 0:
            halo_alpha = int(120 * self.glow_intensity * fade)
            halo_col = (*col_rgb, halo_alpha)
            
            # Plusieurs cercles pour créer l'effet de halo
            for r in range(in_r - 5, out_r + 5, 2):
                if r > 0:
                    pygame.gfxdraw.aacircle(surface, cx, cy, r, halo_col)
        
        # --- PARTICULES ---
        for particle in self.particles:
            particle.draw(surface)