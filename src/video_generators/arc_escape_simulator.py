import pygame
import math
import random
import colorsys
import logging
import os
from pygame import gfxdraw
from typing import Dict, Any, Optional, List, Tuple

from src.video_generators.base_video_generator import IVideoGenerator
from src.utils.video.background_manager import BackgroundManager, BackgroundMode
from src.utils.video.engagement_texts import EngagementTextManager, VideoType

logger = logging.getLogger("TikSimPro")

class Particle:
    """Particule individuelle pour effets visuels"""
    def __init__(self, x: float, y: float, vx: float, vy: float, color: Tuple[int, int, int], size: float = 3.0, life: float = 1.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.gravity = 800  # Gravité pour les particules

    def update(self, dt: float) -> bool:
        self.life -= dt
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.size = max(0.5, self.size * (1 - dt * 2))
        return self.life > 0

    def render(self, surface: pygame.Surface, center: Tuple[int, int], scale: float):
        if self.life <= 0: return
        fade = self.life / self.max_life
        col = (int(self.color[0]*fade), int(self.color[1]*fade), int(self.color[2]*fade))
        px = int((center[0] + self.x) * scale)
        py = int((center[1] + self.y) * scale)
        size = int(max(1, self.size * scale))
        pygame.draw.circle(surface, col, (px, py), size)


class VisualEffect:
    """Effet visuel (Pulse) - dure plus longtemps"""
    def __init__(self, radius: float, color: Tuple[int, int, int], width: int):
        self.radius = radius
        self.color = color
        self.width = float(width)
        self.life = 1.0

    def update(self, dt: float) -> bool:
        self.life -= dt * 0.8  # Beaucoup plus lent (était 2.5)
        self.radius += 80 * dt  # Expansion plus lente (était 200)
        self.width = max(0.1, self.width - dt * 5)  # Réduction plus lente (était 15)
        return self.life > 0

    def render(self, surface: pygame.Surface, center: Tuple[int, int], scale: float):
        if self.life <= 0 or self.width < 1: return

        # On scale tout pour le rendu HD
        r_scaled = self.radius * scale
        w_scaled = int(max(1, self.width * scale))
        cx_scaled = center[0] * scale
        cy_scaled = center[1] * scale

        fade = self.life
        col = (int(self.color[0]*fade), int(self.color[1]*fade), int(self.color[2]*fade))

        rect = pygame.Rect(
            cx_scaled - r_scaled,
            cy_scaled - r_scaled,
            r_scaled * 2,
            r_scaled * 2
        )
        pygame.draw.arc(surface, col, rect, 0, math.pi * 2, w_scaled)

class ArcLayer:
    def __init__(self, index: int, radius: float, hue: float, config: Dict[str, Any]):
        self.index = index
        self.radius = radius
        self.base_radius = radius  # Rayon de base pour l'animation ressort
        self.base_hue = hue

        self.thickness = config.get("wall_thickness", 20)
        gap_deg = config.get("gap_size_deg", 45)
        self.gap_size = math.radians(gap_deg)

        self.rotation = random.uniform(0, math.pi * 2)
        base_speed = config.get("rotation_speed", 1.2)
        direction = 1 if random.random() > 0.5 else -1
        self.rotation_speed = (base_speed + (index * 0.05)) * direction

        self.is_active = True
        self.is_current_target = False

        # Animation ressort
        self.spring_offset = 0.0  # Décalage du ressort
        self.spring_velocity = 0.0  # Vélocité du ressort
        self.spring_stiffness = 800.0  # Raideur du ressort (fort = rapide)
        self.spring_damping = 12.0  # Amortissement

    def trigger_spring(self, strength: float = 15.0):
        """Déclenche l'animation de ressort (quand la balle touche)"""
        self.spring_velocity = strength * 50  # Impulsion initiale vers l'extérieur

    def update(self, dt: float):
        self.rotation += self.rotation_speed * dt
        self.rotation = self.rotation % (math.pi * 2)

        # Physique du ressort (oscillation amortie)
        if abs(self.spring_offset) > 0.01 or abs(self.spring_velocity) > 0.1:
            # Force de rappel (loi de Hooke)
            spring_force = -self.spring_stiffness * self.spring_offset
            # Force d'amortissement
            damping_force = -self.spring_damping * self.spring_velocity
            # Accélération
            acceleration = spring_force + damping_force
            # Intégration
            self.spring_velocity += acceleration * dt
            self.spring_offset += self.spring_velocity * dt

            # Mise à jour du rayon avec l'offset
            self.radius = self.base_radius + self.spring_offset
        else:
            self.spring_offset = 0.0
            self.spring_velocity = 0.0
            self.radius = self.base_radius

    def get_color(self) -> Tuple[int, int, int]:
        sat = 0.85 if self.is_current_target else 0.4
        val = 1.0 if self.is_current_target else 0.6
        r, g, b = colorsys.hsv_to_rgb(self.base_hue/360, sat, val)
        return (int(r*255), int(g*255), int(b*255))

    def check_collision(self, ball_pos: Tuple[float, float], ball_radius: float) -> Tuple[bool, bool, Optional[float]]:
        bx, by = ball_pos
        dist = math.sqrt(bx*bx + by*by)
        
        inner_wall = self.radius - (self.thickness / 2)
        
        if dist + ball_radius >= inner_wall:
            ball_angle = math.atan2(by, bx)
            if ball_angle < 0: ball_angle += math.pi * 2
            
            current_rot = self.rotation % (math.pi * 2)
            angle_diff = abs(ball_angle - current_rot)
            if angle_diff > math.pi: 
                angle_diff = (math.pi * 2) - angle_diff
            
            in_gap = angle_diff < (self.gap_size / 2)
            
            if in_gap:
                return False, True, None
            else:
                return True, False, ball_angle
        return False, False, None

class ArcEscapeSimulator(IVideoGenerator):
    def __init__(self, width=1080, height=1920, fps=60, duration=30):
        super().__init__(width, height, fps, duration)
        self.center = (width // 2, height // 2)
        
        # === SUPER SAMPLING (La clé de l'antialiasing) ===
        # On rend l'image 3x plus grande, puis on la réduit.
        # Cela supprime tous les effets d'escalier sur les arcs.
        self.render_scale = 3 
        
        # Surface haute résolution
        self.hd_width = width * self.render_scale
        self.hd_height = height * self.render_scale
        self.hd_surface = pygame.Surface((self.hd_width, self.hd_height))
        
        self.config = {
            "layer_count": 25,          # Plus de layers pour 60sec
            "spacing": 28,              # Espacement augmenté
            "wall_thickness": 22,
            "gap_size_deg": 50,         # Gap légèrement réduit
            "gravity": 1200.0,          # Gravité normale
            "ball_size": 14,
            "start_hue": 0,
            "rotation_speed": 1.2,
            "restitution": 1.02,        # GAGNE de l'énergie au rebond!
            "air_resistance": 0.9998,   # Très peu de résistance
            "jitter_strength": 40.0,    # Chaos pour variété
            "max_velocity": 1400.0,     # Vitesse max plus haute
            "min_velocity": 300.0       # Vitesse MIN - jamais trop lent!
        }
        
        self.layers = []
        self.effects = []
        self.particles = []  # Liste des particules
        self.ball_pos = [0.0, 0.0]
        self.ball_vel = [0.0, 0.0]

        # Options
        self.enable_spring_animation = True  # Animation ressort sur collision
        self.enable_collision_particles = True  # Particules sur collision
        self.enable_passage_particles = True  # Particules sur passage

        # Background manager
        self.background_manager = BackgroundManager(self.hd_width, self.hd_height, BackgroundMode.ANIMATED_GRADIENT)
        self.background_manager.configure({"mode": BackgroundMode.ANIMATED_GRADIENT})

        # Engagement text manager
        self.engagement_manager: Optional[EngagementTextManager] = None
        self._intro_text: Optional[str] = None
        self.time_elapsed = 0.0

    def configure(self, config: Dict[str, Any]) -> bool:
        self.config.update(config)

        # Configure background mode
        if "background" in config:
            self.background_manager.configure(config["background"])
        elif "background_mode" in config:
            self.background_manager.configure({"mode": config["background_mode"]})

        return True

    def apply_trend_data(self, trend_data: Any) -> None:
        """Apply trend data for engagement texts"""
        self.engagement_manager = EngagementTextManager.for_arc_escape(trend_data)
        logger.info("ArcEscape engagement manager initialized")

    def get_ffmpeg_args(self, output_path: str) -> List[str]:
        return [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-s', f'{self.width}x{self.height}',
            '-r', str(self.fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-preset', 'superfast',
            '-crf', '17', # Qualité visuelle excellente
            '-pix_fmt', 'yuv420p',
            '-threads', '0',
            output_path
        ]

    def initialize_simulation(self) -> bool:
        self.layers = []
        self.effects = []
        self.particles = []
        self.current_layer_index = 0
        self.ball_pos = [0.0, 0.0]
        
        # Physique : Départ dynamique
        angle_deg = random.uniform(-130, -50)
        angle_rad = math.radians(angle_deg)
        speed = 550  # Vitesse initiale dynamique
        self.ball_vel = [math.cos(angle_rad) * speed, math.sin(angle_rad) * speed]
        
        start_radius = 150
        count = self.config["layer_count"]
        
        for i in range(count):
            radius = start_radius + i * self.config["spacing"]
            hue = (self.config["start_hue"] + i * (360 / count)) % 360
            layer = ArcLayer(i, radius, hue, self.config)
            if i == 0: layer.is_current_target = True
            self.layers.append(layer)
        return True

    def render_frame(self, surface: pygame.Surface, frame_number: int, dt: float) -> bool:
        self.time_elapsed += dt

        # 1. On travaille sur la surface HD (3x plus grande)
        # Use background manager instead of hardcoded fill
        self.background_manager.render(self.hd_surface, self.time_elapsed)

        self._update_physics(dt)
        self._update_effects(dt)
        
        # Centre scalé
        cx_hd = self.hd_width // 2
        cy_hd = self.hd_height // 2
        
        # Facteur d'échelle pour les dessins
        S = self.render_scale 
        
        # --- DESSIN SUR HD SURFACE ---
        
        # A. MURS
        for layer in self.layers:
            if not layer.is_active: continue
            
            color = layer.get_color()
            
            # Dimensions scalées
            r_scaled = layer.radius * S
            thick_scaled = int(layer.thickness * S)
            
            rect = pygame.Rect(cx_hd - r_scaled, cy_hd - r_scaled, r_scaled * 2, r_scaled * 2)
            
            if layer.is_current_target:
                gap_half = layer.gap_size / 2
                start_angle = -layer.rotation + gap_half
                stop_angle = -layer.rotation - gap_half + (2 * math.pi)
                
                # Astuce : On dessine l'arc sur la surface HD.
                # Même si c'est pixelisé ici, ça sera lisse après réduction.
                pygame.draw.arc(self.hd_surface, color, rect, start_angle, stop_angle, thick_scaled)
                
                # Pour rendre les bouts de l'arc ronds et jolis (Round Caps)
                # On calcule la position des extrémités du mur
                # (Optionnel, mais ça fait très pro)
                # start_cap_x = cx_hd + math.cos(start_angle) * r_scaled
                # start_cap_y = cy_hd - math.sin(start_angle) * r_scaled # Inversion Y pygame
                # pygame.draw.circle(self.hd_surface, color, (start_cap_x, start_cap_y), thick_scaled//2)
                
            else:
                pygame.draw.circle(self.hd_surface, color, (cx_hd, cy_hd), int(r_scaled), thick_scaled)

        # B. EFFETS
        for effect in self.effects:
            # On passe le scale à la méthode render de l'effet
            effect.render(self.hd_surface, (cx_hd, cy_hd), S)

        # B2. PARTICULES
        for particle in self.particles:
            particle.render(self.hd_surface, (self.width // 2, self.height // 2), S)

        # C. BALLE
        bx_hd = cx_hd + (self.ball_pos[0] * S)
        by_hd = cy_hd + (self.ball_pos[1] * S)
        ball_rad_hd = int(self.config["ball_size"] * S)
        
        # Dessin balle HD
        gfxdraw.filled_circle(self.hd_surface, int(bx_hd), int(by_hd), ball_rad_hd, (255, 255, 255))
        gfxdraw.aacircle(self.hd_surface, int(bx_hd), int(by_hd), ball_rad_hd, (255, 255, 255))

        # D. UI (Engagement texts)
        self._render_ui(self.hd_surface, S)

        # --- ÉTAPE FINALE : DOWNSCALING ---
        # On réduit la surface HD vers la surface finale avec un filtre de lissage (smoothscale)
        # C'est ÇA qui supprime l'aliasing.
        pygame.transform.smoothscale(self.hd_surface, (self.width, self.height), surface)

        return True

    def _render_ui(self, surface: pygame.Surface, scale: float):
        """Render UI with engagement texts - TikTok safe zone"""
        try:
            if not pygame.font.get_init():
                pygame.font.init()

            # TikTok safe zone: ~150px from top, ~200px from bottom
            safe_top = int(180 * scale)  # Safe zone top
            safe_bottom = self.hd_height - int(250 * scale)  # Safe zone bottom

            # Calculate progress (how many layers passed)
            progress = self.current_layer_index / max(1, len(self.layers))

            # Intro text (first 4 seconds)
            if self.time_elapsed < 4:
                font_size = int(38 * scale)
                font = pygame.font.Font(None, font_size)

                # Get intro text
                if self._intro_text is None:
                    if self.engagement_manager:
                        self._intro_text = self.engagement_manager.get_intro_text()
                    else:
                        self._intro_text = "Can the ball escape?"

                text = self._intro_text
                text_surface = font.render(text, True, (255, 255, 0))
                text_rect = text_surface.get_rect(center=(self.hd_width // 2, safe_top))

                # Outline
                outline = font.render(text, True, (0, 0, 0))
                for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                    surface.blit(outline, (text_rect.x + dx, text_rect.y + dy))

                surface.blit(text_surface, text_rect)

            # Layer counter - below intro text
            font_size = int(56 * scale)
            font = pygame.font.Font(None, font_size)
            count_text = f"{self.current_layer_index}/{len(self.layers)}"

            text_surface = font.render(count_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(self.hd_width // 2, safe_top + int(60 * scale)))

            # Outline
            outline = font.render(count_text, True, (0, 0, 0))
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                surface.blit(outline, (text_rect.x + dx, text_rect.y + dy))

            surface.blit(text_surface, text_rect)

            # Climax text (near the end) - in bottom safe zone
            if progress > 0.8:
                font_size = int(44 * scale)
                font = pygame.font.Font(None, font_size)

                if self.engagement_manager:
                    climax_text = self.engagement_manager.get_climax_text() or "Almost free!"
                else:
                    climax_text = "Almost free!"

                text_surface = font.render(climax_text, True, (100, 255, 100))
                text_rect = text_surface.get_rect(center=(self.hd_width // 2, safe_bottom))

                # Outline
                outline = font.render(climax_text, True, (0, 0, 0))
                for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                    surface.blit(outline, (text_rect.x + dx, text_rect.y + dy))

                surface.blit(text_surface, text_rect)

        except Exception as e:
            logger.debug(f"UI error: {e}")

    def _update_physics(self, dt: float):
        # Paramètres de config
        gravity = self.config.get("gravity", 1200.0)
        air_resistance = self.config.get("air_resistance", 0.9998)
        restitution = self.config.get("restitution", 1.02)
        jitter_strength = self.config.get("jitter_strength", 40.0)
        max_velocity = self.config.get("max_velocity", 1400.0)
        min_velocity = self.config.get("min_velocity", 300.0)

        # Appliquer gravité
        self.ball_vel[1] += gravity * dt

        # Résistance de l'air (très légère)
        self.ball_vel[0] *= air_resistance
        self.ball_vel[1] *= air_resistance

        # Calculer vitesse actuelle
        speed = math.sqrt(self.ball_vel[0]**2 + self.ball_vel[1]**2)

        # BOOST si trop lent - jamais ennuyeux!
        if speed < min_velocity and speed > 0:
            boost = min_velocity / speed
            self.ball_vel[0] *= boost
            self.ball_vel[1] *= boost
            speed = min_velocity

        # Limiter vitesse max
        if speed > max_velocity:
            scale = max_velocity / speed
            self.ball_vel[0] *= scale
            self.ball_vel[1] *= scale

        next_x = self.ball_pos[0] + self.ball_vel[0] * dt
        next_y = self.ball_pos[1] + self.ball_vel[1] * dt

        for layer in self.layers:
            layer.update(dt)

        if self.current_layer_index < len(self.layers):
            current_layer = self.layers[self.current_layer_index]
            collision, passed, normal_angle = current_layer.check_collision((next_x, next_y), self.config["ball_size"])

            if passed:
                self.ball_pos = [next_x, next_y]
                self._handle_layer_break(current_layer)
            elif collision:
                # Rebond avec perte d'énergie
                nx = math.cos(normal_angle)
                ny = math.sin(normal_angle)
                dot = self.ball_vel[0] * nx + self.ball_vel[1] * ny
                self.ball_vel[0] = (self.ball_vel[0] - 2 * dot * nx) * restitution
                self.ball_vel[1] = (self.ball_vel[1] - 2 * dot * ny) * restitution

                # Petit chaos contrôlé
                tangent_x, tangent_y = -ny, nx
                jitter = random.uniform(-1, 1) * jitter_strength
                self.ball_vel[0] += tangent_x * jitter
                self.ball_vel[1] += tangent_y * jitter

                safe_dist = current_layer.radius - (current_layer.thickness/2) - self.config["ball_size"] - 2
                angle_pos = math.atan2(next_y, next_x)
                self.ball_pos[0] = math.cos(angle_pos) * safe_dist
                self.ball_pos[1] = math.sin(angle_pos) * safe_dist

                # === ANIMATION RESSORT ===
                if self.enable_spring_animation:
                    speed = math.sqrt(self.ball_vel[0]**2 + self.ball_vel[1]**2)
                    spring_strength = min(15, speed / 150)
                    current_layer.trigger_spring(spring_strength)

                # === PARTICULES DE COLLISION ===
                if self.enable_collision_particles:
                    self._spawn_collision_particles(
                        self.ball_pos[0], self.ball_pos[1],
                        normal_angle, current_layer.get_color()
                    )

                # === AUDIO COLLISION ===
                speed = math.sqrt(self.ball_vel[0]**2 + self.ball_vel[1]**2)
                vol = min(1.0, speed / 1500.0)
                self.add_audio_event("collision", params={
                    "volume": vol,
                    "velocity_magnitude": speed,
                    "bounce_count": self.current_layer_index + 1,
                    "ball_size": self.config["ball_size"]
                })
            else:
                self.ball_pos = [next_x, next_y]
        else:
            self.ball_pos = [next_x, next_y]
            if (next_x**2 + next_y**2) > (self.width)**2:
                self.initialize_simulation()

    def _handle_layer_break(self, layer: ArcLayer):
        layer.is_active = False
        layer.is_current_target = False
        self.effects.append(VisualEffect(layer.radius, layer.get_color(), layer.thickness))
        self.current_layer_index += 1
        if self.current_layer_index < len(self.layers):
            self.layers[self.current_layer_index].is_current_target = True

        # === PARTICULES DE PASSAGE ===
        if self.enable_passage_particles:
            self._spawn_passage_particles(
                self.ball_pos[0], self.ball_pos[1],
                layer.get_color()
            )

        scale = [1.0, 1.12, 1.25, 1.33, 1.5, 1.6, 1.75, 2.0]
        pitch = scale[layer.index % len(scale)] + (layer.index // len(scale))
        self.add_audio_event("passage", params={
            "layer_index": layer.index,
            "total_layers": self.config["layer_count"],
            "velocity_magnitude": 0,
            "pitch": pitch
        })

    def _spawn_collision_particles(self, x: float, y: float, normal_angle: float, color: Tuple[int, int, int]):
        """Génère des particules lors d'une collision avec un arc"""
        num_particles = random.randint(8, 15)
        for _ in range(num_particles):
            # Direction opposée à la normale + spread
            angle = normal_angle + math.pi + random.uniform(-0.8, 0.8)
            speed = random.uniform(150, 400)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(2, 5)
            life = random.uniform(0.3, 0.6)
            # Variation de couleur
            r = min(255, color[0] + random.randint(-30, 50))
            g = min(255, color[1] + random.randint(-30, 50))
            b = min(255, color[2] + random.randint(-30, 50))
            self.particles.append(Particle(x, y, vx, vy, (r, g, b), size, life))

    def _spawn_passage_particles(self, x: float, y: float, color: Tuple[int, int, int]):
        """Génère des particules lors du passage dans un trou (effet célébration)"""
        num_particles = random.randint(20, 35)
        for _ in range(num_particles):
            # Explosion radiale
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(200, 600)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 200  # Bias vers le haut
            size = random.uniform(3, 7)
            life = random.uniform(0.5, 1.0)
            # Couleurs vives variées
            hue_shift = random.uniform(-0.1, 0.1)
            r = min(255, max(0, color[0] + random.randint(-20, 80)))
            g = min(255, max(0, color[1] + random.randint(-20, 80)))
            b = min(255, max(0, color[2] + random.randint(-20, 80)))
            self.particles.append(Particle(x, y, vx, vy, (r, g, b), size, life))

    def _update_effects(self, dt: float):
        self.effects = [e for e in self.effects if e.update(dt)]
        self.particles = [p for p in self.particles if p.update(dt)]

if __name__ == "__main__":
    print("🎯 ARC ESCAPE V4 (Supersampling Antialiasing) 🎯")
    sim = ArcEscapeSimulator(width=720, height=1280, fps=60, duration=20)
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    sim.set_output_path(f"{output_dir}/arc_escape_hd.mp4")
    
    try:
        sim.generate()
        print("✅ Vidéo générée avec succès.")
    except Exception as e:
        print(f"❌ Erreur: {e}")