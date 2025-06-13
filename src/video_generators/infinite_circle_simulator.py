# video_generators/circle_simulator.py
"""
Enhanced TikTok Circle Simulator with satisfying colors, escape system, and countdown
Version améliorée avec couleurs satisfaisantes et système d'évasion - CORRIGÉE
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

BACKGROUND = (8, 8, 15)          # Fond plus sombre pour contraste

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

class InfiniteCircleSimulator(IVideoGenerator):
    """
    Enhanced TikTok Circle Simulator with escape system and satisfying colors
    """
    def __init__(self, width = 1080, height = 1920, fps = 60, duration = 30.0, 
                 output_path = "output/circle_video.mp4", temp_dir = "temp", frames_dir = "frames", 
                 min_radius = 100, gap_radius = 20, nb_rings = 5, thickness = 15, gap_angle = 60, 
                 rotation_speed = 60, random_arc=True, 
                 # Enhanced TikTok rainbow color palette - arc-en-ciel satisfaisant
                 color_palette = [
                     "#FF0000", "#FF8000", "#FFFF00", "#80FF00", "#00FF00",
                     "#00FF80", "#00FFFF", "#0080FF", "#0000FF", "#8000FF", 
                     "#FF00FF", "#FF0080", "#FF4080", "#FF8040", "#FFBF00"
                 ],
                 # Nouveaux paramètres pour les balles
                 balls = 1, balls_size = 10, text_balls = None, on_balls_text = True, max_text_length = 15,
                 # Paramètre pour la question en haut (anglais par défaut)
                 question_text = "Can you escape 2000 circles?",
                 top_frac_text = 0.15,
                 left_frac_text = 0.5,
                 # Nouveaux paramètres d'évasion
                 max_circles_to_escape = 2000,  # Nombre de cercles à détruire pour s'échapper
                 show_countdown = True,  # Afficher le compteur central
                 countdown_color = "#FFFFFF",
                 victory_on_escape = True,  # Victoire quand on s'échappe
                 # Paramètres pour éviter l'écran noir
                 use_gpu_acceleration = True,
                 direct_frames = False,
                 performance_mode = "balanced",
                 render_scale = 1.0,
                 all_arc = True,
                 alternate_rotation = False,
                 debug = True, screen_scale = 1.0,
                 start_angle = 30,
                 gap_angle_rings=0,
                 gap_speed = 10,
                 gravity=400,
                 elasticity=1.02,
                 # Système de rétrécissement amélioré
                 shrink_speed = 50,
                 maintain_ring_count = True,
                 shrink_factor = 0.85,  # Plus progressif
                 # Paramètres d'optimisation
                 max_particles_per_ring = 80,
                 max_particles_per_ball = 15,
                 performance_mode_auto = True,
                 # Nouveau : limite de génération de cercles
                 max_total_rings = 300,  # Arrêter de générer après 300 cercles
                 # NOUVEAUX PARAMÈTRES AMÉLIORÉS
                 rotation_direction = "clockwise",  # "clockwise", "counterclockwise", "alternate", "random"
                 gap_detection_tolerance = 2.0,  # Multiplicateur pour la tolérance de détection
                 gap_detection_debug = False,  # Debug spécifique pour la détection
                 # NOUVEAUX PARAMÈTRES PARTICULES ET RÉTRÉCISSEMENT
                 particle_gravity = 200,  # Gravité appliquée aux particules
                 particle_air_resistance = 0.98,  # Résistance de l'air pour les particules
                 shrink_curve_type = "cubic",  # "linear", "quadratic", "cubic", "bezier"
                 shrink_acceleration_factor = 1.5,  # Facteur d'accélération du rétrécissement
                 min_shrink_radius_ratio = 0.3):  # Ratio minimum de rétrécissement (0.3 = 30% du rayon initial)
        """Initialise le simulateur amélioré"""
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
        self.start_angle = start_angle
        self.gap_angle_rings = gap_angle_rings
        self.gap_speed = gap_speed
        self.elasticity = elasticity

        # Paramètres du jeu
        self.center = None
        self.gravity = pygame.math.Vector2(0, gravity)
        self.min_radius = min_radius
        self.gap_radius = gap_radius
        self.nb_rings = nb_rings
        self.thickness = thickness
        self.gap_angle = gap_angle
        self.rotation_speed = rotation_speed
        self.random_arc = random_arc
        self.all_arc = all_arc
        self.alternate_rotation = alternate_rotation

        # NOUVEAUX PARAMÈTRES AMÉLIORÉS
        self.rotation_direction = rotation_direction
        self.gap_detection_tolerance = gap_detection_tolerance
        self.gap_detection_debug = gap_detection_debug
        
        # NOUVEAUX PARAMÈTRES PARTICULES ET RÉTRÉCISSEMENT
        self.particle_gravity = pygame.math.Vector2(0, particle_gravity)
        self.particle_air_resistance = particle_air_resistance
        self.shrink_curve_type = shrink_curve_type
        self.shrink_acceleration_factor = shrink_acceleration_factor
        self.min_shrink_radius_ratio = min_shrink_radius_ratio

        # Paramètres des balles
        self.balls_count = max(1, balls)
        self.balls_size = balls_size
        self.text_balls = text_balls if text_balls else []
        self.on_balls_text = on_balls_text
        self.max_text_length = max_text_length
        self.use_gpu_acceleration = use_gpu_acceleration
        
        # Paramètre pour la question (en anglais)
        self.question_text = question_text
        self.top_frac_text = top_frac_text
        self.left_frac_text = left_frac_text

        # NOUVEAUX PARAMÈTRES D'ÉVASION
        self.max_circles_to_escape = max_circles_to_escape
        self.circles_destroyed = 0  # Compteur de cercles détruits
        self.show_countdown = show_countdown
        self.countdown_color = countdown_color
        self.victory_on_escape = victory_on_escape
        self.has_escaped = False  # Flag d'évasion réussie
        
        # Limite de génération de cercles
        self.max_total_rings = max_total_rings
        self.total_rings_created = 0  # Compteur total de cercles créés

        # Historique des positions pour détecter le passage amélioré
        self.ball_previous_positions = {}
        self.ball_gap_states = {}  # État précédent de chaque balle dans les gaps

        # Paramètres visuels
        self.direct_frames = direct_frames
        self.performance_mode = performance_mode
        self.render_scale = render_scale
        
        # Système de rétrécissement
        self.shrink_speed = shrink_speed
        self.maintain_ring_count = maintain_ring_count
        self.shrink_factor = shrink_factor
        self.original_ring_spacing = gap_radius + thickness
        self.rings_destroyed_count = 0
        self.shrinking_active = False
        self.shrink_progress = 0.0
        
        # Optimisations
        self.max_particles_per_ring = max_particles_per_ring
        self.max_particles_per_ball = max_particles_per_ball
        self.performance_mode_auto = performance_mode_auto
        self.performance_counter = 0
        self.last_fps = 60.0
        
        # Palette de couleurs améliorée pour TikTok
        self.color_palette = color_palette
        self.color_rgb_cache = {}
        self.color_index = 0  # Index pour continuité des couleurs
        
        # Objets du jeu
        self.rings: list[Ring] = []
        self.balls = []
        self.current_level = 0
        self.game_won = False
        
        # Gestion des événements audio
        self.audio_events = []
        
        # État de la simulation
        self.current_frame = 0
        self.simulation_running = False
        self.simulation_start_time = 0
        
        # Métadonnées
        self.metadata = None
        
        # Effets visuels
        self.screen_shake = ScreenShake()
        self.vignette_intensity = 0.2

        # Polices
        self.font = None
        self.legend_font = None
        self.countdown_font = None  # Police pour le compteur central
        
        # Animation de victoire/évasion
        self.winner_ball = None
        self.victory_animation_time = 0
        self.victory_animation_duration = 3.0
        self.victory_particles = []
        self.victory_flash = 0
        
        # Animation du compteur
        self.countdown_pulse = 0.0
        self.countdown_scale = 1.0
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure le générateur avec des paramètres spécifiques"""
        try:
            # Appliquer les paramètres fournis (en ignorant les commentaires)
            for key, value in config.items():
                # Ignorer les clés de commentaires
                if key.startswith('_comment'):
                    continue
                    
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    logger.warning(f"Unknown parameter ignored: {key}")
            
            # Vérifier correspondance textes/balles
            if self.text_balls and len(self.text_balls) != self.balls_count:
                logger.warning(f"Text count ({len(self.text_balls)}) doesn't match ball count ({self.balls_count}). Auto-adjusting.")
                if len(self.text_balls) > 0:
                    self.balls_count = len(self.text_balls)
                else:
                    self.text_balls = [f"Player {i+1}" for i in range(self.balls_count)]  # Textes anglais par défaut
            elif not self.text_balls:
                self.text_balls = [f"" for i in range(self.balls_count)]
            
            # Vérifications de stabilité
            if self.elasticity > 1.1:
                logger.warning(f"Elasticity too high ({self.elasticity}), reducing to 1.05 for stability")
                self.elasticity = 1.05
            
            # Calculs dérivés
            self.center = pygame.math.Vector2(self.width // 2, self.height // 2)
            
            # Créer répertoires
            os.makedirs(self.temp_dir, exist_ok=True)
            os.makedirs(self.frames_dir, exist_ok=True)
            
            # Nettoyer frames si nécessaire
            if self.direct_frames:
                for file in os.listdir(self.frames_dir):
                    file_path = os.path.join(self.frames_dir, file)
                    if os.path.isfile(file_path) and file.startswith("frame_"):
                        os.remove(file_path)
            
            # Créer répertoire de sortie
            output_dir = os.path.dirname(self.output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Précalculer palette RGB
            self.color_rgb_cache = {color: self._hex_to_rgb(color) for color in self.color_palette}
            
            # Calculer frames totales
            self.total_frames = int(self.fps * self.duration)
            
            # Initialiser polices
            pygame.font.init()
            self.font = pygame.font.SysFont("Arial", 18, bold=True)  # Plus petit
            self.legend_font = pygame.font.SysFont("Arial", 22, bold=True)  # Plus petit
            self.countdown_font = pygame.font.SysFont("Arial", 80, bold=True)  # Plus petit pour compteur
            
            logger.info(f"Enhanced simulator configured: {self.width}x{self.height}, {self.fps} FPS, {self.duration}s")
            logger.info(f"Escape system: {self.max_circles_to_escape} circles to escape, countdown: {self.show_countdown}")
            logger.info(f"Max rings limit: {self.max_total_rings}")
            logger.info(f"Rotation direction: {self.rotation_direction}, Detection tolerance: {self.gap_detection_tolerance}")
            logger.info(f"Particle physics: gravity={self.particle_gravity.y}, air_resistance={self.particle_air_resistance}")
            logger.info(f"Shrink system: {self.shrink_curve_type} curve, acceleration={self.shrink_acceleration_factor}, min_ratio={self.min_shrink_radius_ratio}")
            return True
            
        except Exception as e:
            logger.error(f"Configuration error: {e}")
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
        if hasattr(trend_data, 'recommended_settings') and 'color_palette' in trend_data.recommended_settings:
            self.color_palette = trend_data.recommended_settings['color_palette']
            self.color_rgb_cache = {color: self._hex_to_rgb(color) for color in self.color_palette}
            logger.info(f"Applied color palette: {self.color_palette}")
        
        if hasattr(trend_data, 'timing_trends') and 'beat_frequency' in trend_data.timing_trends:
            beat_frequency = trend_data.timing_trends['beat_frequency']
            self.rotation_speed = int(360 * (1.0 / beat_frequency) / 4)
            logger.info(f"Applied rotation speed: {self.rotation_speed} (BPM: {60/beat_frequency})")
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convertit une couleur hexadécimale en RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _get_next_satisfying_color(self) -> Tuple[int, int, int]:
        """Obtient la prochaine couleur arc-en-ciel satisfaisante avec transition douce"""
        # Créer une transition arc-en-ciel douce basée sur HSV
        hue = (self.color_index * 24) % 360  # 24 degrés entre chaque couleur pour transition douce
        saturation = 0.9 + 0.1 * math.sin(self.color_index * 0.5)  # Saturation variable
        value = 0.8 + 0.2 * math.cos(self.color_index * 0.3)  # Luminosité variable
        
        # Convertir HSV en RGB
        h_i = int(hue / 60)
        f = hue / 60 - h_i
        p = value * (1 - saturation)
        q = value * (1 - f * saturation)
        t = value * (1 - (1 - f) * saturation)
        
        if h_i == 0:
            r, g, b = value, t, p
        elif h_i == 1:
            r, g, b = q, value, p
        elif h_i == 2:
            r, g, b = p, value, t
        elif h_i == 3:
            r, g, b = p, q, value
        elif h_i == 4:
            r, g, b = t, p, value
        else:
            r, g, b = value, p, q
        
        # Convertir en entiers RGB
        rgb_color = (int(r * 255), int(g * 255), int(b * 255))
        
        self.color_index += 1
        return rgb_color
    
    def _get_shrink_curve_factor(self, progress):
        """NOUVELLE MÉTHODE: Calcule le facteur de rétrécissement selon la courbe choisie"""
        # Limiter le progrès entre 0 et 1
        progress = max(0.0, min(1.0, progress))
        
        if self.shrink_curve_type == "linear":
            return progress
        
        elif self.shrink_curve_type == "quadratic":
            # Courbe quadratique : accélération progressive
            return progress ** 2
        
        elif self.shrink_curve_type == "cubic":
            # Courbe cubique : accélération encore plus forte
            return progress ** 3
        
        elif self.shrink_curve_type == "bezier":
            # Courbe de Bézier pour un effet très satisfaisant
            # Points de contrôle : P0(0,0), P1(0.1, 0), P2(0.7, 1), P3(1,1)
            t = progress
            return (3 * (1-t)**2 * t * 0.1) + (3 * (1-t) * t**2 * 0.7) + (t**3 * 1.0)
        
        else:
            return progress  # Fallback linéaire
    
    def _calculate_dynamic_shrink_speed(self):
        """NOUVELLE MÉTHODE: Calcule la vitesse de rétrécissement dynamique"""
        base_speed = self.shrink_speed
        
        # Plus on détruit de cercles, plus ça va vite (effet satisfaisant)
        acceleration = 1.0 + (self.circles_destroyed / 100.0) * self.shrink_acceleration_factor
        
        # Courbe de progression basée sur le nombre de cercles détruits
        progress = min(1.0, self.circles_destroyed / (self.max_circles_to_escape * 0.5))
        curve_factor = self._get_shrink_curve_factor(progress)
        
        # Vitesse finale avec accélération progressive
        dynamic_speed = base_speed * acceleration * (1.0 + curve_factor * 2.0)
        
        if self.gap_detection_debug:
            print(f"Shrink speed: base={base_speed:.1f}, accel={acceleration:.2f}, curve={curve_factor:.2f}, final={dynamic_speed:.1f}")
        
        return dynamic_speed
    
    def _get_rotation_speed_for_ring(self, ring_index):
        """NOUVEAU: Calcule la vitesse de rotation pour un cercle donné selon le paramètre de direction"""
        base_speed = self.rotation_speed + self.gap_speed
        
        if self.rotation_direction == "clockwise":
            return base_speed
        elif self.rotation_direction == "counterclockwise":
            return -base_speed
        elif self.rotation_direction == "alternate":
            return base_speed if ring_index % 2 == 0 else -base_speed
        elif self.rotation_direction == "random":
            return base_speed if random.random() > 0.5 else -base_speed
        else:
            # Fallback au mode existant
            if self.alternate_rotation:
                return base_speed if ring_index % 2 == 0 else -base_speed
            return base_speed
    
    def _shrink_all_rings(self, dt):
        """Rétrécit tous les cercles de manière SIMPLE et FIABLE"""
        if not self.shrinking_active:
            return
            
        # Calculer la vitesse de rétrécissement
        shrink_speed = self.shrink_speed * dt
        
        # CORRECTION: Rétrécissement simple et direct
        active_rings = [ring for ring in self.rings if ring.state != "gone"]
        if not active_rings:
            self.shrinking_active = False
            return
        
        # Trier par rayon pour maintenir l'ordre
        active_rings.sort(key=lambda r: r.outer_radius)
        
        # NOUVEAU: Rétrécissement uniforme avec espacement fixe
        min_spacing = self.thickness + 10  # Espacement minimum garanti
        all_shrunk = True
        
        for i, ring in enumerate(active_rings):
            # Calculer le rayon cible
            if i == 0:
                # Premier cercle - rétrécit vers le minimum
                target_radius = max(
                    self.min_radius * self.min_shrink_radius_ratio + self.thickness,
                    ring.outer_radius * self.shrink_factor
                )
            else:
                # Cercles suivants - maintenir l'espacement
                prev_ring = active_rings[i-1]
                target_radius = prev_ring.outer_radius + min_spacing
            
            # Appliquer le rétrécissement
            if ring.outer_radius > target_radius + 1:
                ring.outer_radius = max(target_radius, ring.outer_radius - shrink_speed)
                ring.inner_radius = max(10, ring.outer_radius - self.thickness)
                all_shrunk = False
            else:
                ring.outer_radius = target_radius
                ring.inner_radius = max(10, target_radius - self.thickness)
        
        # Arrêter le rétrécissement si terminé
        if all_shrunk:
            self.shrinking_active = False
            if self.gap_detection_debug:
                print("SHRINKING COMPLETED")
                
    def _create_new_ring(self):
        """Crée un nouveau cercle avec positionnement coordonné"""
        if not self.maintain_ring_count:
            return
        
        # VÉRIFIER LA LIMITE DE GÉNÉRATION
        if self.total_rings_created >= self.max_total_rings:
            logger.info(f"Maximum ring limit reached ({self.max_total_rings}). No more rings will be generated.")
            return
            
        # CORRECTION : Calculer la position du nouveau cercle de manière coordonnée
        active_rings = [ring for ring in self.rings if ring.state != "gone"]
        
        if active_rings:
            # Trier par rayon pour trouver le plus grand
            active_rings.sort(key=lambda r: r.outer_radius)
            max_ring = active_rings[-1]
            
            # NOUVEAU : Espacement basé sur l'espacement actuel du système
            current_spacing = self.thickness + self.gap_radius
            new_outer_radius = max_ring.outer_radius + current_spacing
        else:
            new_outer_radius = self.min_radius
        
        # Couleur satisfaisante avec continuité
        ring_color = self._get_next_satisfying_color()
        
        # Utiliser le système de rotation amélioré
        rotation_speed = self._get_rotation_speed_for_ring(len(self.rings))
        
        # Créer le nouveau cercle
        new_ring = Ring(
            self.center, 
            outer_radius=new_outer_radius,
            thickness=self.thickness,
            gap_angle=self.gap_angle,
            rotation_speed=rotation_speed,
            color=ring_color,
            simulator=self,
            random_start=self.random_arc,
            start_angle=self.rings[-1].arc_start + self.gap_angle_rings if self.rings else self.start_angle
        )
        
        # CORRECTION : Propriétés de rétrécissement coordonnées
        new_ring.original_outer_radius = new_outer_radius
        new_ring.target_outer_radius = new_outer_radius  # Commence à sa taille normale
        new_ring.target_inner_radius = new_outer_radius - self.thickness
        new_ring.shrink_progress = 0.0
        
        # Respecter le mode all_arc
        if self.all_arc:
            new_ring.state = "arc"
        else:
            new_ring.state = "circle"
        
        # Ajouter à la liste et incrémenter compteur
        self.rings.append(new_ring)
        self.total_rings_created += 1
        
        if self.gap_detection_debug:
            print(f"NEW RING CREATED: radius={new_outer_radius:.1f}, total={self.total_rings_created}")


    def _trigger_shrinking_cycle(self, current_time, event_collector):
        """Déclenche un cycle de rétrécissement COORDONNÉ"""
        if not self.maintain_ring_count:
            return
            
        self.rings_destroyed_count += 1
        self.circles_destroyed += 1
        
        # Vérifier si le joueur s'est échappé
        if self.circles_destroyed >= self.max_circles_to_escape and not self.has_escaped:
            self.has_escaped = True
            if self.victory_on_escape:
                self.game_won = True
                if self.balls:
                    self.winner_ball = self.balls[0]
                    self.victory_animation_time = current_time
                    self.screen_shake.start(intensity=15, duration=1.0)
                    
                    escape_event = AudioEvent(
                        event_type="escape_victory",
                        time=current_time,
                        position=(self.center.x, self.center.y),
                        params={
                            "circles_destroyed": self.circles_destroyed,
                            "achievement": "escaped_from_circles"
                        }
                    )
                    if event_collector:
                        event_collector(escape_event)
        
        # NOUVEAU : Calcul coordonné des nouvelles tailles
        active_rings = [ring for ring in self.rings if ring.state != "gone"]
        active_rings.sort(key=lambda r: r.outer_radius)
        
        if not active_rings:
            return
        
        # Calculer le facteur de rétrécissement et l'espacement de base
        shrink_ratio = self.shrink_factor
        base_spacing = (self.thickness + self.gap_radius) * shrink_ratio
        min_spacing = self.thickness + 5  # Espacement minimum absolu
        target_spacing = max(min_spacing, base_spacing)
        
        # Calculer le rayon de base pour le plus petit cercle
        base_radius = self.min_radius * (shrink_ratio ** self.rings_destroyed_count)
        base_radius = max(base_radius, self.min_radius * self.min_shrink_radius_ratio + self.thickness)
        
        # CORRECTION : Assigner les nouvelles cibles de manière coordonnée
        for i, ring in enumerate(active_rings):
            if i == 0:
                # Premier cercle
                ring.target_outer_radius = base_radius
            else:
                # Cercles suivants : espacés correctement
                ring.target_outer_radius = active_rings[i-1].target_outer_radius + target_spacing
            
            # S'assurer que l'inner radius est cohérent
            ring.target_inner_radius = max(10, ring.target_outer_radius - self.thickness)
        
        # Activer le rétrécissement coordonné
        self.shrinking_active = True
        
        # Créer un nouveau cercle (seulement si sous la limite)
        self._create_new_ring()
        
        # Événement audio
        shrink_event = AudioEvent(
            event_type="shrink_cycle",
            time=current_time,
            position=(self.center.x, self.center.y),
            params={
                "cycle_count": self.rings_destroyed_count,
                "circles_destroyed": self.circles_destroyed,
                "remaining_to_escape": max(0, self.max_circles_to_escape - self.circles_destroyed),
                "shrink_factor": shrink_ratio
            }
        )
        if event_collector:
            event_collector(shrink_event)
        
        if self.gap_detection_debug:
            print(f"SHRINK CYCLE #{self.rings_destroyed_count} - COORDINATED")
            print(f"  Base radius: {base_radius:.1f}")
            print(f"  Target spacing: {target_spacing:.1f}")
            print(f"  New targets:")
            for i, ring in enumerate(active_rings):
                print(f"    Ring {i}: {ring.outer_radius:.1f} -> {ring.target_outer_radius:.1f}")


    def _detect_gap_passage(self, ball, ball_index, ring, ring_index, current_time):
        """MÉTHODE CORRIGÉE: Détection simple et fiable du passage dans le trou"""
        if ring.state != 'arc' or ring.gap_angle <= 0:
            return False
        
        # Calculer la position relative et l'angle
        to_ball = ball.pos - ring.center
        distance_from_center = to_ball.length()
        
        if distance_from_center == 0:
            return False
        
        current_angle = (-math.degrees(math.atan2(to_ball.y, to_ball.x))) % 360
        
        # CORRECTION: Vérification simplifiée - la balle doit être DANS le cercle
        is_inside_ring = (ring.inner_radius - ball.radius) <= distance_from_center <= (ring.inner_radius + ball.radius)
        
        if not is_inside_ring:
            return False
        
        # Vérifier si la balle est dans le gap
        currently_in_gap = ring.is_in_gap(current_angle)
        
        if not currently_in_gap:
            return False
        
        # CORRECTION: Vérification du mouvement - la balle doit se diriger vers l'intérieur
        if len(self.ball_previous_positions[ball_index]) > 0:
            prev_pos = self.ball_previous_positions[ball_index][-1]
            prev_distance = (prev_pos - ring.center).length()
            
            # La balle traverse de l'extérieur vers l'intérieur
            is_moving_inward = prev_distance > distance_from_center
            
            if is_moving_inward and self.gap_detection_debug:
                print(f"GAP PASSAGE: Ball {ball_index} through Ring {ring_index}")
                print(f"  Distance: {prev_distance:.1f} -> {distance_from_center:.1f}")
                print(f"  Angle: {current_angle:.1f}° (gap: {ring.get_gap_angles()})")
            
            return True
        
        return False

    def _update_ball_history(self, ball, ball_index):
        """Met à jour l'historique des positions des balles"""
        # Garder seulement les 5 dernières positions
        if ball_index not in self.ball_previous_positions:
            self.ball_previous_positions[ball_index] = []
        
        self.ball_previous_positions[ball_index].append(ball.pos.copy())
        if len(self.ball_previous_positions[ball_index]) > 5:
            self.ball_previous_positions[ball_index].pop(0)

    def _check_all_gap_passages(self, current_time):
        """MÉTHODE CORRIGÉE: Vérifie les passages avec logique claire"""
        for ball_index, ball in enumerate(self.balls):
            # Mettre à jour l'historique
            self._update_ball_history(ball, ball_index)
            
            # CORRECTION IMPORTANTE: Vérifier SEULEMENT le niveau actuel
            if self.current_level < len(self.rings):
                current_ring = self.rings[self.current_level]
                
                # CORRECTION: Vérifier que le niveau est actif ET que c'est un arc
                if (current_ring.state == 'arc' and 
                    hasattr(current_ring, '_progression_active') and 
                    current_ring._progression_active):
                    
                    if self._detect_gap_passage(ball, ball_index, current_ring, self.current_level, current_time):
                        # Passage réussi !
                        if self.gap_detection_debug:
                            print(f"LEVEL COMPLETED: {self.current_level}")
                        
                        self._handle_successful_passage(ball, current_ring, self.current_level, current_time)
                        return  # Important: sortir après le premier passage

    def _handle_successful_passage(self, ball, ring, ring_index, current_time):
        """Gère un passage réussi - VERSION CORRIGÉE"""
        # CORRECTION: Désactiver immédiatement le niveau actuel
        ring._progression_active = False
        ring.trigger_disappear(current_time, self._collect_audio_event)
        
        if self.maintain_ring_count:
            self._trigger_shrinking_cycle(current_time, self._collect_audio_event)
        
        # Progression au niveau suivant
        self.current_level += 1
        
        # Effets visuels
        ball.hit_flash = 0.3
        if hasattr(self, 'screen_shake'):
            self.screen_shake.start(intensity=3, duration=0.2)
        
        # Particules de succès avec gravité
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(50, 100)
            pos = ball.pos + pygame.math.Vector2(
                math.cos(angle) * distance,
                math.sin(angle) * distance
            )
            vel = pygame.math.Vector2(
                math.cos(angle) * random.uniform(100, 200),
                math.sin(angle) * random.uniform(100, 200)
            )
            color = self._hex_to_rgb("#00FF00")  # Vert pour succès
            
            # NOUVEAU: Particules de succès avec gravité et effet spécial
            success_gravity = self.particle_gravity * 0.5  # Gravité réduite pour effet plus spectaculaire
            life = random.uniform(8.0, 15.0)  # Durée plus longue
            screen_bounds = (self.width, self.height)
            
            ball.impact_particles.append(
                Particle(pos, vel, color, random.uniform(3, 8), life, True, 
                        success_gravity, self.particle_air_resistance, screen_bounds)
            )
        
        # CORRECTION: Activer le niveau suivant
        if self.current_level < len(self.rings):
            next_ring = self.rings[self.current_level]
            next_ring._progression_active = True
            next_ring.activate(current_time, self._collect_audio_event)
            
            if self.gap_detection_debug:
                print(f"NEXT LEVEL ACTIVATED: {self.current_level}")
                
        elif not self.has_escaped:  
            # Victoire normale
            self.game_won = True
            self.screen_shake.start(intensity=8, duration=0.5)
            self.winner_ball = ball
            self.victory_animation_time = current_time
            
            if self.gap_detection_debug:
                print("GAME WON - All levels completed!")

    def _cleanup_particles(self) -> None:
        """Nettoie les particules pour éviter les problèmes de performance"""
        total_particles_before = 0
        total_particles_after = 0
        
        for ring in self.rings:
            total_particles_before += len(ring.particles)
            if len(ring.particles) > self.max_particles_per_ring:
                ring.particles = ring.particles[-self.max_particles_per_ring:]
            total_particles_after += len(ring.particles)
        
        for ball in self.balls:
            total_particles_before += len(ball.impact_particles)
            if len(ball.impact_particles) > self.max_particles_per_ball:
                ball.impact_particles = ball.impact_particles[-self.max_particles_per_ball:]
            total_particles_after += len(ball.impact_particles)
        
        if hasattr(self, 'victory_particles'):
            total_particles_before += len(self.victory_particles)
            if len(self.victory_particles) > 50:
                self.victory_particles = self.victory_particles[-50:]
            total_particles_after += len(self.victory_particles)
        
        if total_particles_before > total_particles_after:
            logger.debug(f"Particle cleanup: {total_particles_before} → {total_particles_after}")
    
    def _auto_performance_management(self, current_fps: float) -> None:
        """Gestion automatique des performances"""
        if not self.performance_mode_auto:
            return
            
        self.performance_counter += 1
        
        if self.performance_counter % 30 == 0:
            if current_fps < self.last_fps * 0.7:
                logger.warning(f"Performance drop detected: {current_fps:.1f} FPS")
                self._apply_performance_optimizations()
            
            self.last_fps = current_fps
    
    def _apply_performance_optimizations(self) -> None:
        """Applique des optimisations automatiques de performance"""
        for ring in self.rings:
            if len(ring.particles) > 30:
                ring.particles = ring.particles[-30:]
        
        for ball in self.balls:
            if len(ball.impact_particles) > 8:
                ball.impact_particles = ball.impact_particles[-8:]
        
        self.max_particles_per_ring = max(15, self.max_particles_per_ring // 2)
        self.max_particles_per_ball = max(4, self.max_particles_per_ball // 2)
        
        logger.info("Auto performance optimizations applied")
    
    def _initialize_game(self) -> None:
        """Initialise les objets du jeu - VERSION CORRIGÉE"""
        # Réinitialiser objets
        self.rings: list[Ring] = []
        self.balls = []
        self.audio_events = []
        self.current_level = 0
        self.game_won = False
        self.winner_ball = None
        self.victory_animation_time = 0
        self.victory_particles = []
        
        # CORRECTION IMPORTANTE: Réinitialiser système de rétrécissement et d'évasion
        self.rings_destroyed_count = 0
        self.circles_destroyed = 0  # IMPORTANT: Doit commencer à 0
        self.total_rings_created = 0  # IMPORTANT: Doit commencer à 0  
        self.has_escaped = False
        self.shrinking_active = False
        self.shrink_progress = 0.0
        self.color_index = 0  # Réinitialiser index couleur
        
        if self.gap_detection_debug:
            print(f"INITIALIZATION: circles_destroyed={self.circles_destroyed}, max_to_escape={self.max_circles_to_escape}")
        
        # Initialiser les historiques de détection
        self.ball_previous_positions = {}
        self.ball_gap_states = {}
        for i in range(self.balls_count):
            self.ball_previous_positions[i] = []
            self.ball_gap_states[i] = {}
        
        # Convertir couleurs
        colors = [self._hex_to_rgb(color) for color in self.color_palette]
        
        # Créer les anneaux initiaux avec nouveau système de rotation
        for i in range(self.nb_rings):
            ring_radius = self.min_radius + i * (self.thickness + self.gap_radius)
            rotation_speed = self._get_rotation_speed_for_ring(i)  # NOUVEAU
            
            # Utiliser couleur satisfaisante avec continuité
            ring_color = self._get_next_satisfying_color()
            
            ring = Ring(
                self.center, 
                outer_radius=ring_radius,
                thickness=self.thickness,
                gap_angle=self.gap_angle,
                rotation_speed=rotation_speed,  # Utiliser la nouvelle méthode
                color=ring_color,
                simulator=self,
                random_start=self.random_arc,
                start_angle = self.start_angle + self.gap_angle_rings * i
            )
            
            # Propriétés de rétrécissement
            ring.original_outer_radius = ring_radius
            ring.target_outer_radius = ring_radius
            ring.target_inner_radius = ring.inner_radius
            ring.shrink_progress = 0.0
            
            self.rings.append(ring)
            self.total_rings_created += 1  # Compter les cercles initiaux
        
        # IMPORTANT: Log pour vérifier l'initialisation
        if self.gap_detection_debug:
            print(f"Created {len(self.rings)} initial rings. Total created: {self.total_rings_created}")
        
        # Configurer les anneaux comme arcs si all_arc est activé
        if self.all_arc:
            for ring in self.rings:
                ring.state = "arc"
            # CORRECTION IMPORTANTE: Activer le premier niveau
            if self.rings:
                self.rings[0]._progression_active = True
                logger.info("Level 0 activated for progression")
        else:
            if self.rings:
                self.rings[0].state = "arc"
                self.rings[0]._progression_active = True
                logger.info("Level 0 activated for progression")
        
        # Initialisation des balles
        for i in range(self.balls_count):
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
            
            ball_color = self._get_next_satisfying_color()
            
            text = self.text_balls[i] if i < len(self.text_balls) else f"Player {i+1}"
            if len(text) > self.max_text_length:
                text = text[:self.max_text_length - 3] + "..."
            
            ball = Ball(
                pos=start_pos,
                vel=start_vel,
                radius=self.balls_size,
                color=ball_color,
                elasticity=self.elasticity,
                text=text,
                font=self.font,
                on_text=self.on_balls_text,
                debug=self.debug,
                simulator=self
            )
            self.balls.append(ball)

    def _collect_audio_event(self, event: AudioEvent) -> None:
        """Collecte un événement audio"""
        self.audio_events.append(event)
    
    def _create_vignette(self, surface):
        """Crée un effet de vignette pour un look cinématique"""
        w, h = surface.get_size()
        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        max_radius = int(min(w, h) * 0.5)

        for r in range(1, max_radius, 2):
            alpha = int(255 * self.vignette_intensity * (r / max_radius))
            pygame.gfxdraw.filled_circle(
                vignette,
                w // 2, h // 2,
                max_radius - r,
                (0, 0, 0, alpha)
            )

        surface.blit(vignette, (0, 0))
    
    def _draw_legend(self, surface):
        """Dessine une légende améliorée si l'affichage du texte sur les balles est désactivé"""
        if not self.on_balls_text and any(ball.text for ball in self.balls):
            legend_height = 35 * len(self.balls)  # Plus compact
            legend_width = 200
            legend_x = 20
            legend_y = 20
            
            for i, ball in enumerate(self.balls):
                if ball.text:
                    circle_x = legend_x + 15
                    circle_y = legend_y + i * 35 + 15
                    
                    # Ombre pour le cercle
                    pygame.gfxdraw.filled_circle(surface, circle_x + 1, circle_y + 1, 8, (0, 0, 0))
                    pygame.gfxdraw.aacircle(surface, circle_x + 1, circle_y + 1, 8, (0, 0, 0))
                    
                    # Cercle de couleur
                    pygame.gfxdraw.filled_circle(surface, circle_x, circle_y, 8, ball.color)
                    pygame.gfxdraw.aacircle(surface, circle_x, circle_y, 8, ball.color)
                    
                    # Ombre pour le texte
                    shadow_surface = self.legend_font.render(ball.text, True, (0, 0, 0))
                    surface.blit(shadow_surface, (circle_x + 18, circle_y - 8))
                    
                    # Texte principal
                    text_surface = self.legend_font.render(ball.text, True, (255, 255, 255))
                    surface.blit(text_surface, (circle_x + 17, circle_y - 9))
    
    def _draw_question_text(self, surface):
        """Dessine la question en haut avec style TikTok amélioré"""
        if not self.question_text:
            return

        if not hasattr(self, 'question_font') or self.question_font is None:
            self.question_font = pygame.font.SysFont("Arial", 36, bold=True)  # Plus petit

        # Couleurs TikTok vibrantes
        color_cyan = "#00FFFF"
        color_pink = "#FF0080"
        shadow_col = "#000000"

        lines = self.question_text.splitlines()
        
        y0 = int(self.height * self.top_frac_text)

        for idx, line in enumerate(lines):
            base_color = self._hex_to_rgb(color_cyan if idx % 2 == 0 else color_pink)
            text_surf = self.question_font.render(line, True, base_color)
            shadow_surf = self.question_font.render(line, True, shadow_col)
            tw, th = text_surf.get_size()

            x = int((self.width - tw) * self.left_frac_text)
            y = y0 + idx * (th + 3)  # Espacement réduit

            # Ombre légère pour lisibilité
            surface.blit(shadow_surf, (x + 2, y + 2))
            surface.blit(text_surf, (x, y))
    
    def _draw_countdown(self, surface):
        """NOUVEAU : Dessine le compteur central d'évasion amélioré"""
        if not self.show_countdown:
            return
            
        remaining = max(0, self.max_circles_to_escape - self.circles_destroyed)
        
        # CORRECTION: Debug pour vérifier les valeurs
        if self.gap_detection_debug and hasattr(self, '_last_remaining_logged'):
            if self._last_remaining_logged != remaining:
                print(f"COUNTDOWN: max={self.max_circles_to_escape}, destroyed={self.circles_destroyed}, remaining={remaining}")
                self._last_remaining_logged = remaining
        elif not hasattr(self, '_last_remaining_logged'):
            self._last_remaining_logged = remaining
            if self.gap_detection_debug:
                print(f"COUNTDOWN INIT: max={self.max_circles_to_escape}, destroyed={self.circles_destroyed}, remaining={remaining}")
        
        # Animation de pulsation quand on approche de l'évasion
        if remaining <= 100:
            self.countdown_pulse += 0.1
            pulse_scale = 1.0 + 0.2 * abs(math.sin(self.countdown_pulse))  # Pulsation réduite
            color_intensity = 1.0 + 0.3 * abs(math.sin(self.countdown_pulse * 2))
        else:
            pulse_scale = 1.0
            color_intensity = 1.0
        
        # Couleurs arc-en-ciel selon la progression
        if remaining > 1500:
            color = self._hex_to_rgb("#FFFFFF")  # Blanc
        elif remaining > 1000:
            color = self._hex_to_rgb("#00FFFF")  # Cyan
        elif remaining > 500:
            color = self._hex_to_rgb("#FFFF00")  # Jaune
        elif remaining > 100:
            color = self._hex_to_rgb("#FF8000")  # Orange
        else:
            # Rouge clignotant pour les derniers
            red_intensity = int(255 * color_intensity)
            color = (red_intensity, 30, 30)
        
        # Rendu du texte principal
        countdown_text = str(remaining)
        if self.has_escaped:
            countdown_text = "ESCAPED!"
            color = self._hex_to_rgb("#00FF00")  # Vert pour succès
        
        text_surface = self.countdown_font.render(countdown_text, True, color)
        
        # Appliquer le scaling de pulsation
        if pulse_scale != 1.0:
            w, h = text_surface.get_size()
            new_w, new_h = int(w * pulse_scale), int(h * pulse_scale)
            text_surface = pygame.transform.scale(text_surface, (new_w, new_h))
        
        # Positionner au centre
        tw, th = text_surface.get_size()
        center_x = (self.width // 2) - (tw // 2)
        center_y = (self.height // 2) - (th // 2)
        
        # Ombre pour lisibilité (pas de fond transparent)
        shadow_surface = self.countdown_font.render(countdown_text, True, (0, 0, 0))
        if pulse_scale != 1.0:
            shadow_surface = pygame.transform.scale(shadow_surface, (tw, th))
        
        # Dessiner ombre puis texte
        surface.blit(shadow_surface, (center_x + 3, center_y + 3))
        surface.blit(text_surface, (center_x, center_y))
        
        # Texte informatif plus petit en dessous (sans fond)
        if not self.has_escaped and remaining > 0:
            info_font = pygame.font.SysFont("Arial", 20, bold=True)  # Plus petit
            info_text = "circles left to escape"
            info_surface = info_font.render(info_text, True, (220, 220, 220))
            info_shadow = info_font.render(info_text, True, (0, 0, 0))
            info_w = info_surface.get_width()
            
            info_x = (self.width // 2) - (info_w // 2)
            info_y = center_y + th + 5  # Espacement réduit
            
            # Ombre puis texte
            surface.blit(info_shadow, (info_x + 1, info_y + 1))
            surface.blit(info_surface, (info_x, info_y))
    
    def _draw_debug_info(self, surface):
        """Debug amélioré avec surveillance des problèmes"""
        if not self.debug:
            return
            
        debug_y = int(self.height * self.render_scale) - 140  # Plus d'espace
        
        # Informations de progression
        level_info = f"Level: {self.current_level}/{len(self.rings)}"
        if self.current_level < len(self.rings):
            current_ring = self.rings[self.current_level]
            active_status = "ACTIVE" if getattr(current_ring, '_progression_active', False) else "INACTIVE"
            level_info += f" ({active_status})"
        
        level_surface = self.font.render(level_info, True, (255, 255, 0))
        surface.blit(level_surface, (10, debug_y))
        debug_y += 20
        
        # NOUVEAU: Surveillance des espacements
        active_rings = [r for r in self.rings if r.state != "gone"]
        if len(active_rings) > 1:
            active_rings.sort(key=lambda r: r.outer_radius)
            min_spacing = float('inf')
            max_spacing = 0
            
            for i in range(len(active_rings) - 1):
                spacing = active_rings[i+1].outer_radius - active_rings[i].outer_radius
                min_spacing = min(min_spacing, spacing)
                max_spacing = max(max_spacing, spacing)
            
            spacing_info = f"Spacing: min={min_spacing:.1f}, max={max_spacing:.1f}"
            spacing_color = (255, 0, 0) if min_spacing < self.thickness else (0, 255, 0)
            spacing_surface = self.font.render(spacing_info, True, spacing_color)
            surface.blit(spacing_surface, (10, debug_y))
            debug_y += 20
        
        # Informations d'évasion
        escape_info = f"Escaped: {self.circles_destroyed}/{self.max_circles_to_escape}"
        escape_color = (0, 255, 0) if self.has_escaped else (255, 255, 255)
        escape_surface = self.font.render(escape_info, True, escape_color)
        surface.blit(escape_surface, (10, debug_y))
        debug_y += 20
        
        # État des anneaux avec indicateur de problème
        rings_active = len([r for r in self.rings if r.state != 'gone'])
        rings_info = f"Rings: {rings_active}/{len(self.rings)} active"
        if self.shrinking_active:
            rings_info += " (SHRINKING)"
        rings_surface = self.font.render(rings_info, True, (100, 200, 255))
        surface.blit(rings_surface, (10, debug_y))
        debug_y += 20
        
        # NOUVEAU: Vitesse de la balle pour détecter les problèmes
        if self.balls:
            ball_vel = self.balls[0].vel.length()
            vel_info = f"Ball velocity: {ball_vel:.1f}"
            vel_color = (255, 255, 0) if ball_vel < 700 else (255, 0, 0)  # Rouge si trop rapide
            vel_surface = self.font.render(vel_info, True, vel_color)
            surface.blit(vel_surface, (10, debug_y))
            debug_y += 20
        
        # Informations de rétrécissement
        if self.maintain_ring_count and self.shrinking_active:
            current_speed = self._calculate_dynamic_shrink_speed()
            min_radius = self.min_radius * self.min_shrink_radius_ratio
            shrink_info = f"Shrinking: {current_speed:.1f}/s | Min: {min_radius:.1f}"
            shrink_surface = self.font.render(shrink_info, True, (255, 100, 100))
            surface.blit(shrink_surface, (10, debug_y))
            debug_y += 20
            
    def _draw_victory_animation(self, surface, current_time):
        """Dessine l'animation de victoire/évasion améliorée"""
        if not self.winner_ball or self.victory_animation_time <= 0:
            return
            
        elapsed = current_time - self.victory_animation_time
        if elapsed > self.victory_animation_duration:
            return
            
        animation_factor = min(1.0, elapsed / self.victory_animation_duration)
        
        if not hasattr(self, 'victory_font') or self.victory_font is None:
            self.victory_font = pygame.font.SysFont("Arial", 60, bold=True)  # Plus petit
        
        # Texte de victoire différent selon le type
        if self.has_escaped:
            winner_name = self.winner_ball.text if self.winner_ball.text else "Player"
            victory_text = f"{winner_name} ESCAPED!"
            victory_color = self._hex_to_rgb("#00FF00")  # Vert pour évasion
        else:
            winner_name = self.winner_ball.text if self.winner_ball.text else "Player"
            victory_text = f"{winner_name} WINS!"
            victory_color = self._hex_to_rgb("#FFD700")  # Or pour victoire normale
        
        # Effet de zoom et opacité
        scale = 0.5 + 1.5 * animation_factor
        alpha = int(255 * min(1.0, animation_factor * 2))
        
        text_surface = self.victory_font.render(victory_text, True, victory_color)
        
        scaled_width = int(text_surface.get_width() * scale)
        scaled_height = int(text_surface.get_height() * scale)
        
        temp_surface = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
        pygame.transform.scale(text_surface, (scaled_width, scaled_height), temp_surface)
        temp_surface.set_alpha(alpha)
        
        center_x = (self.width // 2) - (scaled_width // 2)
        center_y = (self.height // 2) - (scaled_height // 2)
        
        # Pulsation améliorée
        pulse = 1.0 + 0.2 * math.sin(elapsed * 8)
        pulse_width = int(scaled_width * pulse)
        pulse_height = int(scaled_height * pulse)
        
        pulse_surface = pygame.transform.scale(temp_surface, (pulse_width, pulse_height))
        surface.blit(pulse_surface, 
                    (center_x - (pulse_width - scaled_width)//2, 
                     center_y - (pulse_height - scaled_height)//2))
        
        # Particules améliorées pour l'évasion
        if random.random() < 0.4:
            for _ in range(8):
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(150, 400) * animation_factor
                pos_x = center_x + scaled_width/2 + math.cos(angle) * distance
                pos_y = center_y + scaled_height/2 + math.sin(angle) * distance
                
                vel_x = math.cos(angle) * random.uniform(100, 300)
                vel_y = math.sin(angle) * random.uniform(100, 300)
                
                # Couleurs spéciales pour l'évasion
                if self.has_escaped:
                    color = self._hex_to_rgb(random.choice(["#00FF00", "#00F2EA", "#FFD700"]))
                else:
                    color = self._hex_to_rgb(random.choice(self.color_palette))
                
                size = random.uniform(8, 20)
                life = random.uniform(10.0, 20.0)  # Durée plus longue
                
                # NOUVEAU: Particules de victoire avec gravité spectaculaire
                victory_gravity = self.particle_gravity * 0.3  # Gravité très réduite pour effet magique
                screen_bounds = (self.width, self.height)
                
                self.victory_particles.append(Particle(
                    (pos_x, pos_y), 
                    (vel_x, vel_y), 
                    color, size, life, True,
                    victory_gravity, self.particle_air_resistance, screen_bounds
                ))
        
        # Mettre à jour et dessiner les particules
        self.victory_particles = [p for p in self.victory_particles if p.update(1/self.fps)]
        for particle in self.victory_particles:
            particle.draw(surface)
        
        # Flash global plus intense pour l'évasion
        if elapsed < 0.5:
            flash_alpha = int(255 * (1.0 - elapsed / 0.5))
            if self.has_escaped:
                flash_color = (0, 255, 0, flash_alpha)  # Flash vert
            else:
                flash_color = (255, 255, 255, flash_alpha)  # Flash blanc
            
            flash_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash_surface.fill(flash_color)
            surface.blit(flash_surface, (0, 0))

    def _draw_fps_counter(self, surface, fps):
        """Affiche un compteur de FPS"""
        fps_text = f"FPS: {fps:.1f}"
        fps_surface = self.font.render(fps_text, True, (255, 255, 0))
        surface.blit(fps_surface, (10, int(self.height * self.render_scale) - 30))
    
    def _draw_frame_counter(self, surface, current_frame, total_frames):
        """Affiche un compteur de frames"""
        frame_text = f"Frame: {current_frame}/{total_frames}"
        frame_surface = self.font.render(frame_text, True, (255, 255, 0))
        surface.blit(frame_surface, (10, int(self.height * self.render_scale) - 60))
    
    def generate_direct_frames(self) -> bool:
        """Génère les frames directement en PNG - VERSION AMÉLIORÉE"""
        try:
            pygame.init()
            self._initialize_game()
            
            w, h = int(self.width * self.render_scale), int(self.height * self.render_scale)

            render_surf = pygame.Surface((w, h))
            display_surf = pygame.Surface((w, h))
            
            dt = 1.0 / self.fps
            clock = pygame.time.Clock()
            
            logger.info(f"Starting frame rendering ({self.total_frames} frames)")
            
            for i in range(self.total_frames):
                current_time = i * dt
                
                # Mise à jour simulation
                self.screen_shake.update(dt)
                self._shrink_all_rings(dt)
                
                if i % 60 == 0:
                    self._cleanup_particles()
                
                for ring in self.rings:
                    ring.update(dt, [ball.pos for ball in self.balls])
                    for e in ring.events:
                        self._collect_audio_event(e)
                    ring.events.clear()
                
                # Mise à jour des balles
                for ball in self.balls:
                    ball.update(dt, self.gravity, (w, h), self.rings, current_time, self._collect_audio_event)
                
                # NOUVELLE LOGIQUE DE DÉTECTION DES PASSAGES
                self._check_all_gap_passages(current_time)
                
                # Rendu
                render_surf.fill(BACKGROUND)
                
                # Dessiner objets
                for ring in reversed(self.rings):
                    ring.draw(render_surf)
                
                for ball in self.balls:
                    ball.draw(render_surf)
                
                # UI
                self._draw_legend(render_surf)
                self._draw_question_text(render_surf)
                self._draw_countdown(render_surf)  # NOUVEAU
                self._draw_victory_animation(render_surf, current_time)
                
                # Post-processing
                display_surf.fill(BACKGROUND)
                self.screen_shake.apply(render_surf, display_surf)
                display_surf = render_surf

                # Debug info
                if self.debug:
                    current_fps = clock.get_fps()
                    if i % 30 == 0:
                        self._draw_fps_counter(display_surf, current_fps)
                        self._draw_frame_counter(display_surf, i, self.total_frames)
                        self._draw_debug_info(display_surf)
                        self._auto_performance_management(current_fps)
                
                # Sauvegarder frame
                frame_filename = os.path.join(self.frames_dir, f"frame_{i:06d}.png")
                pygame.image.save(display_surf, frame_filename)
                
                if i % 60 == 0:
                    logger.info(f"Frame {i}/{self.total_frames} rendered (Destroyed: {self.circles_destroyed}/{self.max_circles_to_escape})")
                
                self.current_frame = i
                clock.tick()
            
            pygame.quit()
            
            logger.info("Frame assembly to video...")
            return self._create_video_from_frames()
            
        except Exception as e:
            logger.error(f"Error during direct frame generation: {e}")
            import traceback
            traceback.print_exc()
            pygame.quit()
            return False
    
    def generate(self) -> Optional[str]:
        """Génère la vidéo de simulation"""
        # Si direct_frames activé
        if self.direct_frames:
            logger.info("Direct frames mode enabled")
            if self.generate_direct_frames():
                return self.output_path
            logger.warning("Direct frames failed, falling back to FFmpeg pipe")

        # Mode FFmpeg pipe (code existant adapté)
        w, h = int(self.width * self.render_scale), int(self.height * self.render_scale)
        screen_w, screen_h = int(self.width * self.screen_scale), int(self.height * self.screen_scale)

        pygame.init()
        self._initialize_game()
        screen = pygame.display.set_mode((screen_w, screen_h))
        pygame.display.set_caption("Enhanced TikTok Circle Simulator")

        # Setup FFmpeg
        ffmpeg_bin = getattr(self, 'ffmpeg_path', None) or shutil.which('ffmpeg')
        if not ffmpeg_bin or not os.path.isfile(ffmpeg_bin):
            logger.error("FFmpeg not found")
            pygame.quit()
            return None

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
            '-b:v', '8000k', '-maxrate', '8000k', '-bufsize', '16000k',
            '-threads','0','-pix_fmt','yuv420p', self.output_path
        ]
        
        logger.info(f"FFmpeg command: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        # Thread d'envoi
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
        render_surf = pygame.Surface((w,h))
        display_surf = pygame.Surface((w,h))
        dt = 1.0/self.fps
        clock = pygame.time.Clock()

        for i in range(self.total_frames):
            current_time = i * dt
            render_surf.fill(BACKGROUND)
            
            # Update simulation
            self.screen_shake.update(dt)
            self._shrink_all_rings(dt)
            
            if i % 60 == 0:
                self._cleanup_particles()
            
            for ring in self.rings:
                ring.update(dt, [b.pos for b in self.balls])
                for e in ring.events:
                    self._collect_audio_event(e)
                ring.events.clear()
            
            for ball in self.balls:
                ball.update(dt, self.gravity, (w, h), self.rings, current_time, self._collect_audio_event)

            # NOUVELLE LOGIQUE DE DÉTECTION DES PASSAGES
            self._check_all_gap_passages(current_time)

            # Dessin
            for ring in reversed(self.rings): 
                ring.draw(render_surf)
            for ball in self.balls: 
                ball.draw(render_surf)
            
            self._draw_legend(render_surf)
            self._draw_question_text(render_surf)
            self._draw_countdown(render_surf)  # NOUVEAU
            self._draw_victory_animation(render_surf, current_time)

            # Post-processing
            display_surf.fill(BACKGROUND)
            self.screen_shake.apply(render_surf, display_surf)

            if self.debug:
                if i % 30 == 0:
                    current_fps = clock.get_fps()
                    self._draw_fps_counter(display_surf, current_fps)
                    self._draw_frame_counter(display_surf, i, self.total_frames)
                    self._draw_debug_info(display_surf)
                    self._auto_performance_management(current_fps)

            # Affichage
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
                _ = q.get(); q.put(raw)

            self.current_frame = i
            clock.tick(120)

        # Finalisation
        q.put(None)
        try:
            proc.wait(timeout=60)
            if proc.returncode != 0:
                logger.error(f"FFmpeg failed with code: {proc.returncode}")
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout, forcing stop")
            proc.kill()
            proc.wait()
        except Exception as e:
            logger.error(f"FFmpeg finalization error: {e}")
            proc.terminate()
        
        pygame.quit()

        if os.path.exists(self.output_path) and os.path.getsize(self.output_path) > 1000:
            logger.info(f"Video created successfully → {self.output_path}")
            return self.output_path

        logger.warning("FFmpeg pipe failed, trying direct frames")
        if self.generate_direct_frames():
            return self.output_path

        return None

    def _create_video_from_frames(self) -> Optional[str]:
        """Crée une vidéo à partir des frames avec fallback robuste"""
        try:
            ffmpeg_bin = getattr(self, 'ffmpeg_path', None) or shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
            if not ffmpeg_bin or not os.path.isfile(ffmpeg_bin):
                logger.error("FFmpeg not found: add it to PATH or configure 'ffmpeg_path'.")
                return None
            
            frame_pattern = os.path.join(self.frames_dir, "frame_%06d.png")
            
            cmd = [
                ffmpeg_bin, '-y',
                '-framerate', str(self.fps),
                '-i', frame_pattern
            ]
            
            # Système de fallback
            encoders_to_try = []
            
            try:
                encoders_list = subprocess.check_output([ffmpeg_bin, '-hide_banner', '-encoders'], 
                                                      stderr=subprocess.DEVNULL).decode()
                
                if self.use_gpu_acceleration:
                    if 'h264_nvenc' in encoders_list:
                        encoders_to_try.append(('h264_nvenc', ['-preset', 'p1', '-tune', 'hq', '-rc', 'vbr', '-cq', '23']))
                    if 'h264_amf' in encoders_list:
                        encoders_to_try.append(('h264_amf', ['-quality', 'balanced', '-rc', 'cqp', '-qp_i', '22']))
                    if 'h264_qsv' in encoders_list:
                        encoders_to_try.append(('h264_qsv', ['-preset', 'medium', '-global_quality', '23']))
                
                encoders_to_try.append(('libx264', ['-preset', 'medium', '-crf', '23']))
                
            except Exception as e:
                logger.warning(f"Encoder detection error: {e}")
                encoders_to_try = [('libx264', ['-preset', 'medium', '-crf', '23'])]
            
            # Essayer chaque encodeur
            for encoder, params in encoders_to_try:
                try:
                    full_cmd = cmd + ['-c:v', encoder] + params + [
                        '-pix_fmt', 'yuv420p',
                        self.output_path
                    ]
                    
                    logger.info(f"Trying encoding with {encoder}")
                    
                    # Test rapide
                    test_cmd = [ffmpeg_bin, '-f', 'lavfi', '-i', 'testsrc2=duration=0.1:size=100x100', 
                               '-c:v', encoder] + params[:2] + ['-f', 'null', '-']
                    
                    subprocess.run(test_cmd, capture_output=True, timeout=5, check=True)
                    
                    # Vraie vidéo
                    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=120)
                    
                    if result.returncode == 0:
                        logger.info(f"Video created successfully with {encoder}: {self.output_path}")
                        return self.output_path
                    else:
                        logger.warning(f"Failed with {encoder}: {result.stderr[:200]}...")
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"Timeout with {encoder}")
                    continue
                except Exception as e:
                    logger.warning(f"Error with {encoder}: {e}")
                    continue
            
            # Fallback MoviePy
            logger.warning("All FFmpeg encoders failed, trying MoviePy...")
            return self._create_video_with_moviepy_fallback()
            
        except Exception as e:
            logger.error(f"Video creation error: {e}")
            return None
    
    def _create_video_with_moviepy_fallback(self) -> Optional[str]:
        """Méthode de fallback avec MoviePy"""
        try:
            from moviepy.editor import ImageSequenceClip
            
            clip = ImageSequenceClip(self.frames_dir, fps=self.fps)
            
            clip.write_videofile(
                self.output_path,
                codec='libx264',
                fps=self.fps,
                audio=False,
                threads=4,
                preset='medium',
                bitrate='2000k',
                verbose=False,
                logger=None
            )
            
            clip.close()
            
            logger.info(f"Video created with MoviePy: {self.output_path}")
            return self.output_path
            
        except ImportError:
            logger.error("MoviePy not available for fallback")
            return None
        except Exception as e:
            logger.error(f"MoviePy fallback error: {e}")
            return None
    
    def get_audio_events(self) -> List[AudioEvent]:
        """Récupère les événements audio générés"""
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


class Particle:
    """Particule pour les effets visuels avec gravité et physique améliorée - VERSION CORRIGÉE"""
    
    def __init__(self, pos, vel, color, size, life, glow=False, gravity=None, air_resistance=0.98, screen_bounds=None):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.glow = glow
        self.gravity = gravity if gravity else pygame.math.Vector2(0, 200)
        self.air_resistance = air_resistance
        self.screen_bounds = screen_bounds  # (width, height) pour détecter la sortie d'écran
        self.use_screen_bounds = screen_bounds is not None
    
    def update(self, dt):
        # Appliquer la gravité
        self.vel += self.gravity * dt
        
        # Appliquer la résistance de l'air
        self.vel *= self.air_resistance
        
        # Mettre à jour la position
        self.pos += self.vel * dt
        
        # NOUVEAU: Vérifier sortie d'écran au lieu du timer de vie
        if self.use_screen_bounds:
            width, height = self.screen_bounds
            # Particule sort de l'écran = disparaît
            if (self.pos.x < -self.size * 2 or self.pos.x > width + self.size * 2 or
                self.pos.y < -self.size * 2 or self.pos.y > height + self.size * 2):
                return False
        
        # Diminuer la durée de vie (backup au cas où)
        self.life -= dt
        
        # Retourner True si encore vivante
        return self.life > 0 if not self.use_screen_bounds else True
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        # CORRECTION: Utiliser seulement RGB pour pygame.gfxdraw
        color_rgb = self.color[:3]  # Prendre seulement RGB, ignorer alpha
        
        particle_surf = pygame.Surface((int(self.size*2.5), int(self.size*2.5)), pygame.SRCALPHA)
        
        if self.glow:
            glow_radius = int(self.size * 2)
            # CORRECTION: glow_color en RGB seulement
            glow_color_rgb = self.color[:3]
            pygame.gfxdraw.filled_circle(particle_surf, glow_radius//2, glow_radius//2, glow_radius//2, glow_color_rgb)
            pygame.gfxdraw.aacircle(particle_surf, glow_radius//2, glow_radius//2, glow_radius//2, glow_color_rgb)
        
        # CORRECTION: color en RGB seulement
        pygame.gfxdraw.filled_circle(particle_surf, int(self.size), int(self.size), int(self.size), color_rgb)
        pygame.gfxdraw.aacircle(particle_surf, int(self.size), int(self.size), int(self.size), color_rgb)
        
        # Appliquer l'alpha à toute la surface
        particle_surf.set_alpha(alpha)
        surface.blit(particle_surf, (int(self.pos.x - self.size), int(self.pos.y - self.size)))

class Ball:
    """Balle avec système de collision continue (CCD) et effets visuels améliorés - VERSION CORRIGÉE"""

    def __init__(self, pos, vel, radius=20, color=(255, 255, 255), elasticity=1.01, 
                 text="", font=None, on_text=True, simulator=None, debug=False):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.radius = radius
        self.color = color
        self.elasticity = elasticity
        self.simulator = simulator
        self.debug = debug
        
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
        
        if self.text and self.font and self.on_text:
            self.text_surface = self.font.render(self.text, True, (255, 255, 255))
        
        # Particules d'impact
        self.impact_particles = []

    def create_impact_particles(self, normal):
        """Crée des particules lors d'un impact avec gravité améliorée"""
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
            life = random.uniform(5.0, 10.0)  # Durée de vie plus longue car on utilise les limites d'écran
            glow = random.random() < 0.3
            
            # NOUVEAU: Utiliser les paramètres de gravité du simulateur avec limites d'écran
            gravity = self.simulator.particle_gravity if self.simulator else pygame.math.Vector2(0, 200)
            air_resistance = self.simulator.particle_air_resistance if self.simulator else 0.98
            screen_bounds = (self.simulator.width, self.simulator.height) if self.simulator else None
            
            self.impact_particles.append(Particle(
                impact_point, vel, color, size, life, glow, gravity, air_resistance, screen_bounds
            ))

    def update(self, dt, gravity, screen_size, rings, current_time, event_collector):
        """Mise à jour avec collision detection corrigée pour la rotation"""
        
        # Appliquer la gravité
        self.vel += gravity * dt
        
        # CORRECTION: Limiter la vitesse pour éviter les bugs
        max_velocity = 400  # Réduit pour plus de stabilité
        if self.vel.length() > max_velocity:
            self.vel = self.vel.normalize() * max_velocity
        
        # CORRECTION: Vérification des cercles valides
        valid_rings = [ring for ring in rings if 
                    ring.state not in ("disappearing", "gone") and 
                    ring.outer_radius > 0 and 
                    ring.inner_radius > 0]
        
        if not valid_rings:
            self.pos += self.vel * dt
            return
        
        # NOUVEAU: Mouvement par petits pas avec rotation compensée
        steps = max(3, int(self.vel.length() * dt / 20))  # Pas adaptatif
        sub_dt = dt / steps
        
        for step in range(steps):
            # Position initiale et cible
            pos_start = self.pos.copy()
            pos_target = pos_start + self.vel * sub_dt
            
            # CORRECTION: Précompenser la rotation pendant ce sous-pas
            compensated_rings = []
            for ring in valid_rings:
                # Calculer où sera le gap à la fin du sous-pas
                future_rotation = ring.rotation_speed * sub_dt * 0.5  # Compensation partielle
                compensated_gap_start = (ring.arc_start + future_rotation) % 360
                
                compensated_rings.append({
                    'ring': ring,
                    'gap_start': compensated_gap_start,
                    'gap_end': (compensated_gap_start + ring.gap_angle) % 360
                })
            
            # Détection de collision avec compensation de rotation
            collision_found = False
            min_t = 1.0
            best_collision = None
            
            move_vector = pos_target - pos_start
            move_length = move_vector.length()
            
            if move_length > 0:
                move_dir = move_vector.normalize()
                
                for comp_ring in compensated_rings:
                    ring = comp_ring['ring']
                    
                    # Test collision cercle extérieur
                    for is_inner in [False, True]:
                        collision_radius = (ring.inner_radius - self.radius) if is_inner else (ring.outer_radius + self.radius)
                        
                        if collision_radius <= 0:
                            continue
                        
                        # Calcul intersection rayon-cercle
                        to_center = pos_start - ring.center
                        a = move_vector.dot(move_vector)
                        b = 2 * to_center.dot(move_vector)
                        c = to_center.dot(to_center) - collision_radius * collision_radius
                        
                        discriminant = b*b - 4*a*c
                        if discriminant < 0 or a == 0:
                            continue
                        
                        sqrt_disc = math.sqrt(discriminant)
                        t1 = (-b - sqrt_disc) / (2*a)
                        t2 = (-b + sqrt_disc) / (2*a)
                        
                        for t in [t1, t2]:
                            if 0 <= t < min_t:
                                collision_point = pos_start + move_vector * t
                                to_collision = collision_point - ring.center
                                
                                if to_collision.length() == 0:
                                    continue
                                
                                # CORRECTION: Vérifier gap avec rotation compensée
                                angle = (-math.degrees(math.atan2(to_collision.y, to_collision.x))) % 360
                                
                                # Utiliser les angles compensés pour la rotation
                                gap_start = comp_ring['gap_start']
                                gap_end = comp_ring['gap_end']
                                
                                in_gap = False
                                if gap_start <= gap_end:
                                    in_gap = gap_start <= angle <= gap_end
                                else:
                                    in_gap = angle >= gap_start or angle <= gap_end
                                
                                if ring.state == "arc" and in_gap:
                                    continue  # Dans le gap, pas de collision
                                
                                # Collision valide trouvée
                                normal = to_collision.normalize()
                                if is_inner:
                                    normal = -normal
                                
                                min_t = t
                                best_collision = (ring, collision_point, normal, is_inner)
                                collision_found = True
            
            # Appliquer la collision ou le mouvement
            if collision_found:
                ring, collision_point, normal, is_inner = best_collision
                
                # Position après collision
                self.pos = pos_start + move_vector * min_t
                
                # CORRECTION: Réflexion stable avec amortissement
                velocity_normal = self.vel.dot(normal)
                if velocity_normal < 0:  # S'approche de la surface
                    # Réflexion avec légère perte d'énergie pour stabilité
                    reflection = -2 * velocity_normal * normal
                    self.vel += reflection * self.elasticity * 0.98  # Amortissement
                    
                    # Effets visuels
                    self.hit_flash = 0.1
                    self.collision = True
                    self.create_impact_particles(normal)
                    
                    # Légère séparation pour éviter les collisions multiples
                    self.pos += normal * 0.5
            else:
                # Mouvement libre
                self.pos = pos_target
            
            # Mettre à jour la rotation des cercles pour le prochain sous-pas
            for ring in valid_rings:
                ring.arc_start = (ring.arc_start + ring.rotation_speed * sub_dt) % 360
        
        # Mise à jour des effets visuels
        self.trail.append(self.pos.copy())
        if len(self.trail) > self.max_trail: 
            self.trail.pop(0)
        
        self.impact_particles = [p for p in self.impact_particles if p.update(dt)]
        
        if self.hit_flash > 0: 
            self.hit_flash -= dt
        
        self.collision = False
        self.in_gap = False
        
    def draw(self, surface):
        """Rendu avec effets visuels améliorés"""
        # Traînée
        for i, pos in enumerate(self.trail):
            alpha = int(200 * (i / len(self.trail)) ** self.trail_fade)
            size = int(self.radius * (0.4 + 0.6 * i / len(self.trail)))
            
            if self.hit_flash > 0:
                trail_color = (255, 255, 255)
            else:
                r, g, b = self.color
                brightness = int(50 * (i / len(self.trail)))
                trail_color = (min(255, r + brightness), min(255, g + brightness), min(255, b + brightness))
            
            if size > 0:
                trail_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.gfxdraw.filled_circle(trail_surface, size, size, size, trail_color)
                pygame.gfxdraw.aacircle(trail_surface, size, size, size, trail_color)
                trail_surface.set_alpha(alpha)
                surface.blit(trail_surface, (int(pos.x - size), int(pos.y - size)))
        
        # Particules d'impact
        for particle in self.impact_particles:
            particle.draw(surface)
        
        # Balle principale
        draw_color = self.color
        
        if self.collision:
            draw_color = (255, 100, 100)
        elif self.in_gap:
            draw_color = (100, 255, 100)
        
        # Flash blanc
        if self.hit_flash > 0:
            flash_intensity = self.hit_flash / 0.1
            flash_color = (
                min(255, draw_color[0] + int(150 * flash_intensity)),
                min(255, draw_color[1] + int(150 * flash_intensity)),
                min(255, draw_color[2] + int(150 * flash_intensity))
            )
            
            glow_radius = int(self.radius * 1.3)
            glow_surface = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
            pygame.gfxdraw.filled_circle(glow_surface, glow_radius, glow_radius, glow_radius, flash_color)
            pygame.gfxdraw.aacircle(glow_surface, glow_radius, glow_radius, glow_radius, flash_color)
            glow_surface.set_alpha(100)
            surface.blit(glow_surface, (int(self.pos.x - glow_radius), int(self.pos.y - glow_radius)))
        
        # Cercle principal
        pygame.gfxdraw.filled_circle(surface, int(self.pos.x), int(self.pos.y), int(self.radius), draw_color)
        pygame.gfxdraw.aacircle(surface, int(self.pos.x), int(self.pos.y), int(self.radius), draw_color)
        
        # Reflet
        highlight_pos = (int(self.pos.x - self.radius * 0.3), int(self.pos.y - self.radius * 0.3))
        highlight_radius = int(self.radius * 0.4)
        highlight_surface = pygame.Surface((highlight_radius*2, highlight_radius*2), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(highlight_surface, highlight_radius, highlight_radius, highlight_radius, (255, 255, 255))
        pygame.gfxdraw.aacircle(highlight_surface, highlight_radius, highlight_radius, highlight_radius, (255, 255, 255))
        highlight_surface.set_alpha(100)
        surface.blit(highlight_surface, (highlight_pos[0] - highlight_radius, highlight_pos[1] - highlight_radius))
        
        # Texte sur la balle (sans fond transparent)
        if self.text and self.on_text and self.text_surface:
            text_width, text_height = self.text_surface.get_size()
            text_pos = (int(self.pos.x - text_width // 2), int(self.pos.y - text_height // 2))
            
            # Ombre pour lisibilité (plus simple)
            shadow_surface = self.font.render(self.text, True, (0, 0, 0))
            surface.blit(shadow_surface, (text_pos[0] + 1, text_pos[1] + 1))
            
            # Texte principal
            surface.blit(self.text_surface, text_pos)


class Ring:
    """Anneau avec trouée et système de collision continue (CCD) + rétrécissement - VERSION CORRIGÉE"""

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
        self.state = "circle"
        self.disappear_timer = 1.0
        self.glow_intensity = 0.0
        
        # NOUVEAU: Marqueur de progression pour distinguer les niveaux actifs
        self._progression_active = False
        
        # Propriétés de rétrécissement
        self.original_outer_radius = outer_radius
        self.target_outer_radius = outer_radius
        self.target_inner_radius = self.inner_radius
        self.shrink_progress = 0.0
        
        # Animation
        self.pulse_timer = 0.0
        self.pulse_period = 1.5
        self.pulse_amount = 0.2
        self.color_shift_timer = 0.0
        self.color_shift_period = 3.0
        self.color_hue_shift = 0.0
        
        # Effets
        self.particles = []
        self.events = []
    
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
        
        if gap_start <= gap_end:
            return gap_start <= angle <= gap_end
        else:
            return angle >= gap_start or angle <= gap_end
    
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
        
        # Conversion RGB vers HSV
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
        
        # Animations
        h = (h + self.color_hue_shift) % 360
        v = v * (1 + np.sin(2 * np.pi * self.pulse_timer / self.pulse_period) * self.pulse_amount)
        v = min(1.0, max(0.3, v))
        
        return self.hsv_to_rgb(h, s, v)

    def _handle_collision_effects(self, ball, current_time, event_collector, dot_product, normal):
        """Gère tous les effets de collision"""
        ball.hit_flash = 0.1
        ball.create_impact_particles(normal)
        ball.collision = True
        self.glow_intensity = 0.5
        
        # Secousse d'écran
        impact_force = abs(dot_product) / 200
        if self.simulator and hasattr(self.simulator, 'screen_shake') and impact_force > 0.2:
            self.simulator.screen_shake.start(
                intensity=min(5, impact_force * 2),
                duration=min(0.1, impact_force * 0.05)
            )
        
        # Particules
        particles_to_create = min(5, int(impact_force * 10))
        for _ in range(particles_to_create):
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
    
    def create_particle(self, has_glow=False):
        """Crée une particule avec contrôle de performance et gravité améliorée"""
        if len(self.particles) > 150:
            return
            
        angle = random.uniform(0, np.pi * 2)
        radius = random.uniform(self.inner_radius, self.outer_radius)
        
        pos = (
            self.center.x + np.cos(angle) * radius,
            self.center.y + np.sin(angle) * radius
        )
        
        dir_vec = pygame.math.Vector2(np.cos(angle), np.sin(angle))
        vel = dir_vec * random.uniform(50, 150)
        
        base_color = self.get_animated_color()
        color_var = 30
        
        # CORRECTION: S'assurer que la couleur est en RGB valide
        color = (
            max(0, min(255, base_color[0] + random.randint(-color_var, color_var))),
            max(0, min(255, base_color[1] + random.randint(-color_var, color_var))),
            max(0, min(255, base_color[2] + random.randint(-color_var, color_var)))
        )
        
        size = random.uniform(2, 5)
        life = random.uniform(5.0, 12.0)
        
        # Utiliser les paramètres de gravité du simulateur avec limites d'écran
        gravity = self.simulator.particle_gravity if self.simulator else pygame.math.Vector2(0, 200)
        air_resistance = self.simulator.particle_air_resistance if self.simulator else 0.98
        screen_bounds = (self.simulator.width, self.simulator.height) if self.simulator else None
        
        self.particles.append(Particle(pos, vel, color, size, life, glow=has_glow, 
                                    gravity=gravity, air_resistance=air_resistance, screen_bounds=screen_bounds))

    def activate(self, current_time, event_collector=None):
        """Active l'anneau"""
        if self.state == "circle":
            self.state = "arc"
            
            event = AudioEvent(
                event_type="activation",
                time=current_time,
                position=(self.center.x, self.center.y)
            )
            self.events.append(event)
            if event_collector:
                event_collector(event)
            
            for _ in range(15):
                self.create_particle(has_glow=True)
    
    def trigger_disappear(self, current_time, event_collector=None):
        """Déclenche la disparition"""
        if self.state == "arc":
            self.state = "disappearing"
            
            event = AudioEvent(
                event_type="explosion",
                time=current_time,
                position=(self.center.x, self.center.y),
                params={"size": "large"}
            )
            self.events.append(event)
            if event_collector:
                event_collector(event)
            
            if self.simulator and hasattr(self.simulator, 'screen_shake'):
                self.simulator.screen_shake.start(intensity=8, duration=0.3)
            
            for _ in range(50):
                self.create_particle(has_glow=True)
    
    def update(self, dt, ball_positions=None):
        """Mise à jour de l'anneau"""
        self.pulse_timer = (self.pulse_timer + dt) % self.pulse_period
        self.color_shift_timer = (self.color_shift_timer + dt) % self.color_shift_period
        
        if self.state == "arc":
            self.color_hue_shift = (self.color_hue_shift + 15 * dt) % 360
            self.arc_start = (self.arc_start + self.rotation_speed * dt) % 360
            
            if ball_positions:
                min_dist = float('inf')
                for ball_pos in ball_positions:
                    dist = (ball_pos - self.center).length()
                    if dist < min_dist:
                        min_dist = dist
                
                proximity = max(0, 1 - abs(min_dist - self.inner_radius) / (self.thickness * 2))
                self.glow_intensity = proximity * 0.8
        
        elif self.state == "disappearing":
            self.disappear_timer -= dt
            if self.disappear_timer <= 0:
                self.state = "gone"
            
            if random.random() < 20 * dt:
                self.create_particle(has_glow=True)
        
        self.particles = [p for p in self.particles if p.update(dt)]
        
        if len(self.particles) > 200:
            self.particles = self.particles[-200:]
    
    def draw_filled_arc(self, surface, center, inner_radius, outer_radius, start_angle, end_angle, color):
        """Dessine un arc rempli"""
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
        
        if len(points) >= 3:
            pygame.gfxdraw.filled_polygon(surface, points, color)
            pygame.gfxdraw.aapolygon(surface, points, color)
    
    def draw(self, surface):
        """Rendu amélioré avec correction des couleurs"""
        if self.state == "gone":
            return
        
        cx, cy = int(self.center.x), int(self.center.y)
        out_r = int(self.outer_radius)
        in_r = int(self.inner_radius)
        col_rgb = self.get_animated_color()
        
        fade = self.disappear_timer if self.state == "disappearing" else 1.0
        alpha = int(255 * fade)
        
        # CORRECTION: Utiliser seulement RGB pour les fonctions de base
        col = col_rgb  # RGB seulement pour pygame.gfxdraw
        
        # Cercle complet
        if self.state == "circle":
            temp_surface = pygame.Surface((out_r * 2, out_r * 2), pygame.SRCALPHA)
            
            pygame.gfxdraw.filled_circle(temp_surface, out_r, out_r, out_r, col)
            pygame.gfxdraw.aacircle(temp_surface, out_r, out_r, out_r, col)
            
            # Créer un trou au centre
            pygame.gfxdraw.filled_circle(temp_surface, out_r, out_r, in_r, (0, 0, 0, 0))
            
            # Appliquer l'alpha
            temp_surface.set_alpha(alpha)
            surface.blit(temp_surface, (cx - out_r, cy - out_r))
        
        # Arc avec trouée
        elif self.state == "arc" or self.state == "disappearing":
            arc_start = (self.arc_start + self.gap_angle) % 360
            arc_end = self.arc_start % 360
            
            # Créer une surface temporaire avec alpha
            temp_surface = pygame.Surface((out_r * 2, out_r * 2), pygame.SRCALPHA)
            
            if arc_start > arc_end:
                self.draw_filled_arc(temp_surface, (out_r, out_r), in_r, out_r, arc_start, 360, col)
                self.draw_filled_arc(temp_surface, (out_r, out_r), in_r, out_r, 0, arc_end, col)
            else:
                self.draw_filled_arc(temp_surface, (out_r, out_r), in_r, out_r, arc_start, arc_end, col)
            
            # Appliquer l'alpha
            temp_surface.set_alpha(alpha)
            surface.blit(temp_surface, (cx - out_r, cy - out_r))
        
        # Halo lumineux (CORRECTION: RGB seulement)
        if self.glow_intensity > 0 and alpha > 0:
            halo_alpha = int(120 * self.glow_intensity * fade)
            
            for r in range(in_r - 5, out_r + 5, 2):
                if r > 0:
                    # Créer une surface temporaire pour l'effet de halo
                    halo_surface = pygame.Surface((r*2+10, r*2+10), pygame.SRCALPHA)
                    pygame.gfxdraw.aacircle(halo_surface, r+5, r+5, r, col_rgb)
                    halo_surface.set_alpha(halo_alpha)
                    surface.blit(halo_surface, (cx-r-5, cy-r-5))
        
        # Particules
        for particle in self.particles:
            particle.draw(surface)