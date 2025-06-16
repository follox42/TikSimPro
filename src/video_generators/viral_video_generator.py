#!/usr/bin/env python3
"""
🔥 GÉNÉRATEUR VIRAL CORRIGÉ 🔥
Version stable sans bugs d'explosion

Corrections apportées:
- Explosion stable sans corruption des cercles
- Gestion sécurisée des particules  
- Screen shake contrôlé
- Protection contre les overflows
- Performance optimisée
"""

import pygame
import math
import random
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
import colorsys

logger = logging.getLogger("TikSimPro")

from src.video_generators.base_video_generator import IVideoGenerator
from src.core.data_pipeline import TrendData, AudioEvent

class ViralTikTokGenerator(IVideoGenerator):
    """🔥 GÉNÉRATEUR VIRAL STABLE - Version corrigée 🔥"""
    
    def __init__(self, width=1080, height=1920, fps=60, duration=30):
        super().__init__(width, height, fps, duration)
        
        # MODE PERFORMANCE VIRAL
        self.set_performance_mode(headless=False, fast=True, use_numpy=True)
        
        # 🎨 PALETTES ULTRA-VIRALES (inchangées - elles fonctionnent)
        self.viral_palettes = {
            "neon_explosion": [
                (255, 0, 102),   # Rose électrique
                (0, 255, 255),   # Cyan pur
                (255, 255, 0),   # Jaune flash
                (255, 0, 255),   # Magenta pur
                (0, 255, 102),   # Vert néon
            ],
            "sunset_vibes": [
                (255, 71, 87),   # Corail vibrant
                (255, 154, 0),   # Orange sunset
                (255, 206, 84),  # Jaune doré
                (199, 0, 57),    # Rouge profond
                (144, 12, 63),   # Violet foncé
            ],
            "galaxy_dream": [
                (138, 43, 226),  # Violet galaxie
                (255, 20, 147),  # Rose cosmique
                (0, 191, 255),   # Bleu ciel
                (50, 205, 50),   # Vert lime
                (255, 69, 0),    # Orange feu
            ],
            "rainbow_hypnotic": [
                (255, 0, 0),     # Rouge pur
                (255, 127, 0),   # Orange
                (255, 255, 0),   # Jaune
                (0, 255, 0),     # Vert
                (0, 0, 255),     # Bleu
                (75, 0, 130),    # Indigo
                (148, 0, 211),   # Violet
            ]
        }
        
        # 🎯 PARAMÈTRES VIRAUX OPTIMISÉS
        self.viral_mode = "ULTIMATE"
        self.hook_style = "COUNTDOWN"
        self.climax_mode = "EXPLOSION"
        
        # État viral
        self.center_x = width // 2
        self.center_y = height // 2
        self.circles = []
        self.particles = []
        self.current_palette = "neon_explosion"
        self.colors = self.viral_palettes[self.current_palette]
        
        # 🎪 PHASES VIRALES (timing parfait pour engagement)
        self.phases = {
            "hook": (0, 3),           # 0-3s: Hook captivant
            "build": (3, 12),         # 3-12s: Montée en puissance
            "hypnotic": (12, 22),     # 12-22s: Phase hypnotique
            "climax": (22, 27),       # 22-27s: Climax épique
            "outro": (27, 30),        # 27-30s: CTA + hook final
        }
        
        # 🔥 ÉLÉMENTS VIRAUX SÉCURISÉS
        self.viral_elements = {
            "speed_multiplier": 1.0,
            "intensity": 1.0,
            "color_shift_speed": 1.0,
            "particle_count": 0,
            "screen_shake": 0,
            "glow_effect": True,
            "rainbow_mode": False,
            "explosion_active": False,      # NOUVEAU: contrôle explosion
            "explosion_frame": 0,           # NOUVEAU: compteur explosion
            "max_particles": 50,            # NOUVEAU: limite particules
        }
        
        # 🛡️ PROTECTION CONTRE LES BUGS
        self.circle_base_properties = []    # Sauvegarde des propriétés originales
        self.explosion_start_frame = 0
        self.max_explosion_duration = 5 * fps  # 5 secondes max
        
        # Cache pour performance
        self.color_cache = {}
        self.precompute_viral_data()
        
        logger.info(f"🔥 VIRAL GENERATOR FIXED initialisé: {self.viral_mode} mode")

    def precompute_viral_data(self):
        """Pré-calcule TOUT pour performance maximale (inchangé)"""
        logger.info("🚀 Pré-calcul des données virales...")
        
        # Cache des couleurs avec variations
        for palette_name, colors in self.viral_palettes.items():
            self.color_cache[palette_name] = {}
            for i, color in enumerate(colors):
                # Variations d'intensité
                variations = []
                for intensity in [0.5, 0.7, 0.9, 1.0, 1.2, 1.5]:
                    var_color = tuple(min(255, max(0, int(c * intensity))) for c in color)
                    variations.append(var_color)
                
                # Version glow (plus claire)
                glow_color = tuple(min(255, int(c * 1.3 + 50)) for c in color)
                
                self.color_cache[palette_name][i] = {
                    'base': color,
                    'variations': variations,
                    'glow': glow_color,
                    'hsv': colorsys.rgb_to_hsv(color[0]/255, color[1]/255, color[2]/255)
                }

    def configure(self, config: Dict[str, Any]) -> bool:
        """Configuration viral-optimisée (inchangée mais sécurisée)"""
        try:
            # Params de base
            if "width" in config:
                self.width = config["width"]
                self.center_x = self.width // 2
            if "height" in config:
                self.height = config["height"]
                self.center_y = self.height // 2
            if "fps" in config:
                self.fps = config["fps"]
                # CORRECTION: Recalculer la durée max explosion
                self.max_explosion_duration = 5 * self.fps
            if "duration" in config:
                self.duration = config["duration"]
                self.total_frames = int(self.fps * self.duration)
            
            # 🔥 PARAMÈTRES VIRAUX
            self.viral_mode = config.get("viral_mode", "ULTIMATE")
            self.hook_style = config.get("hook_style", "COUNTDOWN")
            self.climax_mode = config.get("climax_mode", "EXPLOSION")
            
            # Palette
            palette_name = config.get("color_palette", "neon_explosion")
            if palette_name in self.viral_palettes:
                self.current_palette = palette_name
                self.colors = self.viral_palettes[palette_name]
            
            # Ajuster les phases selon la durée
            if self.duration != 30:
                self._adjust_phases_for_duration()
            
            logger.info(f"🔥 VIRAL configuré: {self.viral_mode}, hook: {self.hook_style}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur config viral: {e}")
            return False

    def _adjust_phases_for_duration(self):
        """Ajuste les phases selon la durée totale"""
        ratio = self.duration / 30.0
        
        self.phases = {
            "hook": (0, 3 * ratio),
            "build": (3 * ratio, 12 * ratio),
            "hypnotic": (12 * ratio, 22 * ratio),
            "climax": (22 * ratio, 27 * ratio),
            "outro": (27 * ratio, self.duration),
        }

    def apply_trend_data(self, trend_data: TrendData) -> None:
        """Application des tendances VIRAL-OPTIMISÉE (inchangée)"""
        try:
            if not trend_data:
                return
            
            # Couleurs tendance
            trend_colors = trend_data.get_recommended_colors()
            if trend_colors and len(trend_colors) >= 3:
                self.colors = self._convert_hex_colors(trend_colors)
                self.viral_palettes["trending"] = self.colors
                self.current_palette = "trending"
                self.precompute_viral_data()
                logger.info(f"🎨 Couleurs tendance appliquées: {len(self.colors)}")
            
        except Exception as e:
            logger.error(f"Erreur tendances viral: {e}")

    def _convert_hex_colors(self, hex_colors: List[str]) -> List[Tuple[int, int, int]]:
        """Conversion hex avec boost viral (inchangée)"""
        rgb_colors = []
        for color in hex_colors:
            try:
                if isinstance(color, str) and color.startswith("#"):
                    hex_color = color.lstrip("#")
                    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    # BOOST viral: augmenter la saturation
                    h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
                    s = min(1.0, s * 1.3)  # +30% saturation
                    v = min(1.0, v * 1.1)  # +10% luminosité
                    boosted_rgb = colorsys.hsv_to_rgb(h, s, v)
                    final_rgb = tuple(int(c * 255) for c in boosted_rgb)
                    rgb_colors.append(final_rgb)
            except:
                continue
        return rgb_colors if rgb_colors else self.colors

    def initialize_simulation(self) -> bool:
        """Initialisation VIRAL ULTIMATE SÉCURISÉE"""
        try:
            self.create_viral_circles()
            
            # 🛡️ NOUVEAU: Sauvegarder les propriétés originales
            self.circle_base_properties = []
            for circle in self.circles:
                base_props = {
                    'radius': circle['radius'],
                    'thickness': circle['thickness'],
                    'rotation_speed': circle['rotation_speed'],
                    'gap_angle': circle['gap_angle']
                }
                self.circle_base_properties.append(base_props)
            
            logger.info(f"🔥 Simulation VIRAL: {len(self.circles)} cercles (sécurisé)")
            return True
        except Exception as e:
            logger.error(f"Erreur init viral: {e}")
            return False

    def create_viral_circles(self):
        """Créer des cercles VIRAL-OPTIMISÉS (légèrement modifié pour stabilité)"""
        self.circles = []
        
        # Nombre optimal selon le mode
        circle_counts = {"CHILL": 8, "INTENSE": 15, "ULTIMATE": 18}  # Réduit de 20 à 18
        num_circles = circle_counts.get(self.viral_mode, 15)
        
        for i in range(num_circles):
            circle = {
                'index': i,
                'radius': 40 + i * 35,
                'thickness': 8 + i * 2,
                'rotation_speed': (i + 1) * 0.4 * self.viral_elements['speed_multiplier'],
                'rotation': random.uniform(0, 360),
                'gap_angle': 45 + i * 3,
                'gap_start': i * (360 / num_circles),
                'color_index': i % len(self.colors),
                'pulse_phase': random.uniform(0, math.pi * 2),
                'pulse_speed': 0.1 + i * 0.02,
                'glow_intensity': 1.0,
                'viral_effect': random.choice(['normal', 'pulse', 'glow']),  # Retiré 'rainbow'
                
                # État courant
                'current_rotation': 0,
                'current_gap_start': 0,
                'current_color': self.colors[i % len(self.colors)],
                'current_thickness': 8 + i * 2,
                'alpha': 255,
                
                # 🛡️ NOUVEAU: Propriétés pour explosion sécurisée
                'explosion_radius_offset': 0,
                'explosion_thickness_offset': 0,
            }
            self.circles.append(circle)

    def render_frame(self, surface: pygame.Surface, frame_number: int, dt: float) -> bool:
        """🔥 RENDU VIRAL ULTIMATE SÉCURISÉ 🔥"""
        try:
            # Phase actuelle
            current_time = frame_number / self.fps
            current_phase = self._get_current_phase(current_time)
            
            # Fond viral adaptatif
            self._render_viral_background(surface, current_phase, frame_number)
            
            # Mise à jour état viral SÉCURISÉE
            self._update_viral_simulation_safe(frame_number, current_phase)
            
            # Rendu selon la phase CORRIGÉ
            if current_phase == "hook":
                self._render_hook_phase(surface, frame_number)
            elif current_phase == "build":
                self._render_build_phase(surface, frame_number)
            elif current_phase == "hypnotic":
                self._render_hypnotic_phase(surface, frame_number)
            elif current_phase == "climax":
                self._render_climax_phase_safe(surface, frame_number)  # CORRIGÉ
            else:  # outro
                self._render_outro_phase(surface, frame_number)
            
            # Effets post-processing viraux CONTRÔLÉS
            self._apply_viral_effects_safe(surface, current_phase, frame_number)
            
            # Audio events synchronisés
            self._trigger_audio_events(current_phase, frame_number)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur rendu viral frame {frame_number}: {e}")
            return False

    def _get_current_phase(self, time: float) -> str:
        """Détermine la phase actuelle (inchangé)"""
        for phase, (start, end) in self.phases.items():
            if start <= time < end:
                return phase
        return "outro"

    def _render_viral_background(self, surface: pygame.Surface, phase: str, frame: int):
        """Fond adaptatif selon la phase (inchangé mais avec protection)"""
        try:
            if phase == "hook":
                # Fond pulsant pour attirer l'attention
                intensity = abs(math.sin(frame * 0.2)) * 30
                bg_color = (int(15 + intensity), int(15 + intensity), int(25 + intensity))
            elif phase == "climax":
                # Fond ultra-dynamique CONTRÔLÉ
                r = int(50 + abs(math.sin(frame * 0.3)) * 30)  # Réduit de 50 à 30
                g = int(20 + abs(math.cos(frame * 0.25)) * 20)  # Réduit de 30 à 20
                b = int(40 + abs(math.sin(frame * 0.4)) * 30)   # Réduit de 40 à 30
                bg_color = (r, g, b)
            else:
                # Fond standard
                bg_color = (15, 15, 25)
            
            surface.fill(bg_color)
        except Exception as e:
            # Fallback sécurisé
            surface.fill((15, 15, 25))

    def _update_viral_simulation_safe(self, frame: int, phase: str):
        """🛡️ MISE À JOUR VIRAL SÉCURISÉE 🛡️"""
        try:
            time_factor = frame * 0.01
            
            # Intensité selon la phase
            phase_intensities = {
                "hook": 1.2,
                "build": 1.5,
                "hypnotic": 2.0,
                "climax": 2.5,  # Réduit de 3.0 à 2.5
                "outro": 1.0
            }
            intensity = phase_intensities.get(phase, 1.0)
            
            # Gérer l'explosion de manière SÉCURISÉE
            if phase == "climax":
                if not self.viral_elements['explosion_active']:
                    self.viral_elements['explosion_active'] = True
                    self.explosion_start_frame = frame
                    self.viral_elements['explosion_frame'] = 0
                    logger.debug("🔥 Explosion démarrée de manière sécurisée")
                
                self.viral_elements['explosion_frame'] = frame - self.explosion_start_frame
            else:
                # Réinitialiser l'explosion en dehors du climax
                if self.viral_elements['explosion_active']:
                    self._reset_explosion_safely()
            
            for i, circle in enumerate(self.circles):
                # Rotation avec intensité CONTRÔLÉE
                speed = circle['rotation_speed'] * min(intensity, 3.0)  # Limite à 3.0
                circle['current_rotation'] = (circle['rotation'] + speed) % 360
                circle['rotation'] = circle['current_rotation']
                
                # Gap movement
                gap_speed = speed * 0.7
                circle['current_gap_start'] = (circle['gap_start'] + gap_speed) % 360
                circle['gap_start'] = circle['current_gap_start']
                
                # Couleur virale avec rainbow mode CONTRÔLÉ
                if self.viral_elements['rainbow_mode'] or phase == "climax":
                    # Mode arc-en-ciel SÉCURISÉ
                    hue = (time_factor * 50 + circle['index'] * 30) % 360  # Réduit vitesse
                    rgb = colorsys.hsv_to_rgb(hue/360, 0.9, 1.0)  # Saturation réduite
                    circle['current_color'] = tuple(int(c * 255) for c in rgb)
                else:
                    # Couleur normale avec pulse
                    color_index = circle['color_index']
                    base_color = self.colors[color_index]
                    pulse = math.sin(time_factor * circle['pulse_speed'] * 10 + circle['pulse_phase'])
                    pulse_factor = 1.0 + pulse * 0.2 * intensity  # Réduit de 0.3 à 0.2
                    circle['current_color'] = tuple(min(255, int(c * pulse_factor)) for c in base_color)
                
                # Épaisseur virale SÉCURISÉE
                thickness_pulse = math.sin(time_factor * 5 + circle['index']) * 0.1  # Réduit de 0.2 à 0.1
                circle['current_thickness'] = circle['thickness'] * (1 + thickness_pulse * intensity)
                
                # 🛡️ GESTION EXPLOSION SÉCURISÉE
                if self.viral_elements['explosion_active'] and phase == "climax":
                    explosion_progress = min(1.0, self.viral_elements['explosion_frame'] / (2 * self.fps))
                    
                    # Offset contrôlé au lieu de multiplication directe
                    max_radius_offset = 50  # Maximum 50 pixels d'augmentation
                    max_thickness_offset = 10  # Maximum 10 pixels d'augmentation
                    
                    circle['explosion_radius_offset'] = explosion_progress * max_radius_offset * math.sin(explosion_progress * math.pi)
                    circle['explosion_thickness_offset'] = explosion_progress * max_thickness_offset * math.sin(explosion_progress * math.pi)
                else:
                    # Réinitialiser les offsets
                    circle['explosion_radius_offset'] = 0
                    circle['explosion_thickness_offset'] = 0
                
                # Alpha selon la phase
                if phase == "hook":
                    circle['alpha'] = int(255 * (0.7 + 0.3 * abs(math.sin(frame * 0.1))))
                else:
                    circle['alpha'] = 255
                    
        except Exception as e:
            logger.error(f"Erreur mise à jour simulation: {e}")
            # Réinitialisation d'urgence
            self._reset_explosion_safely()

    def _reset_explosion_safely(self):
        """🛡️ Réinitialise l'explosion de manière sécurisée"""
        try:
            self.viral_elements['explosion_active'] = False
            self.viral_elements['explosion_frame'] = 0
            
            # Restaurer les propriétés originales
            for i, circle in enumerate(self.circles):
                if i < len(self.circle_base_properties):
                    base_props = self.circle_base_properties[i]
                    circle['explosion_radius_offset'] = 0
                    circle['explosion_thickness_offset'] = 0
                    # Ne pas restaurer radius/thickness directement, juste les offsets
            
            logger.debug("🛡️ Explosion réinitialisée en sécurité")
        except Exception as e:
            logger.error(f"Erreur réinitialisation explosion: {e}")

    def _render_climax_phase_safe(self, surface: pygame.Surface, frame: int):
        """🔥 PHASE CLIMAX SÉCURISÉE - SANS BUGS 🔥"""
        try:
            if self.climax_mode == "EXPLOSION":
                self._render_explosion_climax_safe(surface, frame)
            elif self.climax_mode == "CONVERGENCE":
                self._render_convergence_climax_safe(surface, frame)
            else:
                self._render_spiral_climax_safe(surface, frame)
        except Exception as e:
            logger.error(f"Erreur climax: {e}")
            # Fallback: rendu normal
            self._render_normal_circles(surface)

    def _render_explosion_climax_safe(self, surface: pygame.Surface, frame: int):
        """🔥 EXPLOSION SÉCURISÉE - Version corrigée 🔥"""
        try:
            # Screen shake CONTRÔLÉ
            shake_intensity = 3  # Réduit de 10 à 3
            shake_x = random.randint(-shake_intensity, shake_intensity)
            shake_y = random.randint(-shake_intensity, shake_intensity)
            
            # Dessiner les cercles avec explosion SÉCURISÉE
            for circle in self.circles:
                # Calculer les nouvelles dimensions SANS modifier les originales
                current_radius = circle['radius'] + circle['explosion_radius_offset']
                current_thickness = circle['current_thickness'] + circle['explosion_thickness_offset']
                
                # Sécurités
                current_radius = max(10, min(current_radius, 1000))  # Entre 10 et 1000 pixels
                current_thickness = max(1, min(current_thickness, 50))  # Entre 1 et 50 pixels
                
                # Dessiner avec glow et shake
                shake_center = (self.center_x + shake_x, self.center_y + shake_y)
                self._draw_viral_circle_explosion(surface, circle, current_radius, current_thickness, shake_center)
            
            # Particules d'explosion CONTRÔLÉES
            if frame % 8 == 0:  # Moins fréquent: tous les 8 frames au lieu de 2
                self._spawn_explosion_particles_safe(3)  # Moins de particules: 3 au lieu de 10
                
        except Exception as e:
            logger.error(f"Erreur explosion: {e}")
            # Fallback
            self._render_normal_circles(surface)

    def _render_normal_circles(self, surface: pygame.Surface):
        """Rendu normal de sécurité"""
        for circle in self.circles:
            self._draw_viral_circle(surface, circle, 1.0)

    def _draw_viral_circle_explosion(self, surface: pygame.Surface, circle: Dict, 
                                   radius: float, thickness: float, center: Tuple[int, int]):
        """Dessine un cercle avec effet explosion SÉCURISÉ"""
        try:
            # Validation des paramètres
            radius = max(10, min(int(radius), 800))
            thickness = max(1, min(int(thickness), 40))
            center = (max(0, min(center[0], self.width)), max(0, min(center[1], self.height)))
            
            color = circle['current_color']
            
            # Gap calculation sécurisée
            gap_start_rad = math.radians(circle['current_gap_start'] + circle['current_rotation'])
            gap_angle_rad = math.radians(circle['gap_angle'])
            
            # Dessiner arc principal (méthode sécurisée)
            rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
            
            try:
                # Arc principal avec glow
                start_angle = gap_start_rad + gap_angle_rad
                end_angle = gap_start_rad + 2 * math.pi
                
                # Glow effect
                glow_color = tuple(min(255, c + 30) for c in color[:3])
                pygame.draw.arc(surface, glow_color, rect, start_angle, end_angle, thickness + 4)
                
                # Arc principal
                pygame.draw.arc(surface, color, rect, start_angle, end_angle, thickness)
                
            except Exception:
                # Fallback: cercle complet
                pygame.draw.circle(surface, color, center, radius, thickness)
                
        except Exception as e:
            logger.debug(f"Erreur dessin cercle explosion: {e}")

    def _spawn_explosion_particles_safe(self, count: int):
        """Particules d'explosion SÉCURISÉES"""
        try:
            # Limite le nombre total de particules
            if len(self.particles) >= self.viral_elements['max_particles']:
                # Supprimer les plus anciennes
                self.particles = self.particles[-30:]  # Garder seulement les 30 plus récentes
            
            for _ in range(min(count, 5)):  # Maximum 5 particules à la fois
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(3, 8)  # Vitesse réduite
                particle = {
                    'x': self.center_x,
                    'y': self.center_y,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'color': random.choice(self.colors),
                    'life': random.randint(30, 60),  # Vie réduite
                    'size': random.randint(2, 6)     # Taille réduite
                }
                self.particles.append(particle)
        except Exception as e:
            logger.debug(f"Erreur spawn particules: {e}")

    def _apply_viral_effects_safe(self, surface: pygame.Surface, phase: str, frame: int):
        """Effets post-processing viraux SÉCURISÉS"""
        try:
            # Mettre à jour et dessiner particules de manière sécurisée
            self._update_and_draw_particles_safe(surface)
            
            # Effets selon la phase CONTRÔLÉS
            if phase == "climax":
                # Flash effect CONTRÔLÉ
                if frame % 20 < 3:  # Moins fréquent: 20 au lieu de 10
                    flash_surface = pygame.Surface((self.width, self.height))
                    flash_surface.fill((255, 255, 255))
                    flash_surface.set_alpha(30)  # Moins intense: 30 au lieu de 50
                    surface.blit(flash_surface, (0, 0))
        except Exception as e:
            logger.debug(f"Erreur effets viraux: {e}")

    def _update_and_draw_particles_safe(self, surface: pygame.Surface):
        """Met à jour et dessine les particules SÉCURISÉES"""
        try:
            particles_to_remove = []
            
            for i, particle in enumerate(self.particles):
                # Mise à jour position avec bounds checking
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['life'] -= 1
                
                # Suppression si mort ou hors écran
                if (particle['life'] <= 0 or 
                    particle['x'] < -50 or particle['x'] > self.width + 50 or
                    particle['y'] < -50 or particle['y'] > self.height + 50):
                    particles_to_remove.append(i)
                    continue
                
                # Dessiner de manière sécurisée
                try:
                    x, y = int(particle['x']), int(particle['y'])
                    if 0 <= x < self.width and 0 <= y < self.height:
                        pygame.draw.circle(surface, particle['color'], (x, y), particle['size'])
                except Exception:
                    particles_to_remove.append(i)
            
            # Supprimer les particules en une fois (en sens inverse pour éviter les décalages d'index)
            for i in reversed(particles_to_remove):
                if 0 <= i < len(self.particles):
                    del self.particles[i]
                    
        except Exception as e:
            logger.debug(f"Erreur particules: {e}")
            # En cas d'erreur, vider toutes les particules
            self.particles.clear()

    # ========== MÉTHODES INCHANGÉES ==========
    # Les méthodes suivantes restent identiques car elles fonctionnent correctement
    
    def _render_hook_phase(self, surface: pygame.Surface, frame: int):
        """Phase HOOK: 3 premières secondes cruciales (inchangée)"""
        if self.hook_style == "COUNTDOWN":
            self._render_countdown_hook(surface, frame)
        elif self.hook_style == "CHALLENGE":
            self._render_challenge_hook(surface, frame)
        elif self.hook_style == "QUESTION":
            self._render_question_hook(surface, frame)
        else:  # SATISFYING
            self._render_satisfying_hook(surface, frame)
        
        # Cercles avec effet d'apparition
        for i, circle in enumerate(self.circles):
            # Apparition progressive
            appear_delay = i * 3  # frames
            if frame >= appear_delay:
                alpha_factor = min(1.0, (frame - appear_delay) / 30.0)
                self._draw_viral_circle(surface, circle, alpha_factor)

    def _render_countdown_hook(self, surface: pygame.Surface, frame: int):
        """Hook countdown viral (inchangé)"""
        remaining = 3 - int(frame / self.fps)
        if remaining > 0:
            # Texte countdown énorme
            font_size = 200 + int(abs(math.sin(frame * 0.3)) * 50)
            self._draw_viral_text(surface, str(remaining), font_size, (255, 255, 255), 
                                 (self.center_x, self.center_y - 200))
            
            # Sous-texte
            self._draw_viral_text(surface, "Can you follow them all?", 80, (255, 255, 0),
                                 (self.center_x, self.center_y + 200))

    def _render_challenge_hook(self, surface: pygame.Surface, frame: int):
        """Hook défi viral (inchangé)"""
        self._draw_viral_text(surface, "CHALLENGE:", 120, (255, 100, 100),
                             (self.center_x, self.center_y - 300))
        self._draw_viral_text(surface, "Follow the RED circle!", 100, (255, 255, 255),
                             (self.center_x, self.center_y - 150))
        self._draw_viral_text(surface, "WITHOUT BLINKING! 👁️", 80, (255, 255, 0),
                             (self.center_x, self.center_y + 200))

    def _render_question_hook(self, surface: pygame.Surface, frame: int):
        """Hook question viral (inchangé)"""
        questions = [
            "Which circle will escape first?",
            "Can you count them all?",
            "Which color hypnotizes you most?"
        ]
        question = questions[frame // 60 % len(questions)]
        self._draw_viral_text(surface, question, 90, (255, 255, 255),
                             (self.center_x, self.center_y - 200))

    def _render_satisfying_hook(self, surface: pygame.Surface, frame: int):
        """Hook satisfying viral (inchangé)"""
        self._draw_viral_text(surface, "This is so satisfying...", 100, (100, 255, 100),
                             (self.center_x, self.center_y - 200))
        self._draw_viral_text(surface, "Watch until the end! 😌", 80, (255, 255, 255),
                             (self.center_x, self.center_y + 200))

    def _render_build_phase(self, surface: pygame.Surface, frame: int):
        """Phase BUILD: Montée en puissance (inchangée)"""
        # Tous les cercles avec intensité croissante
        for circle in self.circles:
            self._draw_viral_circle(surface, circle, 1.0)
        
        # Début des particules
        if frame % 10 == 0:
            self._spawn_viral_particles(3)

    def _render_hypnotic_phase(self, surface: pygame.Surface, frame: int):
        """Phase HYPNOTIQUE: Maximum d'engagement (inchangée)"""
        # Mode rainbow activé
        self.viral_elements['rainbow_mode'] = True
        
        # Cercles avec effet glow
        for circle in self.circles:
            self._draw_viral_circle_with_glow(surface, circle)
        
        # Plus de particules
        if frame % 5 == 0:
            self._spawn_viral_particles(5)

    def _render_convergence_climax_safe(self, surface: pygame.Surface, frame: int):
        """Climax convergence sécurisé"""
        for circle in self.circles:
            self._draw_viral_circle_with_glow(surface, circle)

    def _render_spiral_climax_safe(self, surface: pygame.Surface, frame: int):
        """Climax spiral sécurisé"""
        for circle in self.circles:
            self._draw_viral_circle(surface, circle, 1.0)

    def _render_outro_phase(self, surface: pygame.Surface, frame: int):
        """Phase OUTRO: CTA + hook final (inchangée)"""
        # Cercles qui ralentissent
        for circle in self.circles:
            circle['rotation_speed'] *= 0.98
            self._draw_viral_circle(surface, circle, 0.8)
        
        # CTA text
        self._draw_viral_text(surface, "FOLLOW FOR MORE! 👆", 120, (255, 255, 0),
                             (self.center_x, self.center_y + 400))

    def _draw_viral_circle(self, surface: pygame.Surface, circle: Dict, alpha_factor: float = 1.0):
        """Dessine un cercle viral optimisé (inchangé)"""
        center = (self.center_x, self.center_y)
        radius = int(circle['radius'])
        thickness = int(circle['current_thickness'])
        color = circle['current_color']
        
        # Ajuster alpha
        if alpha_factor < 1.0:
            alpha = int(circle['alpha'] * alpha_factor)
            color = tuple(list(color) + [alpha]) if len(color) == 3 else color
        
        # Gap calculation
        gap_start_rad = math.radians(circle['current_gap_start'] + circle['current_rotation'])
        gap_angle_rad = math.radians(circle['gap_angle'])
        
        # Dessiner arc principal (méthode rapide)
        rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
        
        try:
            # Arc principal
            start_angle = gap_start_rad + gap_angle_rad
            end_angle = gap_start_rad + 2 * math.pi
            pygame.draw.arc(surface, color, rect, start_angle, end_angle, thickness)
        except:
            # Fallback: cercle complet
            pygame.draw.circle(surface, color, center, radius, thickness)

    def _draw_viral_circle_with_glow(self, surface: pygame.Surface, circle: Dict):
        """Cercle avec effet glow viral (inchangé)"""
        # Glow (cercle plus large, plus transparent)
        glow_color = tuple(min(255, c + 50) for c in circle['current_color'][:3])
        glow_circle = circle.copy()
        glow_circle['radius'] += 15
        glow_circle['current_thickness'] += 5
        glow_circle['current_color'] = glow_color
        glow_circle['alpha'] = 100
        
        self._draw_viral_circle(surface, glow_circle, 0.4)
        
        # Cercle principal
        self._draw_viral_circle(surface, circle, 1.0)

    def _draw_viral_text(self, surface: pygame.Surface, text: str, size: int, 
                        color: Tuple[int, int, int], pos: Tuple[int, int]):
        """Texte viral avec outline (inchangé)"""
        try:
            font = pygame.font.Font(None, size)
            
            # Outline noir
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                outline = font.render(text, True, (0, 0, 0))
                outline_rect = outline.get_rect(center=(pos[0] + dx, pos[1] + dy))
                surface.blit(outline, outline_rect)
            
            # Texte principal
            text_surface = font.render(text, True, color)
            text_rect = text_surface.get_rect(center=pos)
            surface.blit(text_surface, text_rect)
            
        except:
            pass  # Ignore font errors

    def _spawn_viral_particles(self, count: int):
        """Spawn particules virales (inchangé)"""
        for _ in range(count):
            particle = {
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'vx': random.uniform(-5, 5),
                'vy': random.uniform(-5, 5),
                'color': random.choice(self.colors),
                'life': 60,
                'size': random.randint(2, 8)
            }
            self.particles.append(particle)

    def _trigger_audio_events(self, phase: str, frame: int):
        """Déclenchement d'événements audio synchronisés (inchangé)"""
        current_time = frame / self.fps
        
        # Événements selon la phase
        if phase == "hook" and frame % 60 == 0:
            self.add_audio_event("countdown_beep", params={"volume": 0.8, "pitch": 1.2})
        
        elif phase == "build" and frame % 30 == 0:
            self.add_audio_event("build_pulse", params={"volume": 0.6, "intensity": 1.5})
        
        elif phase == "hypnotic" and frame % 20 == 0:
            self.add_audio_event("hypnotic_tone", params={"volume": 0.7, "frequency": 440})
        
        elif phase == "climax":
            if frame % 10 == 0:
                self.add_audio_event("climax_hit", params={"volume": 1.0, "impact": 2.0})
            if frame % 5 == 0:
                self.add_audio_event("explosion_particle", params={"volume": 0.4})
        
        elif phase == "outro" and frame % 120 == 0:
            self.add_audio_event("outro_chord", params={"volume": 0.8})


def main():
    """🔥 TEST DU GÉNÉRATEUR VIRAL CORRIGÉ 🔥"""
    print("🔥 VIRAL TIKTOK GENERATOR - VERSION CORRIGÉE 🔥")
    print("=" * 60)
    
    generator = ViralTikTokGeneratorFixed(width=1080, height=1920, fps=60, duration=10)
    
    try:
        # Configuration viral ultimate
        viral_config = {
            "viral_mode": "ULTIMATE",
            "hook_style": "COUNTDOWN",
            "climax_mode": "EXPLOSION",
            "color_palette": "neon_explosion",
            "duration": 10
        }
        
        generator.configure(viral_config)
        
        print(f"🎯 Mode: {viral_config['viral_mode']}")
        print(f"🎪 Hook: {viral_config['hook_style']}")
        print(f"💥 Climax: {viral_config['climax_mode']} (CORRIGÉ)")
        print(f"🎨 Palette: {viral_config['color_palette']}")
        
        # Génération
        print("\n🚀 Génération en cours (version stable)...")
        generator.set_output_path("output/viral_tiktok_fixed.mp4")
        
        start_time = time.time()
        result = generator.generate()
        gen_time = time.time() - start_time
        
        if result:
            print(f"\n🎉 VIDÉO VIRALE GÉNÉRÉE SANS BUGS!")
            print(f"📱 Fichier: {result}")
            print(f"⚡ Temps: {gen_time:.1f}s")
            print(f"\n✅ CORRECTIONS APPORTÉES:")
            print(f"   🛡️ Explosion sécurisée (pas de corruption des cercles)")
            print(f"   🎯 Particules limitées (max 50)")
            print(f"   🔒 Screen shake contrôlé")
            print(f"   ⚡ Gestion d'erreurs renforcée")
            print(f"   💾 Sauvegarde des propriétés originales")
            
        else:
            print("❌ Échec de génération")
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêté")
    finally:
        generator.cleanup()


if __name__ == "__main__":
    main()