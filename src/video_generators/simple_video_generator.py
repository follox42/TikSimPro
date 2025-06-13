#!/usr/bin/env python3
"""
Simple TikTok Circle Generator - Version fonctionnelle et simple
Génère des vidéos de cercles colorés comme dans vos exemples TikTok
"""

import pygame
import math
import random
import time
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger("TikSimPro")

from src.video_generators.base_video_generator import IVideoGenerator
from src.core.data_pipeline import TrendData, AudioEvent

class SimpleTikTokCircleGenerator(IVideoGenerator):
    """Générateur simple de vidéos TikTok avec des cercles animés"""
    
    def __init__(self, width=1080, height=1920, fps=60, duration=30):
        super().__init__(width, height, fps, duration)
        
        # Couleurs TikTok populaires (défaut)
        self.colors = [
            (255, 0, 80),    # Rose TikTok
            (0, 242, 234),   # Turquoise TikTok
            (255, 255, 255), # Blanc
            (254, 44, 85),   # Rose vif
            (37, 244, 238),  # Bleu TikTok
            (255, 215, 0),   # Or
            (255, 105, 180), # Rose chaud
            (0, 255, 127),   # Vert printemps
            (138, 43, 226),  # Violet
            (255, 69, 0),    # Rouge-orange
        ]
        
        # État de la simulation
        self.circles = []
        self.center_x = width // 2
        self.center_y = height // 2
        
        # Configuration
        self.num_circles = 15
        self.show_countdown = True
        
        logger.info(f"Générateur initialisé: {width}x{height} @ {fps}fps, {duration}s")

    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure le générateur avec des paramètres spécifiques"""
        try:
            # Mise à jour des paramètres de base
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
            
            # Paramètres spécifiques du générateur de cercles
            if "num_circles" in config:
                self.num_circles = config["num_circles"]
            if "show_countdown" in config:
                self.show_countdown = config["show_countdown"]
            if "colors" in config:
                # Convertir les couleurs hex en RGB si nécessaire
                custom_colors = []
                for color in config["colors"]:
                    if isinstance(color, str) and color.startswith("#"):
                        # Conversion hex vers RGB
                        hex_color = color.lstrip("#")
                        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                        custom_colors.append(rgb)
                    elif isinstance(color, (list, tuple)) and len(color) == 3:
                        custom_colors.append(tuple(color))
                if custom_colors:
                    self.colors = custom_colors
            
            logger.info(f"Générateur configuré: {self.num_circles} cercles, couleurs: {len(self.colors)}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur de configuration: {e}")
            return False

    def apply_trend_data(self, trend_data: TrendData) -> None:
        """Applique les données de tendance au générateur"""
        try:
            if not trend_data:
                logger.warning("Aucune donnée de tendance fournie")
                return
            
            # Appliquer les couleurs tendance
            trend_colors = trend_data.get_recommended_colors()
            if trend_colors:
                converted_colors = []
                for color_hex in trend_colors:
                    try:
                        # Conversion hex vers RGB
                        hex_color = color_hex.lstrip("#")
                        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                        converted_colors.append(rgb)
                    except:
                        continue
                
                if converted_colors:
                    self.colors = converted_colors
                    logger.info(f"Couleurs tendance appliquées: {len(converted_colors)} couleurs")
            
            # Appliquer les paramètres recommandés
            if hasattr(trend_data, 'recommended_settings') and trend_data.recommended_settings:
                video_settings = trend_data.recommended_settings.get('video_generator', {})
                if video_settings:
                    if 'num_circles' in video_settings:
                        self.num_circles = video_settings['num_circles']
                    if 'animation_speed' in video_settings:
                        self.animation_speed_multiplier = video_settings['animation_speed']
                    logger.info(f"Paramètres recommandés appliqués: {video_settings}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application des tendances: {e}")

    def initialize_simulation(self) -> bool:
        """Initialise les objets et l'état de la simulation"""
        try:
            self.create_circles()
            logger.info(f"Simulation initialisée avec {len(self.circles)} cercles")
            return True
        except Exception as e:
            logger.error(f"Erreur d'initialisation de la simulation: {e}")
            return False

    def create_circles(self):
        """Crée les cercles animés"""
        self.circles = []
        
        for i in range(self.num_circles):
            circle = {
                'radius': 50 + i * 40,  # Rayons croissants
                'thickness': random.randint(8, 25),
                'rotation_speed': random.uniform(-2, 2),  # Vitesse de rotation
                'rotation': random.uniform(0, 360),
                'gap_angle': random.randint(60, 120),  # Taille du trou
                'gap_start': random.uniform(0, 360),
                'color': random.choice(self.colors),
                'pulse_speed': random.uniform(0.02, 0.05),
                'pulse_phase': random.uniform(0, math.pi * 2)
            }
            self.circles.append(circle)
        
        logger.debug(f"✨ {len(self.circles)} cercles créés")

    def render_frame(self, surface: pygame.Surface, frame_number: int, dt: float) -> bool:
        """Rend une frame de la vidéo"""
        try:
            # Fond noir/sombre
            surface.fill((15, 15, 25))
            
            # Mettre à jour la simulation
            self.update_simulation(frame_number)
            
            # Dessiner tous les cercles (du plus grand au plus petit)
            for circle in reversed(self.circles):
                # Couleur avec variation basée sur le temps
                time_factor = frame_number / self.fps
                color_variation = math.sin(time_factor * 0.5 + circle['pulse_phase']) * 0.3
                adjusted_color = []
                for c in circle['color']:
                    new_c = int(c * (1 + color_variation))
                    adjusted_color.append(max(0, min(255, new_c)))
                
                self.draw_circle_with_gap(
                    surface,
                    (self.center_x, self.center_y),
                    circle['radius'],
                    circle['current_thickness'],
                    circle['gap_start'] + circle['rotation'],
                    circle['gap_angle'],
                    tuple(adjusted_color)
                )
            
            # Ajouter un texte central avec compte à rebours style TikTok
            if self.show_countdown:
                remaining_frames = self.total_frames - frame_number
                remaining_seconds = remaining_frames // self.fps
                
                if remaining_seconds > 0:
                    font = pygame.font.Font(None, 120)
                    text = font.render(str(remaining_seconds), True, (255, 255, 255))
                    text_rect = text.get_rect(center=(self.center_x, self.center_y))
                    
                    # Ombre pour le texte
                    shadow = font.render(str(remaining_seconds), True, (0, 0, 0))
                    shadow_rect = shadow.get_rect(center=(self.center_x + 3, self.center_y + 3))
                    surface.blit(shadow, shadow_rect)
                    surface.blit(text, text_rect)
            
            # Ajouter des événements audio si approprié
            if frame_number % (self.fps // 2) == 0:  # Toutes les 0.5 secondes
                self.add_audio_event("circle_pulse", (self.center_x, self.center_y), 
                                   {"intensity": 0.5})
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur de rendu frame {frame_number}: {e}")
            return False

    def update_simulation(self, frame_number: int):
        """Met à jour la simulation pour la frame actuelle"""
        time_factor = frame_number / self.fps
        
        for circle in self.circles:
            # Rotation continue
            circle['rotation'] += circle['rotation_speed']
            if circle['rotation'] > 360:
                circle['rotation'] -= 360
            elif circle['rotation'] < 0:
                circle['rotation'] += 360
            
            # Effet de pulsation sur l'épaisseur
            pulse = math.sin(time_factor * circle['pulse_speed'] * 10 + circle['pulse_phase'])
            circle['current_thickness'] = circle['thickness'] + pulse * 3
            
            # Mouvement du gap
            circle['gap_start'] = (circle['gap_start'] + circle['rotation_speed'] * 2) % 360

    def draw_circle_with_gap(self, surface: pygame.Surface, center: Tuple[int, int], 
                           radius: float, thickness: float, gap_start: float, 
                           gap_angle: float, color: Tuple[int, int, int]):
        """Dessine un cercle avec un trou (gap)"""
        # Convertir les angles en radians
        gap_start_rad = math.radians(gap_start)
        gap_end_rad = math.radians(gap_start + gap_angle)
        
        # Nombre de segments pour dessiner l'arc
        segments = max(20, int(radius / 3))
        angle_per_segment = (2 * math.pi) / segments
        
        points_outer = []
        points_inner = []
        
        for i in range(segments):
            angle = i * angle_per_segment
            
            # Vérifier si on est dans le gap
            if gap_start_rad <= gap_end_rad:
                in_gap = gap_start_rad <= angle <= gap_end_rad
            else:  # Le gap traverse 0°
                in_gap = angle >= gap_start_rad or angle <= gap_end_rad
            
            if not in_gap:
                # Points du cercle extérieur
                x_outer = center[0] + (radius + thickness/2) * math.cos(angle)
                y_outer = center[1] + (radius + thickness/2) * math.sin(angle)
                points_outer.append((x_outer, y_outer))
                
                # Points du cercle intérieur
                x_inner = center[0] + (radius - thickness/2) * math.cos(angle)
                y_inner = center[1] + (radius - thickness/2) * math.sin(angle)
                points_inner.append((x_inner, y_inner))
        
        # Dessiner l'anneau si on a des points
        if len(points_outer) >= 3:
            # Combiner les points pour former un polygone fermé
            all_points = points_outer + points_inner[::-1]  # Inverser l'ordre des points intérieurs
            pygame.draw.polygon(surface, color, all_points)
            
            # Ajouter un contour lisse
            if len(points_outer) >= 2:
                pygame.draw.lines(surface, color, False, points_outer, 2)
            if len(points_inner) >= 2:
                pygame.draw.lines(surface, color, False, points_inner, 2)


def main():
    """Fonction principale - exemple d'utilisation"""
    print("🎨 TikTok Circle Generator - Version Simple")
    print("=" * 50)
    
    # Créer le générateur
    generator = SimpleTikTokCircleGenerator(
        width=1080,
        height=1920,
        fps=60,
        duration=15  # Vidéo de 15 secondes
    )
    
    try:
        # Configuration
        generator.set_output_path("output/tiktok_circles_simple.mp4")
        
        # Générer la vidéo
        result_path = generator.generate()
        
        if result_path:
            print("\n🎉 Succès! Votre vidéo TikTok est prête!")
            print(f"📱 Fichier généré: {result_path}")
            print("📱 Parfait pour TikTok/Instagram/YouTube Shorts")
            print("\n💡 Conseils pour TikTok:")
            print("   - Ajoutez du son tendance")
            print("   - Utilisez des hashtags: #fyp #satisfying #hypnotic")
            print("   - Postez aux heures de pointe")
        else:
            print("\n❌ Échec de la génération")
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
    
    finally:
        generator.cleanup()


if __name__ == "__main__":
    main()