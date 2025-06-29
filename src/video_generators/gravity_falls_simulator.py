# src/video_generators/gravity_falls_simulator.py
"""

"""

import pygame
import math
import random
import time
import colorsys
from typing import Dict, Any, Optional, Tuple
import logging
import os

from src.video_generators.base_video_generator import IVideoGenerator
from src.core.data_pipeline import TrendData, AudioEvent

logger = logging.getLogger("TikSimPro")

class Vector2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Velocity:
    def __init__(self, vx, vy):
        self.vx = vx
        self.vy = vy

class CleanBounce:
    """Balle avec physique triangulaire intéressante"""
    
    def __init__(self, pos: Vector2D, vel: Velocity, size: float = 15.0):
        
        self.pos = pos
        self.vel = vel
        self.size = size
        
        self.max_speed = 1800  # Vitesse max contrôlée
        self.max_size = 180

        # Couleur simple
        self.hue = random.uniform(0, 360)
        self.hue_speed = 120
        
        # === PHYSIQUE RAPIDE ET ÉNERGIQUE ===
        self.gravity = 2800  # Gravité plus forte pour vitesse
        self.restitution = 1.08  # Rebond énergique qui ajoute de l'énergie
        self.min_velocity = 600  # Vitesse minimale élevée pour éviter l'arrêt
        
        # Physique énergique
        self.air_resistance = 1.001  # Légèrement accélérateur
        self.max_bounces = 0
        self.energy_boost = 1.02  # Boost d'énergie à chaque frame
        
    def update(self, dt: float, container_center: Tuple[float, float], container_radius: float, hue):
        """Physique rapide et énergique - JAMAIS D'ARRÊT !"""
        
        # Gravité forte pour vitesse
        self.vel.vy += self.gravity * dt
        
        # Boost d'énergie constant pour éviter l'arrêt
        self.vel.vx *= self.air_resistance
        self.vel.vy *= self.air_resistance
        
        # Boost énergétique à chaque frame
        current_speed = math.sqrt(self.vel.vx*self.vel.vx + self.vel.vy*self.vel.vy)
        if current_speed > 0:
            boost_factor = self.energy_boost
            self.vel.vx *= boost_factor
            self.vel.vy *= boost_factor
        
        # Mouvement
        self.pos.x += self.vel.vx * dt
        self.pos.y += self.vel.vy * dt
        
        # Couleur
        self.hue = hue
        
        # ANTI-ARRÊT : Si vitesse trop faible, boost immédiat
        velocity_magnitude = math.sqrt(self.vel.vx * self.vel.vx + self.vel.vy * self.vel.vy)
        if velocity_magnitude < self.min_velocity:
            # Boost dans direction aléatoire si trop lent
            boost_angle = random.uniform(0, 2 * math.pi)
            boost_strength = self.min_velocity * 1.5
            self.vel.vx = math.cos(boost_angle) * boost_strength
            self.vel.vy = math.sin(boost_angle) * boost_strength
        
        # Collision avec le cercle
        center_x, center_y = container_center
        dx = self.pos.x - center_x
        dy = self.pos.y - center_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        wall_distance = container_radius - self.size
        if distance > wall_distance:
            if distance > 0:
                # Grossissement rapide
                if self.size < self.max_size:
                    self.size *= 1.08
                wall_distance = container_radius - self.size

                # Direction normale
                nx = dx / distance
                ny = dy / distance
                
                # Repositionnement
                self.pos.x = center_x + nx * wall_distance
                self.pos.y = center_y + ny * wall_distance
                
                # Réflexion ÉNERGIQUE
                dot = self.vel.vx * nx + self.vel.vy * ny
                
                # Nouvelles vitesses avec BOOST
                new_vx = (self.vel.vx - 2 * dot * nx) * self.restitution
                new_vy = (self.vel.vy - 2 * dot * ny) * self.restitution
                
                # Contrôle de vitesse énergique
                velocity_magnitude = math.sqrt(new_vx * new_vx + new_vy * new_vy)
                
                # Limite max plus élevée
                if velocity_magnitude > self.max_speed:
                    scale = self.max_speed / velocity_magnitude
                    new_vx *= scale
                    new_vy *= scale
                
                # GARANTIE de vitesse minimale élevée
                if velocity_magnitude < self.min_velocity:
                    scale = self.min_velocity * 1.2 / velocity_magnitude  # 20% de boost
                    new_vx *= scale
                    new_vy *= scale
                
                # Anti-mouvement répétitif avec boost plus fort
                if abs(new_vx) < 300:
                    new_vx += random.uniform(-600, 600)
                
                if abs(new_vy) < 300:
                    new_vy += random.uniform(-600, 600)
                
                # Boost aléatoire énergique à chaque rebond
                energy_boost = random.uniform(1.1, 1.3)
                new_vx *= energy_boost
                new_vy *= energy_boost
                
                self.vel.vx = new_vx
                self.vel.vy = new_vy
                self.max_bounces += 1
                
                return True
        
        return False
    
    def get_color(self) -> Tuple[int, int, int]:
        """Couleur actuelle"""
        r, g, b = colorsys.hsv_to_rgb(self.hue/360, 1.0, 1.0)
        return (int(r*255), int(g*255), int(b*255))
    
    def render(self, surface: pygame.Surface, border_only: bool = False):
        """Dessine la balle simple"""
        color = self.get_color()
        pos = (int(self.pos.x), int(self.pos.y))
        
        if border_only:
            # Previous ball juste draw border
            pygame.draw.circle(surface, (0, 0, 0), pos, int(self.size))
            pygame.draw.circle(surface, color, pos, int(self.size), width=1)
        else:
            # Classic ball
            pygame.draw.circle(surface, color, pos, int(self.size))

class GravityFallsSimulator(IVideoGenerator):
    """🎯 Simulateur propre avec historique des positions 🎯"""
    
    def __init__(self, width=1080, height=1920, fps=60, duration=30):
        super().__init__(width, height, fps, duration)
        
        # Mode performance
        self.set_performance_mode(headless=False, fast=True, use_numpy=True)
        
        # Container
        self.container_center = (width // 2, height // 2)
        self.container_radius = min(width, height) * 0.9 / 2
        
        # Balle
        self.ball = None

        # Couleur du container
        self.container_hue = 0.0
        
        # Stats
        self.bounce_count = 0
        self.time_elapsed = 0.0
        
    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure simple"""
        try:
            if "container_size" in config:
                size_factor = max(0.2, min(0.9, config["container_size"]))
                self.container_radius = min(self.width, self.height) * size_factor / 2
            
            logger.info("Clean Ball Simulator configuré")
            return True
            
        except Exception as e:
            logger.error(f"Erreur configuration: {e}")
            return False
    
    def apply_trend_data(self, trend_data: TrendData) -> None:
        """Pas de tendances complexes"""
        pass
    
    def initialize_simulation(self) -> bool:
        """Initialise avec physique simple et naturelle"""
        try:
            # Position de départ naturelle
            center_x, center_y = self.container_center
            
            # Position aléatoire dans le cercle
            start_x = center_x + random.uniform(-150, 150)
            start_y = center_y + random.uniform(-300, -100)  # Plus haut pour plus de vitesse
            
            # Vitesse initiale RAPIDE
            vx = random.uniform(-1000, 1000)  # Beaucoup plus rapide
            vy = random.uniform(-600, 200)   # Plus de variation
            
            self.ball = CleanBounce(pos=Vector2D(start_x, start_y), vel=Velocity(vx, vy), size=15)
            
            logger.info("Simulation simple initialisée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur initialisation: {e}")
            return False
    
    # overwrite to avoid cleaning screen in this case
    def generate(self) -> Optional[str]:
        """Generate the complete video with MAXIMUM PERFORMANCE"""
        try:
            logger.info("Starting HIGH PERFORMANCE video generation...")
            
            # Setup with performance optimizations
            if not self.setup_pygame(0.5):
                return None
            
            if not self.initialize_simulation():
                return None
            
            if not self.start_recording():
                return None
            
            # HIGH SPEED render loop
            dt = 1.0 / self.fps
            last_progress_time = time.time()
            
            while not self.is_finished():
                # Handle events ONLY if not headless
                if not self.handle_events():
                    break

                # Render frame
                if not self.render_frame(self.recording_surface, self.current_frame, dt):
                    logger.error(f"Frame rendering failed at frame {self.current_frame}")
                    break
                
                # Record frame
                self.record_frame(self.recording_surface)
                
                # Update display ONLY if not headless
                if not self.headless_mode:
                    self.update_display()
                
                # Frame rate control ONLY if not in fast mode
                if not self.fast_mode:
                    self.clock.tick(self.fps)
                
                # Progress logging (reduced frequency for performance)
                current_time = time.time()
                if current_time - last_progress_time >= 5.0:  # Every 5 seconds
                    progress = self.get_progress() * 100
                    self.update_performance_stats()
                    render_fps = self.performance_stats["average_fps"]
                    encoding_fps = self.performance_stats["encoding_fps"]
                    
                    logger.info(f"Progress: {progress:.1f}% ({self.current_frame}/{self.total_frames}) | "
                              f"Render: {render_fps:.1f} FPS | Encoding: {encoding_fps:.1f} FPS")
                    last_progress_time = current_time
            
            # Finalize
            logger.info("Finalizing video...")
            success = self.stop_recording()
            
            # Cleanup
            self.cleanup()
            
            # Check if video was actually created despite errors
            if os.path.exists(self.output_path):
                file_size = os.path.getsize(self.output_path) / (1024*1024)
                if file_size > 0.1:  # File has content
                    logger.info(f"Video generated successfully: {self.output_path} ({file_size:.1f} MB)")
                    return self.output_path
                else:
                    logger.error(f"Video file is empty: {self.output_path}")
            
            return None
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            self.cleanup()
            return None
        
    def render_frame(self, surface: pygame.Surface, frame_number: int, dt: float) -> bool:
        """Rendu avec historique des positions du bord"""
        try:
            self.time_elapsed += dt
            
            # Couleur actuelle du container
            self.container_hue += 90 * (1/60)  # Changement lent
            self.container_hue = self.container_hue % 360
            
            r, g, b = colorsys.hsv_to_rgb(self.container_hue/360, 0.9, 0.8)
            current_container_color = (int(r*255), int(g*255), int(b*255))

            # 1. dessiner la ball precedente
            if self.ball:
                self.ball.render(surface, True)

            # 2. Mettre à jour la balle
            if self.ball:
                collision = self.ball.update(dt, self.container_center, self.container_radius, self.container_hue)
                if collision:
                    self.bounce_count += 1
                    self.add_audio_event("collision", 
                                       position=(self.ball.pos.x, self.ball.pos.y),
                                       params={"volume": 0.5, "bounce_count": self.bounce_count})

            # 3. Dessiner le container actuel
            pygame.draw.circle(surface, current_container_color, self.container_center, int(self.container_radius), 10)
            
            # 4. Dessiner la balle
            if self.ball:
                self.ball.render(surface)
            
            # 5. UI simple
            self._render_ui(surface)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur rendu frame {frame_number}: {e}")
            return False
    
    def _render_ui(self, surface: pygame.Surface):
        """UI simple et propre"""
        try:
            # Compteur de rebonds
            font = pygame.font.Font(None, 64)
            text = str(self.bounce_count)
            
            # Outline
            text_outline = font.render(text, True, (0, 0, 0))
            text_rect = text_outline.get_rect(center=(self.width//2, 100))
            
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                surface.blit(text_outline, (text_rect.x + dx, text_rect.y + dy))
            
            # Texte principal
            text_main = font.render(text, True, (255, 255, 255))
            surface.blit(text_main, text_rect)
            
            # Texte viral simple
            if self.time_elapsed < 4:
                viral_font = pygame.font.Font(None, 40)
                viral_text = "BALL GETS BIGGER!"
                viral_surface = viral_font.render(viral_text, True, (255, 255, 0))
                viral_rect = viral_surface.get_rect(center=(self.width//2, 50))
                
                # Outline
                viral_outline = viral_font.render(viral_text, True, (0, 0, 0))
                for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    surface.blit(viral_outline, (viral_rect.x + dx, viral_rect.y + dy))
                
                surface.blit(viral_surface, viral_rect)
            
            # Alerte simple quand grosse
            if self.ball and self.ball.size > 80:
                warning_font = pygame.font.Font(None, 48)
                warning_text = "TOO BIG!"
                warning_surface = warning_font.render(warning_text, True, (255, 100, 100))
                warning_rect = warning_surface.get_rect(center=(self.width//2, self.height - 100))
                
                # Outline
                warning_outline = warning_font.render(warning_text, True, (0, 0, 0))
                for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                    surface.blit(warning_outline, (warning_rect.x + dx, warning_rect.y + dy))
                
                surface.blit(warning_surface, warning_rect)
            
        except Exception as e:
            logger.debug(f"Erreur UI: {e}")

def main():
    """Test du simulateur clean"""
    print("🎯 CLEAN BOUNCING BALL SIMULATOR 🎯")
    print("=" * 50)
    
    simulator = GravityFallsSimulator(width=800, height=800, fps=60, duration=20)
    
    try:
        config = {"container_size": 0.35}
        
        simulator.configure(config)
        simulator.set_output_path("clean_bouncing_ball.mp4")
        
        print("🚀 Génération clean en cours...")
        start_time = time.time()
        
        result = simulator.generate()
        
        gen_time = time.time() - start_time
        
        if result:
            print(f"✅ Simulation clean générée!")
            print(f"📱 Fichier: {result}")
            print(f"⚡ Temps: {gen_time:.1f}s")
            print(f"\n🎯 CARACTÉRISTIQUES CLEAN:")
            print(f"   ✨ Code propre et simple")
            print(f"   🎨 Historique des bords avec couleur actuelle")
            print(f"   🌍 Gravité réaliste")
            print(f"   ⚡ Rebonds élastiques logiques")
            print(f"   🔴 Cercle simple sans pulse")
            print(f"   ⚫ Balle simple sans effets")
            print(f"   📈 Grossit à chaque rebond")
            print(f"   🎯 Style viral TikTok clean")
            print(f"   🔄 Toutes les positions précédentes avec couleur actuelle")
        else:
            print("❌ Échec de génération")
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêté par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        simulator.cleanup()

if __name__ == "__main__":
    main()