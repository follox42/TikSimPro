# physics_engine/particles/system.py
"""
Système de particules avancé pour effets visuels
"""
import pygame
import math
import random
from typing import List, Tuple, Optional, Dict, Callable
from dataclasses import dataclass, field
from enum import Enum

from ..core.vector import Vector2D
from ..core.utils import hsv_to_rgb, rainbow_color, lerp, smooth_step

class BlendMode(Enum):
    """Modes de mélange pour les particules"""
    NORMAL = 0
    ADD = 1
    MULTIPLY = 2
    SCREEN = 3

@dataclass
class ParticleData:
    """Données d'une particule individuelle"""
    position: Vector2D
    velocity: Vector2D
    acceleration: Vector2D = field(default_factory=lambda: Vector2D(0, 0))
    
    # Propriétés visuelles
    color: Tuple[int, int, int] = (255, 255, 255)
    alpha: float = 1.0
    size: float = 5.0
    rotation: float = 0.0
    
    # Propriétés d'animation
    life: float = 1.0  # Durée de vie restante (0-1)
    max_life: float = 1.0  # Durée de vie totale
    
    # Propriétés physiques
    mass: float = 1.0
    drag: float = 0.0
    gravity_scale: float = 1.0
    
    # Propriétés spéciales
    metadata: Dict = field(default_factory=dict)

class ParticleEmitter:
    """Émetteur de particules"""
    
    def __init__(self, position: Vector2D):
        self.position = position.copy()
        self.active = True
        self.particles = []
        
        # Propriétés d'émission
        self.emission_rate = 10.0  # particules par seconde
        self.emission_accumulator = 0.0
        self.burst_count = 0
        self.burst_timer = 0.0
        
        # Zone d'émission
        self.emission_shape = "point"  # "point", "circle", "line", "rect"
        self.emission_radius = 0.0
        self.emission_size = Vector2D(10, 10)
        
        # Propriétés des particules
        self.particle_life_min = 1.0
        self.particle_life_max = 3.0
        self.particle_speed_min = 50.0
        self.particle_speed_max = 100.0
        self.particle_angle_min = 0.0
        self.particle_angle_max = 360.0
        self.particle_size_min = 2.0
        self.particle_size_max = 8.0
        
        # Couleurs
        self.color_start = (255, 255, 255)
        self.color_end = (255, 255, 255)
        self.color_variance = 0.1
        
        # Physique
        self.gravity = Vector2D(0, 0)
        self.drag = 0.0
        
        # Effets
        self.size_over_life = None  # Fonction size(life_progress)
        self.alpha_over_life = None  # Fonction alpha(life_progress)
        self.color_over_life = None  # Fonction color(life_progress)
        
        # Rendu
        self.blend_mode = BlendMode.NORMAL
        self.texture = None
        
    def emit_burst(self, count: int):
        """Émet un burst de particules"""
        for _ in range(count):
            self._create_particle()
    
    def _create_particle(self) -> ParticleData:
        """Crée une nouvelle particule"""
        # Position d'émission
        if self.emission_shape == "point":
            pos = self.position.copy()
        elif self.emission_shape == "circle":
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(0, self.emission_radius)
            offset = Vector2D(math.cos(angle) * radius, math.sin(angle) * radius)
            pos = self.position + offset
        elif self.emission_shape == "line":
            t = random.uniform(-0.5, 0.5)
            pos = self.position + Vector2D(t * self.emission_size.x, 0)
        else:  # rect
            offset = Vector2D(
                random.uniform(-self.emission_size.x/2, self.emission_size.x/2),
                random.uniform(-self.emission_size.y/2, self.emission_size.y/2)
            )
            pos = self.position + offset
        
        # Vitesse initiale
        angle = math.radians(random.uniform(self.particle_angle_min, self.particle_angle_max))
        speed = random.uniform(self.particle_speed_min, self.particle_speed_max)
        velocity = Vector2D(math.cos(angle) * speed, math.sin(angle) * speed)
        
        # Propriétés
        life = random.uniform(self.particle_life_min, self.particle_life_max)
        size = random.uniform(self.particle_size_min, self.particle_size_max)
        
        # Couleur avec variance
        color = self._vary_color(self.color_start, self.color_variance)
        
        particle = ParticleData(
            position=pos,
            velocity=velocity,
            color=color,
            size=size,
            life=life,
            max_life=life,
            gravity_scale=1.0,
            drag=self.drag
        )
        
        self.particles.append(particle)
        return particle
    
    def _vary_color(self, base_color: Tuple[int, int, int], variance: float) -> Tuple[int, int, int]:
        """Applique une variance à une couleur"""
        r, g, b = base_color
        
        r = max(0, min(255, r + random.randint(-int(variance * 255), int(variance * 255))))
        g = max(0, min(255, g + random.randint(-int(variance * 255), int(variance * 255))))
        b = max(0, min(255, b + random.randint(-int(variance * 255), int(variance * 255))))
        
        return (r, g, b)
    
    def update(self, dt: float):
        """Met à jour l'émetteur et ses particules"""
        if not self.active:
            return
        
        # Émission continue
        if self.emission_rate > 0:
            self.emission_accumulator += self.emission_rate * dt
            while self.emission_accumulator >= 1.0:
                self._create_particle()
                self.emission_accumulator -= 1.0
        
        # Mise à jour des particules
        for particle in self.particles[:]:  # Copie pour éviter les modifications pendant l'itération
            self._update_particle(particle, dt)
            
            # Supprimer les particules mortes
            if particle.life <= 0:
                self.particles.remove(particle)
    
    def _update_particle(self, particle: ParticleData, dt: float):
        """Met à jour une particule individuelle"""
        # Durée de vie
        particle.life -= dt
        if particle.life <= 0:
            return
        
        # Progrès de vie (1.0 = nouveau, 0.0 = mort)
        life_progress = particle.life / particle.max_life
        
        # Forces
        total_force = Vector2D(0, 0)
        
        # Gravité
        if self.gravity.magnitude > 0:
            total_force += self.gravity * particle.gravity_scale * particle.mass
        
        # Drag
        if particle.drag > 0 and particle.velocity.magnitude > 0:
            drag_force = particle.velocity.normalized * -particle.velocity.magnitude_squared * particle.drag
            total_force += drag_force
        
        # Accélération
        particle.acceleration = total_force / particle.mass
        
        # Intégration de Verlet
        particle.velocity += particle.acceleration * dt
        particle.position += particle.velocity * dt
        
        # Mise à jour des propriétés visuelles
        self._update_particle_visuals(particle, life_progress)
    
    def _update_particle_visuals(self, particle: ParticleData, life_progress: float):
        """Met à jour les propriétés visuelles d'une particule"""
        # Taille sur la durée de vie
        if self.size_over_life:
            particle.size = self.size_over_life(life_progress) * particle.metadata.get('initial_size', particle.size)
        
        # Alpha sur la durée de vie
        if self.alpha_over_life:
            particle.alpha = self.alpha_over_life(life_progress)
        else:
            # Fade out par défaut
            particle.alpha = life_progress
        
        # Couleur sur la durée de vie
        if self.color_over_life:
            particle.color = self.color_over_life(life_progress)
        elif self.color_start != self.color_end:
            # Interpolation de couleur
            t = 1.0 - life_progress
            r = int(lerp(self.color_start[0], self.color_end[0], t))
            g = int(lerp(self.color_start[1], self.color_end[1], t))
            b = int(lerp(self.color_start[2], self.color_end[2], t))
            particle.color = (r, g, b)
    
    def render(self, screen: pygame.Surface):
        """Rendu de toutes les particules"""
        for particle in self.particles:
            self._render_particle(screen, particle)
    
    def _render_particle(self, screen: pygame.Surface, particle: ParticleData):
        """Rendu d'une particule individuelle"""
        if particle.alpha <= 0 or particle.size <= 0:
            return
        
        pos = (int(particle.position.x), int(particle.position.y))
        size = max(1, int(particle.size))
        color = particle.color
        
        # Appliquer l'alpha
        if particle.alpha < 1.0:
            alpha = int(particle.alpha * 255)
            color = (*color, alpha)
        
        try:
            if self.texture:
                # Rendu avec texture (à implémenter)
                pass
            else:
                # Rendu simple
                if self.blend_mode == BlendMode.ADD:
                    # Mode additif
                    temp_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(temp_surf, color, (size, size), size)
                    screen.blit(temp_surf, (pos[0] - size, pos[1] - size), special_flags=pygame.BLEND_ADD)
                else:
                    # Mode normal
                    pygame.draw.circle(screen, color, pos, size)
        except:
            pass  # Ignore rendering errors

class EffectManager:
    """Gestionnaire d'effets visuels"""
    
    def __init__(self):
        self.emitters = []
        self.screen_effects = []
        
        # Shake d'écran
        self.screen_shake = Vector2D(0, 0)
        self.screen_shake_decay = 0.9
        
        # Flash d'écran
        self.screen_flash = 0.0
        self.screen_flash_color = (255, 255, 255)
        self.screen_flash_decay = 0.95
        
    def add_emitter(self, emitter: ParticleEmitter):
        """Ajoute un émetteur"""
        self.emitters.append(emitter)
    
    def remove_emitter(self, emitter: ParticleEmitter):
        """Supprime un émetteur"""
        if emitter in self.emitters:
            self.emitters.remove(emitter)
    
    def create_explosion_effect(self, position: Vector2D, intensity: float = 1.0, color: Tuple[int, int, int] = (255, 100, 0)):
        """Crée un effet d'explosion"""
        emitter = ParticleEmitter(position)
        emitter.emission_rate = 0  # Pas d'émission continue
        emitter.particle_life_min = 0.5 * intensity
        emitter.particle_life_max = 1.5 * intensity
        emitter.particle_speed_min = 100 * intensity
        emitter.particle_speed_max = 300 * intensity
        emitter.particle_angle_min = 0
        emitter.particle_angle_max = 360
        emitter.particle_size_min = 3 * intensity
        emitter.particle_size_max = 10 * intensity
        emitter.color_start = color
        emitter.color_end = (color[0] // 3, color[1] // 3, color[2] // 3)
        emitter.gravity = Vector2D(0, 200 * intensity)
        emitter.drag = 0.5
        emitter.blend_mode = BlendMode.ADD
        
        # Fonctions d'animation
        emitter.size_over_life = lambda t: smooth_step(0.0, 0.3, t) * (1.0 - smooth_step(0.7, 1.0, t))
        emitter.alpha_over_life = lambda t: 1.0 - smooth_step(0.5, 1.0, t)
        
        # Burst initial
        emitter.emit_burst(int(20 * intensity))
        
        self.add_emitter(emitter)
        return emitter
    
    def create_trail_effect(self, position: Vector2D, velocity: Vector2D, color: Tuple[int, int, int] = (255, 255, 255)):
        """Crée un effet de trainée"""
        emitter = ParticleEmitter(position)
        emitter.emission_rate = 50
        emitter.emission_shape = "point"
        emitter.particle_life_min = 0.2
        emitter.particle_life_max = 0.8
        emitter.particle_speed_min = 0
        emitter.particle_speed_max = 20
        emitter.particle_angle_min = 0
        emitter.particle_angle_max = 360
        emitter.particle_size_min = 1
        emitter.particle_size_max = 3
        emitter.color_start = color
        emitter.color_end = color
        emitter.blend_mode = BlendMode.ADD
        
        # Alpha fade
        emitter.alpha_over_life = lambda t: t * t
        
        self.add_emitter(emitter)
        return emitter
    
    def create_sparkle_effect(self, position: Vector2D, count: int = 10):
        """Crée un effet de scintillement"""
        emitter = ParticleEmitter(position)
        emitter.emission_rate = 0
        emitter.emission_shape = "circle"
        emitter.emission_radius = 20
        emitter.particle_life_min = 0.5
        emitter.particle_life_max = 1.5
        emitter.particle_speed_min = 10
        emitter.particle_speed_max = 50
        emitter.particle_size_min = 1
        emitter.particle_size_max = 4
        emitter.blend_mode = BlendMode.ADD
        
        # Couleurs arc-en-ciel
        emitter.color_over_life = lambda t: rainbow_color(t * 2, 1.0, 1.0)
        emitter.size_over_life = lambda t: math.sin(t * math.pi)
        
        emitter.emit_burst(count)
        self.add_emitter(emitter)
        return emitter
    
    def create_collision_effect(self, position: Vector2D, normal: Vector2D, intensity: float = 1.0):
        """Crée un effet de collision"""
        # Angle de la normale
        normal_angle = math.atan2(normal.y, normal.x)
        
        emitter = ParticleEmitter(position)
        emitter.emission_rate = 0
        emitter.particle_life_min = 0.3
        emitter.particle_life_max = 0.8
        emitter.particle_speed_min = 50 * intensity
        emitter.particle_speed_max = 150 * intensity
        
        # Particules dans la direction de la normale
        emitter.particle_angle_min = math.degrees(normal_angle) - 45
        emitter.particle_angle_max = math.degrees(normal_angle) + 45
        
        emitter.particle_size_min = 2
        emitter.particle_size_max = 6
        emitter.color_start = (255, 255, 100)
        emitter.color_end = (255, 100, 0)
        emitter.gravity = Vector2D(0, 100)
        emitter.blend_mode = BlendMode.ADD
        
        emitter.emit_burst(int(8 * intensity))
        self.add_emitter(emitter)
        return emitter
    
    def add_screen_shake(self, intensity: float):
        """Ajoute un shake d'écran"""
        shake_x = random.uniform(-intensity, intensity)
        shake_y = random.uniform(-intensity, intensity)
        self.screen_shake += Vector2D(shake_x, shake_y)
    
    def add_screen_flash(self, intensity: float, color: Tuple[int, int, int] = (255, 255, 255)):
        """Ajoute un flash d'écran"""
        self.screen_flash = max(self.screen_flash, intensity)
        self.screen_flash_color = color
    
    def update(self, dt: float):
        """Met à jour tous les effets"""
        # Mise à jour des émetteurs
        for emitter in self.emitters[:]:
            emitter.update(dt)
            
            # Supprimer les émetteurs inactifs sans particules
            if not emitter.active and len(emitter.particles) == 0:
                self.emitters.remove(emitter)
        
        # Décroissance du shake
        self.screen_shake *= self.screen_shake_decay
        if self.screen_shake.magnitude < 0.1:
            self.screen_shake = Vector2D(0, 0)
        
        # Décroissance du flash
        self.screen_flash *= self.screen_flash_decay
        if self.screen_flash < 0.01:
            self.screen_flash = 0.0
    
    def render(self, screen: pygame.Surface):
        """Rendu de tous les effets"""
        # Rendu des particules
        for emitter in self.emitters:
            emitter.render(screen)
        
        # Flash d'écran
        if self.screen_flash > 0:
            flash_surface = pygame.Surface(screen.get_size())
            flash_surface.fill(self.screen_flash_color)
            flash_surface.set_alpha(int(self.screen_flash * 255))
            screen.blit(flash_surface, (0, 0), special_flags=pygame.BLEND_ADD)
    
    def get_screen_offset(self) -> Tuple[int, int]:
        """Retourne l'offset d'écran pour le shake"""
        return (int(self.screen_shake.x), int(self.screen_shake.y))
    
    def clear_all_effects(self):
        """Supprime tous les effets"""
        self.emitters.clear()
        self.screen_shake = Vector2D(0, 0)
        self.screen_flash = 0.0

# Fonctions d'aide pour créer des courbes d'animation
def ease_in_quad(t: float) -> float:
    """Ease-in quadratique"""
    return t * t

def ease_out_quad(t: float) -> float:
    """Ease-out quadratique"""
    return 1 - (1 - t) * (1 - t)

def ease_in_out_quad(t: float) -> float:
    """Ease-in-out quadratique"""
    if t < 0.5:
        return 2 * t * t
    return 1 - 2 * (1 - t) * (1 - t)

def bounce(t: float) -> float:
    """Fonction de rebond"""
    if t < 1/2.75:
        return 7.5625 * t * t
    elif t < 2/2.75:
        t -= 1.5/2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5/2.75:
        t -= 2.25/2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625/2.75
        return 7.5625 * t * t + 0.984375

def elastic(t: float) -> float:
    """Fonction élastique"""
    if t <= 0:
        return 0
    if t >= 1:
        return 1
    
    p = 0.3
    s = p / 4
    return -(2**(-10*t)) * math.sin((t - s) * (2 * math.pi) / p) + 1