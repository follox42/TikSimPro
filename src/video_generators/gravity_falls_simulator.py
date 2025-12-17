# src/video_generators/gravity_falls_simulator.py
"""

"""

import pygame
import math
import random
import time
import colorsys
from typing import Dict, Any, Optional, Tuple, List
import logging
import os

from src.video_generators.base_video_generator import IVideoGenerator
from src.core.data_pipeline import TrendData, AudioEvent
from src.utils.video.particles import SimpleParticle, ParticleSpawner
from src.utils.video.background_manager import BackgroundManager, BackgroundMode
from src.utils.video.engagement_texts import EngagementTextManager, VideoType

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
        
        # === PHYSIQUE ÉNERGIQUE MAIS CONTRÔLÉE ===
        self.gravity = 1800  # Gravité modérée (était 2800)
        self.restitution = 1.0  # Rebond neutre (était 1.08)
        self.min_velocity = 200  # Vitesse min plus basse (était 600)

        # Physique fluide
        self.air_resistance = 0.9995  # Léger freinage (était 1.001 qui accélérait)
        self.max_bounces = 0
        self.bounce_energy_boost = 1.02  # Léger boost seulement au rebond
        
    def update(self, dt: float, container_center: Tuple[float, float], container_radius: float, hue):
        """Physique énergique mais contrôlée - mouvement fluide et prévisible"""

        # Gravité modérée
        self.vel.vy += self.gravity * dt

        # Léger freinage (résistance de l'air réaliste)
        self.vel.vx *= self.air_resistance
        self.vel.vy *= self.air_resistance

        # Mouvement
        self.pos.x += self.vel.vx * dt
        self.pos.y += self.vel.vy * dt

        # Couleur
        self.hue = hue

        # Anti-arrêt doux : boost dans la direction actuelle avec légère déviation
        velocity_magnitude = math.sqrt(self.vel.vx * self.vel.vx + self.vel.vy * self.vel.vy)
        if velocity_magnitude < self.min_velocity and velocity_magnitude > 0:
            # Boost plus doux dans la direction actuelle
            current_angle = math.atan2(self.vel.vy, self.vel.vx)
            deviation = random.uniform(-0.3, 0.3)  # Petite déviation
            boost_angle = current_angle + deviation
            boost_strength = self.min_velocity * 1.1  # Boost doux (était 1.5)
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
                
                # Réflexion avec boost léger au rebond
                dot = self.vel.vx * nx + self.vel.vy * ny

                # Nouvelles vitesses avec réflexion propre
                new_vx = (self.vel.vx - 2 * dot * nx) * self.restitution
                new_vy = (self.vel.vy - 2 * dot * ny) * self.restitution

                # Léger boost au rebond (satisfaisant mais pas chaotique)
                new_vx *= self.bounce_energy_boost
                new_vy *= self.bounce_energy_boost

                # Contrôle de vitesse
                velocity_magnitude = math.sqrt(new_vx * new_vx + new_vy * new_vy)

                # Limite max
                if velocity_magnitude > self.max_speed:
                    scale = self.max_speed / velocity_magnitude
                    new_vx *= scale
                    new_vy *= scale

                # Garantie de vitesse minimale
                if velocity_magnitude < self.min_velocity:
                    scale = self.min_velocity / velocity_magnitude
                    new_vx *= scale
                    new_vy *= scale

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
        
        # Container - très grand pour 30sec sans saturation
        self.container_center = (width // 2, height // 2)
        self.container_radius = min(width, height) * 0.93 / 2  # 93% de la largeur
        
        # Balle
        self.ball = None

        # Couleur du container
        self.container_hue = 0.0
        
        # Stats
        self.bounce_count = 0
        self.time_elapsed = 0.0

        # Configuration physique par défaut (peut être overridée via configure())
        self._physics_config = {}

        # Particle system
        self.particles: List[SimpleParticle] = []
        self.enable_particles = True

        # Background manager
        self.background_manager = BackgroundManager(width, height, BackgroundMode.ANIMATED_GRADIENT)
        self.background_manager.configure({"mode": BackgroundMode.ANIMATED_GRADIENT})

        # Engagement text manager
        self.engagement_manager: Optional[EngagementTextManager] = None
        self._intro_text: Optional[str] = None  # Cached intro text

    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure avec paramètres physiques optionnels"""
        try:
            if "container_size" in config:
                size_factor = max(0.2, min(0.98, config["container_size"]))  # Max 98% de l'écran
                self.container_radius = min(self.width, self.height) * size_factor / 2

            # Stocker les paramètres physiques pour l'initialisation de la balle
            self._physics_config = {
                "gravity": config.get("gravity"),
                "restitution": config.get("restitution"),
                "ball_size": config.get("ball_size"),
                "min_velocity": config.get("min_velocity"),
                "max_speed": config.get("max_speed"),
                "bounce_energy_boost": config.get("bounce_energy_boost"),
            }
            # Filtrer les None
            self._physics_config = {k: v for k, v in self._physics_config.items() if v is not None}

            # Configure background mode
            if "background" in config:
                self.background_manager.configure(config["background"])
            elif "background_mode" in config:
                self.background_manager.configure({"mode": config["background_mode"]})

            # Configure particles
            if "enable_particles" in config:
                self.enable_particles = config["enable_particles"]

            if self._physics_config:
                logger.info(f"GravityFalls configuré avec physique: {self._physics_config}")
            else:
                logger.info("GravityFalls configuré (paramètres par défaut)")
            return True

        except Exception as e:
            logger.error(f"Erreur configuration: {e}")
            return False
    
    def apply_trend_data(self, trend_data: TrendData) -> None:
        """Apply trend data for engagement texts"""
        # Create engagement manager with AI-generated texts if available
        self.engagement_manager = EngagementTextManager.for_gravity_falls(trend_data)
        logger.info("Engagement manager initialized")
    
    def initialize_simulation(self) -> bool:
        """Initialise avec physique configurable"""
        try:
            # Position de départ naturelle
            center_x, center_y = self.container_center

            # Position aléatoire dans le cercle
            start_x = center_x + random.uniform(-150, 150)
            start_y = center_y + random.uniform(-300, -100)  # Plus haut pour plus de vitesse

            # Vitesse initiale modérée (moins chaotique)
            vx = random.uniform(-600, 600)
            vy = random.uniform(-400, 200)

            # Taille de la balle (configurable)
            ball_size = self._physics_config.get("ball_size", 15)

            self.ball = CleanBounce(pos=Vector2D(start_x, start_y), vel=Velocity(vx, vy), size=ball_size)

            # Appliquer les paramètres physiques configurés
            if "gravity" in self._physics_config:
                self.ball.gravity = self._physics_config["gravity"]
            if "restitution" in self._physics_config:
                self.ball.restitution = self._physics_config["restitution"]
            if "min_velocity" in self._physics_config:
                self.ball.min_velocity = self._physics_config["min_velocity"]
            if "max_speed" in self._physics_config:
                self.ball.max_speed = self._physics_config["max_speed"]
            if "bounce_energy_boost" in self._physics_config:
                self.ball.bounce_energy_boost = self._physics_config["bounce_energy_boost"]

            logger.info(f"Simulation initialisée - gravity={self.ball.gravity}, restitution={self.ball.restitution}")
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

            # 0. Render background (replaces black fill)
            self.background_manager.render(surface, self.time_elapsed)

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
                                       params={
                                           "volume": 0.5,
                                           "bounce_count": self.bounce_count,
                                           "note_index": self.bounce_count  # For melody sync
                                       })

                    # Spawn particles on collision
                    if self.enable_particles:
                        # Calculate collision normal angle
                        dx = self.ball.pos.x - self.container_center[0]
                        dy = self.ball.pos.y - self.container_center[1]
                        normal_angle = math.atan2(dy, dx)

                        # Spawn particles with ball color
                        new_particles = ParticleSpawner.spawn_collision_particles(
                            self.ball.pos.x, self.ball.pos.y,
                            normal_angle,
                            self.ball.get_color(),
                            count=random.randint(8, 15),
                            speed_range=(150, 400),
                            life_range=(0.3, 0.6)
                        )
                        self.particles.extend(new_particles)

            # 3. Update and render particles
            self.particles = [p for p in self.particles if p.update(dt)]
            for particle in self.particles:
                particle.render(surface)

            # 4. Dessiner le container actuel
            pygame.draw.circle(surface, current_container_color, self.container_center, int(self.container_radius), 10)

            # 5. Dessiner la balle
            if self.ball:
                self.ball.render(surface)

            # 6. UI simple
            self._render_ui(surface)

            return True

        except Exception as e:
            logger.error(f"Erreur rendu frame {frame_number}: {e}")
            return False
    
    def _render_ui(self, surface: pygame.Surface):
        """UI simple et propre avec textes d'engagement dynamiques"""
        try:
            # Ensure pygame font is initialized
            if not pygame.font.get_init():
                pygame.font.init()

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

            # Texte viral dynamique (intro - first 4 seconds)
            if self.time_elapsed < 4:
                viral_font = pygame.font.Font(None, 40)

                # Get intro text from engagement manager or use default
                if self._intro_text is None:
                    if self.engagement_manager:
                        self._intro_text = self.engagement_manager.get_intro_text()
                    else:
                        self._intro_text = "BALL GETS BIGGER!"

                viral_text = self._intro_text
                viral_surface = viral_font.render(viral_text, True, (255, 255, 0))
                viral_rect = viral_surface.get_rect(center=(self.width//2, 50))

                # Outline
                viral_outline = viral_font.render(viral_text, True, (0, 0, 0))
                for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    surface.blit(viral_outline, (viral_rect.x + dx, viral_rect.y + dy))

                surface.blit(viral_surface, viral_rect)

            # Alerte dynamique quand grosse (climax)
            if self.ball and self.ball.size > 80:
                warning_font = pygame.font.Font(None, 48)

                # Get climax text from engagement manager
                if self.engagement_manager:
                    warning_text = self.engagement_manager.get_climax_text() or "TOO BIG!"
                else:
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