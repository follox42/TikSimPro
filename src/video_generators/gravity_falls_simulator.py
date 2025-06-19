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
    """Balle propre et simple"""
    
    def __init__(self, pos: Vector2D, vel: Velocity, size: float = 15.0):
        
        self.pos = pos
        self.vel = vel
        self.size = size
        
        self.max_speed = 2000
        self.max_size = 200

        # Couleur simple
        self.hue = random.uniform(0, 360)
        self.hue_speed = 120  # Plus lent
        
        # Physique réaliste
        self.gravity = 1200  # Gravité vers le bas
        self.restitution = 1.03  # Rebond élastique
        
    def update(self, dt: float, container_center: Tuple[float, float], container_radius: float, hue):
        """Met à jour la balle avec gravité"""
        # Gravité
        self.vel.vy += self.gravity * dt
        
        # Mouvement
        self.pos.x += self.vel.vx * dt
        self.pos.y += self.vel.vy * dt
        
        # Changement de couleur lent
        self.hue = hue
        
        # Collision avec le cercle
        center_x, center_y = container_center
        dx = self.pos.x - center_x
        dy = self.pos.y - center_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Collision détectée
        wall_distance = container_radius - self.size
        if distance > wall_distance:
            # Normaliser
            if distance > 0:
                # 🔥 VIRAL: Grossir à chaque rebond
                if self.size < self.max_size:
                    self.size *= 1.15
                wall_distance = container_radius - self.size

                nx = dx / distance
                ny = dy / distance
                
                # Repositionner
                self.pos.x = center_x + nx * wall_distance
                self.pos.y = center_y + ny * wall_distance
                
                # Réflexion élastique
                dot = self.vel.vx * nx + self.vel.vy * ny
                
                if dot > self.max_speed:
                    self.restitution = 1.0
                    
                self.vel.vx = (self.vel.vx - 2 * dot * nx) * self.restitution
                self.vel.vy = (self.vel.vy - 2 * dot * ny) * self.restitution
                
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
        """Initialise simple"""
        try:
            # Créer la balle
            center_x, center_y = self.container_center
            start_x = center_x + 100
            start_y = center_y - 100
            
            # Vitesse initiale
            vx = 0
            vy = random.uniform(400, 200)
            
            self.ball = CleanBounce(pos=Vector2D(start_x, start_y), vel=Velocity(vx, vy), size=15)
            
            logger.info("Simulation clean initialisée")
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
            
            if success and os.path.exists(self.output_path):
                return self.output_path
            
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