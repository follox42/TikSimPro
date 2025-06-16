#!/usr/bin/env python3
"""
ULTRA FAST TikTok Circle Generator - Optimisé pour vitesse maximale
Peut générer des vidéos à 30+ FPS au lieu de 4.8 FPS
"""

import pygame
import math
import random
import time
import logging
import numpy as np
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger("TikSimPro")

from src.video_generators.base_video_generator import IVideoGenerator
from src.core.data_pipeline import TrendData, AudioEvent

class SimpleTikTokCircleGenerator(IVideoGenerator):
    """Générateur ULTRA-RAPIDE de vidéos TikTok avec des cercles satisfaisants"""
    
    def __init__(self, width=1080, height=1920, fps=60, duration=30):
        super().__init__(width, height, fps, duration)
        
        # ACTIVER MODE PERFORMANCE AVEC AFFICHAGE
        self.set_performance_mode(
            headless=False,   # Affichage activé comme demandé
            fast=True,        # Pas de limitation FPS artificielle
            use_numpy=True    # Conversion ultra-rapide
        )
        
        # Palettes de couleurs optimisées
        self.color_palettes = {
            "neon": [
                (255, 0, 80),    # Rose néon
                (0, 242, 234),   # Turquoise néon  
                (255, 255, 255), # Blanc pur
                (254, 44, 85),   # Rose vif
                (37, 244, 238),  # Cyan électrique
            ],
            "sunset": [
                (255, 94, 77),   # Corail
                (255, 154, 0),   # Orange
                (255, 206, 84),  # Jaune doré
                (237, 117, 88),  # Rose saumon
                (240, 147, 43),  # Orange vif
            ],
            "cosmic": [
                (138, 43, 226),  # Violet
                (255, 20, 147),  # Rose profond
                (0, 255, 255),   # Cyan
                (255, 0, 255),   # Magenta
                (148, 0, 211),   # Violet foncé
            ]
        }
        
        self.current_palette = "neon"
        self.colors = self.color_palettes[self.current_palette]
        
        # État de la simulation
        self.circles = []
        self.center_x = width // 2
        self.center_y = height // 2
        
        # Configuration optimisée pour vitesse
        self.num_circles = 8  # RÉDUIT pour performance (8 au lieu de 15)
        self.show_countdown = False
        
        # Optimisations de rendu
        self.use_fast_circles = True    # Utiliser pygame.draw.circle au lieu de polygones
        self.reduce_segments = True     # Moins de segments pour les arcs
        self.cache_colors = True        # Cache des couleurs pré-calculées
        self.simple_effects = True      # Effets simplifiés
        
        # Cache des couleurs pré-calculées pour performance
        self.color_cache = {}
        self.precompute_colors()
        
        logger.info(f"ULTRA-FAST générateur initialisé: {width}x{height} @ {fps}fps, {duration}s")
        logger.info(f"Mode performance: {self.num_circles} cercles, fast_circles={self.use_fast_circles}")

    def precompute_colors(self):
        """Pré-calcule toutes les variations de couleurs pour éviter les calculs en temps réel"""
        logger.debug("Pré-calcul des couleurs pour performance...")
        
        for color in self.colors:
            color_key = str(color)
            self.color_cache[color_key] = {
                'base': color,
                'bright': tuple(min(255, int(c * 1.3)) for c in color),
                'dim': tuple(max(0, int(c * 0.7)) for c in color),
                'variations': []
            }
            
            # Pré-calculer 20 variations de couleur
            for i in range(20):
                factor = 0.7 + (i / 20) * 0.6  # De 0.7 à 1.3
                variation = tuple(max(0, min(255, int(c * factor))) for c in color)
                self.color_cache[color_key]['variations'].append(variation)

    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure le générateur avec optimisations de performance"""
        try:
            # Paramètres de base
            if "width" in config:
                self.width = config["width"]
                self.center_x = self.width // 2
            if "height" in config:
                self.height = config["height"]
                self.center_y = self.height // 2
            if "fps" in config:
                self.fps = config["fps"]
            if "duration" in config:
                self.duration = config["duration"]
                self.total_frames = int(self.fps * self.duration)
            
            # Paramètres de performance
            if "num_circles" in config:
                self.num_circles = min(config["num_circles"], 12)  # Max 12 pour performance
            if "use_fast_circles" in config:
                self.use_fast_circles = config["use_fast_circles"]
            
            # Couleurs
            if "color_palette" in config:
                palette = config["color_palette"]
                if isinstance(palette, str) and palette in self.color_palettes:
                    self.current_palette = palette
                    self.colors = self.color_palettes[palette]
                    self.precompute_colors()  # Recalculer le cache
                elif isinstance(palette, list):
                    self.colors = self._convert_hex_colors(palette)
                    self.precompute_colors()  # Recalculer le cache
            
            logger.info(f"Générateur ULTRA-FAST configuré: {self.num_circles} cercles, palette: {self.current_palette}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur de configuration: {e}")
            return False

    def _convert_hex_colors(self, hex_colors: List[str]) -> List[Tuple[int, int, int]]:
        """Convertit les couleurs hex en RGB"""
        rgb_colors = []
        for color in hex_colors:
            try:
                if isinstance(color, str) and color.startswith("#"):
                    hex_color = color.lstrip("#")
                    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    rgb_colors.append(rgb)
            except:
                continue
        return rgb_colors if rgb_colors else self.colors

    def apply_trend_data(self, trend_data: TrendData) -> None:
        """Applique les données de tendance avec optimisations"""
        try:
            if not trend_data:
                logger.warning("Aucune donnée de tendance fournie")
                return
            
            # Appliquer les couleurs tendance
            trend_colors = trend_data.get_recommended_colors()
            if trend_colors:
                converted_colors = self._convert_hex_colors(trend_colors)
                if converted_colors:
                    self.colors = converted_colors
                    self.precompute_colors()  # Recalculer le cache pour les nouvelles couleurs
                    logger.info(f"Couleurs tendance appliquées: {len(converted_colors)} couleurs")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application des tendances: {e}")

    def initialize_simulation(self) -> bool:
        """Initialise les cercles avec des paramètres optimisés pour la vitesse"""
        try:
            self.create_fast_circles()
            logger.info(f"Simulation ULTRA-FAST initialisée avec {len(self.circles)} cercles")
            return True
        except Exception as e:
            logger.error(f"Erreur d'initialisation de la simulation: {e}")
            return False

    def create_fast_circles(self):
        """Crée des cercles optimisés pour vitesse maximale"""
        self.circles = []
        
        # Paramètres optimisés pour performance
        base_radius = min(self.width, self.height) // 10
        radius_increment = base_radius * 0.9
        
        for i in range(self.num_circles):
            # Vitesses simples pour calculs rapides
            speed = (i + 1) * 0.5  # Vitesses croissantes simples
            
            circle = {
                'radius': base_radius + (i * radius_increment * 0.7),
                'thickness': 10 + (i * 3),  # Épaisseur simple
                'rotation_speed': speed,
                'rotation': random.uniform(0, 360),
                'gap_angle': 60 + (i * 10),  # Gaps simples
                'gap_start': i * (360 / self.num_circles),
                'color_index': i % len(self.colors),
                'base_color': self.colors[i % len(self.colors)],
                'pulse_phase': i * 0.5,  # Phase simple
                
                # Optimisations pré-calculées
                'cos_cache': {},  # Cache des cosinus
                'sin_cache': {},  # Cache des sinus
            }
            self.circles.append(circle)
        
        logger.debug(f"{len(self.circles)} cercles ULTRA-FAST créés")

    def render_frame(self, surface: pygame.Surface, frame_number: int, dt: float) -> bool:
        """Rendu ULTRA-RAPIDE d'une frame"""
        try:
            # Fond simple et rapide
            surface.fill((15, 15, 25))
            
            # Mettre à jour la simulation rapidement
            self.update_fast_simulation(frame_number)
            
            # Dessiner les cercles avec méthode optimisée
            if self.use_fast_circles:
                self._draw_fast_circles(surface)
            else:
                self._draw_polygon_circles(surface)
            
            # Génération d'événements audio simplifiée
            if frame_number % (self.fps * 2) == 0:  # Moins d'événements audio
                self.add_audio_event("circle_pulse", (self.center_x, self.center_y), 
                                   {"intensity": 0.5})
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur de rendu frame {frame_number}: {e}")
            return False

    def update_fast_simulation(self, frame_number: int):
        """Mise à jour ULTRA-RAPIDE de la simulation"""
        time_factor = frame_number * 0.01  # Calcul simplifié
        
        for circle in self.circles:
            # Rotation simple et rapide
            circle['rotation'] = (circle['rotation'] + circle['rotation_speed']) % 360
            
            # Gap movement simple
            circle['gap_start'] = (circle['gap_start'] + circle['rotation_speed'] * 0.2) % 360
            
            # Variation de couleur basée sur le cache pré-calculé
            color_key = str(circle['base_color'])
            if color_key in self.color_cache:
                variation_index = int((frame_number + circle['pulse_phase']) * 0.1) % 20
                circle['current_color'] = self.color_cache[color_key]['variations'][variation_index]
            else:
                circle['current_color'] = circle['base_color']

    def _draw_fast_circles(self, surface: pygame.Surface):
        """Dessine les cercles avec pygame.draw.circle (TRÈS RAPIDE)"""
        for circle in self.circles:
            color = circle['current_color']
            center = (self.center_x, self.center_y)
            radius = int(circle['radius'])
            thickness = int(circle['thickness'])
            
            # Calculer les angles de gap
            gap_start = math.radians(circle['gap_start'] + circle['rotation'])
            gap_end = math.radians(circle['gap_start'] + circle['rotation'] + circle['gap_angle'])
            
            # Dessiner plusieurs arcs pour simuler le gap
            # (Plus simple que des polygones complexes)
            arc_count = 8  # Nombre d'arcs pour faire le tour
            arc_angle = (2 * math.pi) / arc_count
            
            for i in range(arc_count):
                start_angle = i * arc_angle
                end_angle = (i + 1) * arc_angle
                
                # Vérifier si cet arc est dans le gap
                in_gap = self._angle_in_gap_fast(start_angle, gap_start, gap_end)
                
                if not in_gap:
                    # Dessiner un arc avec pygame (RAPIDE)
                    rect = pygame.Rect(
                        center[0] - radius, center[1] - radius,
                        radius * 2, radius * 2
                    )
                    
                    try:
                        pygame.draw.arc(surface, color, rect, start_angle, end_angle, thickness)
                    except:
                        # Fallback si l'arc échoue
                        pygame.draw.circle(surface, color, center, radius, thickness)

    def _angle_in_gap_fast(self, angle: float, gap_start: float, gap_end: float) -> bool:
        """Version rapide de la détection de gap"""
        # Normaliser les angles
        angle = angle % (2 * math.pi)
        gap_start = gap_start % (2 * math.pi)
        gap_end = gap_end % (2 * math.pi)
        
        if gap_start <= gap_end:
            return gap_start <= angle <= gap_end
        else:
            return angle >= gap_start or angle <= gap_end

    def _draw_polygon_circles(self, surface: pygame.Surface):
        """Version fallback avec polygones (plus lente mais plus précise)"""
        for circle in self.circles:
            color = circle['current_color']
            center = (self.center_x, self.center_y)
            radius = circle['radius']
            thickness = circle['thickness']
            gap_start = circle['gap_start'] + circle['rotation']
            gap_angle = circle['gap_angle']
            
            # Version simplifiée de l'algorithme polygonal original
            self._draw_arc_with_gap_simple(surface, center, radius, thickness, gap_start, gap_angle, color)

    def _draw_arc_with_gap_simple(self, surface: pygame.Surface, center: Tuple[int, int], 
                                 radius: float, thickness: float, gap_start: float, 
                                 gap_angle: float, color: Tuple[int, int, int]):
        """Version simplifiée de l'arc avec gap pour performance"""
        # Moins de segments pour plus de vitesse
        segments = max(16, int(radius / 8))  # Beaucoup moins de segments
        angle_per_segment = (2 * math.pi) / segments
        
        gap_start_rad = math.radians(gap_start)
        gap_end_rad = math.radians(gap_start + gap_angle)
        
        points = []
        
        for i in range(segments):
            angle = i * angle_per_segment
            
            if not self._angle_in_gap_fast(angle, gap_start_rad, gap_end_rad):
                # Points simplifiés
                x = center[0] + radius * math.cos(angle)
                y = center[1] + radius * math.sin(angle)
                points.append((int(x), int(y)))
        
        # Dessiner avec des lignes simples si assez de points
        if len(points) >= 3:
            pygame.draw.lines(surface, color, False, points, int(thickness))

    def get_performance_info(self) -> Dict[str, Any]:
        """Retourne les informations de performance"""
        return {
            "num_circles": self.num_circles,
            "use_fast_circles": self.use_fast_circles,
            "reduce_segments": self.reduce_segments,
            "cache_colors": self.cache_colors,
            "current_palette": self.current_palette,
            "color_cache_size": len(self.color_cache)
        }


def main():
    """Test du générateur ultra-rapide"""
    print("Générateur de Cercles ULTRA-RAPIDE TikTok")
    print("=" * 50)
    
    # Configuration pour test de vitesse
    generator = SimpleTikTokCircleGenerator(
        width=1080,
        height=1920,
        fps=60,
        duration=10  # Test court pour vérifier la vitesse
    )
    
    try:
        # Configuration optimisée
        config = {
            "num_circles": 8,
            "use_fast_circles": True,
            "color_palette": "neon"
        }
        generator.configure(config)
        
        # Test de vitesse
        start_time = time.time()
        generator.set_output_path("output/ultra_fast_circles.mp4")
        result_path = generator.generate()
        end_time = time.time()
        
        if result_path:
            generation_time = end_time - start_time
            target_duration = generator.duration
            speed_ratio = target_duration / generation_time
            
            print(f"✅ Vidéo ULTRA-RAPIDE générée: {result_path}")
            print(f"⚡ Temps de génération: {generation_time:.1f}s pour {target_duration}s de vidéo")
            print(f"🚀 Ratio de vitesse: {speed_ratio:.1f}x (1.0x = temps réel)")
            
            # Afficher infos de performance
            perf_info = generator.get_performance_info()
            print(f"📊 Configuration: {perf_info}")
        else:
            print("❌ Échec de la génération")
    
    except KeyboardInterrupt:
        print("🛑 Arrêt demandé")
    
    finally:
        generator.cleanup()


if __name__ == "__main__":
    main()