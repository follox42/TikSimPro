# physics_engine/core/engine.py
"""
Moteur de physique principal
"""
import pygame
import time
from typing import List, Optional, Callable
from dataclasses import dataclass

from .vector import Vector2D

@dataclass
class EngineConfig:
    """Configuration du moteur"""
    width: int = 1080
    height: int = 1920
    fps: int = 60
    gravity: Vector2D = Vector2D(0, 981)  # pixels/s²
    air_resistance: float = 0.99
    restitution: float = 0.8  # Coefficient de rebond
    friction: float = 0.1
    background_color: tuple = (15, 15, 25)
    max_velocity: float = 2000.0  # Vitesse max pour éviter les bugs

class PhysicsEngine:
    """Moteur de physique 2D modulaire"""
    
    def __init__(self, config: EngineConfig = None):
        self.config = config or EngineConfig()
        
        # État du moteur
        self.running = False
        self.paused = False
        self.time_scale = 1.0
        
        # Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.config.width, self.config.height))
        self.clock = pygame.time.Clock()
        
        # Objets physiques
        self.bodies = []
        self.constraints = []
        self.collision_pairs = []
        
        # Callbacks
        self.update_callbacks = []
        self.render_callbacks = []
        self.collision_callbacks = []
        
        # Timing
        self.dt = 1.0 / self.config.fps
        self.last_time = time.time()
        self.frame_count = 0
        
        # Debug
        self.debug_mode = False
        self.performance_stats = {
            'fps': 0,
            'frame_time': 0,
            'physics_time': 0,
            'render_time': 0,
            'bodies_count': 0
        }
    
    def add_body(self, body):
        """Ajoute un corps physique"""
        self.bodies.append(body)
        body.engine = self
    
    def remove_body(self, body):
        """Supprime un corps physique"""
        if body in self.bodies:
            self.bodies.remove(body)
            body.engine = None
    
    def add_constraint(self, constraint):
        """Ajoute une contrainte"""
        self.constraints.append(constraint)
        constraint.engine = self
    
    def add_update_callback(self, callback: Callable):
        """Ajoute un callback de mise à jour"""
        self.update_callbacks.append(callback)
    
    def add_render_callback(self, callback: Callable):
        """Ajoute un callback de rendu"""
        self.render_callbacks.append(callback)
    
    def add_collision_callback(self, callback: Callable):
        """Ajoute un callback de collision"""
        self.collision_callbacks.append(callback)
    
    def step(self, dt: float = None):
        """Un pas de simulation"""
        if self.paused:
            return
        
        if dt is None:
            dt = self.dt * self.time_scale
        
        physics_start = time.time()
        
        # 1. Appliquer les forces
        self._apply_forces(dt)
        
        # 2. Intégrer les positions
        self._integrate(dt)
        
        # 3. Détecter les collisions
        self._detect_collisions()
        
        # 4. Résoudre les collisions
        self._resolve_collisions(dt)
        
        # 5. Appliquer les contraintes
        self._apply_constraints(dt)
        
        # 6. Callbacks de mise à jour
        for callback in self.update_callbacks:
            callback(dt)
        
        self.performance_stats['physics_time'] = time.time() - physics_start
        self.performance_stats['bodies_count'] = len(self.bodies)
    
    def _apply_forces(self, dt: float):
        """Applique les forces à tous les corps"""
        for body in self.bodies:
            if not body.static:
                # Gravité
                body.acceleration = self.config.gravity.copy()
                
                # Résistance de l'air
                if body.velocity.magnitude > 0:
                    air_force = body.velocity.normalized * -body.velocity.magnitude_squared * 0.5 * body.drag_coefficient
                    body.acceleration += air_force / body.mass
                
                # Forces personnalisées
                for force in body.forces:
                    body.acceleration += force / body.mass
                
                # Nettoyer les forces
                body.forces.clear()
    
    def _integrate(self, dt: float):
        """Intégration de Verlet pour plus de stabilité"""
        for body in self.bodies:
            if not body.static:
                # Sauvegarde position précédente
                old_pos = body.position.copy()
                
                # Nouvelle position (Verlet)
                body.position += body.velocity * dt + body.acceleration * 0.5 * dt * dt
                
                # Nouvelle vitesse
                body.velocity += body.acceleration * dt
                
                # Limitation de vitesse
                if body.velocity.magnitude > self.config.max_velocity:
                    body.velocity = body.velocity.normalized * self.config.max_velocity
                
                # Friction
                body.velocity *= (1.0 - self.config.friction * dt)
    
    def _detect_collisions(self):
        """Détection de collisions optimisée"""
        self.collision_pairs.clear()
        
        # Collision simple O(n²) - à optimiser avec spatial hashing si nécessaire
        for i in range(len(self.bodies)):
            for j in range(i + 1, len(self.bodies)):
                body_a = self.bodies[i]
                body_b = self.bodies[j]
                
                # Skip si les deux sont statiques
                if body_a.static and body_b.static:
                    continue
                
                # Détection de collision spécifique aux formes
                collision_info = self._check_collision(body_a, body_b)
                if collision_info:
                    self.collision_pairs.append((body_a, body_b, collision_info))
    
    def _check_collision(self, body_a, body_b):
        """Vérifie la collision entre deux corps"""
        # Cette méthode sera implémentée dans le module collision
        # Pour l'instant, collision cercle-cercle simple
        if hasattr(body_a, 'radius') and hasattr(body_b, 'radius'):
            distance = body_a.position.distance_to(body_b.position)
            if distance < body_a.radius + body_b.radius:
                normal = (body_b.position - body_a.position).normalized
                penetration = body_a.radius + body_b.radius - distance
                return {
                    'normal': normal,
                    'penetration': penetration,
                    'contact_point': body_a.position + normal * body_a.radius
                }
        return None
    
    def _resolve_collisions(self, dt: float):
        """Résout les collisions détectées"""
        for body_a, body_b, collision_info in self.collision_pairs:
            # Séparer les objets
            normal = collision_info['normal']
            penetration = collision_info['penetration']
            
            # Correction de position
            correction = normal * penetration * 0.5
            if not body_a.static:
                body_a.position -= correction
            if not body_b.static:
                body_b.position += correction
            
            # Calcul des vitesses relatives
            relative_velocity = body_b.velocity - body_a.velocity
            velocity_along_normal = relative_velocity.dot(normal)
            
            # Ne pas résoudre si les objets se séparent déjà
            if velocity_along_normal > 0:
                continue
            
            # Coefficient de restitution
            restitution = min(body_a.restitution, body_b.restitution)
            
            # Calculer l'impulsion
            impulse_scalar = -(1 + restitution) * velocity_along_normal
            
            # Masses
            inv_mass_a = 0 if body_a.static else 1.0 / body_a.mass
            inv_mass_b = 0 if body_b.static else 1.0 / body_b.mass
            
            impulse_scalar /= inv_mass_a + inv_mass_b
            impulse = normal * impulse_scalar
            
            # Appliquer l'impulsion
            if not body_a.static:
                body_a.velocity -= impulse * inv_mass_a
            if not body_b.static:
                body_b.velocity += impulse * inv_mass_b
            
            # Callback de collision
            for callback in self.collision_callbacks:
                callback(body_a, body_b, collision_info)
    
    def _apply_constraints(self, dt: float):
        """Applique les contraintes"""
        for constraint in self.constraints:
            constraint.apply(dt)
    
    def render(self):
        """Rendu de la scène"""
        render_start = time.time()
        
        # Nettoyer l'écran
        self.screen.fill(self.config.background_color)
        
        # Rendu des corps
        for body in self.bodies:
            body.render(self.screen)
        
        # Callbacks de rendu personnalisés
        for callback in self.render_callbacks:
            callback(self.screen)
        
        # Debug
        if self.debug_mode:
            self._render_debug()
        
        pygame.display.flip()
        
        self.performance_stats['render_time'] = time.time() - render_start
    
    def _render_debug(self):
        """Rendu des informations de debug"""
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.Font(None, 36)
        y_offset = 10
        
        debug_info = [
            f"FPS: {self.performance_stats['fps']:.1f}",
            f"Bodies: {self.performance_stats['bodies_count']}",
            f"Physics: {self.performance_stats['physics_time']*1000:.1f}ms",
            f"Render: {self.performance_stats['render_time']*1000:.1f}ms",
        ]
        
        for info in debug_info:
            text = font.render(info, True, (255, 255, 255))
            self.screen.blit(text, (10, y_offset))
            y_offset += 30
    
    def run(self):
        """Boucle principale du moteur"""
        self.running = True
        
        while self.running:
            frame_start = time.time()
            
            # Événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_d:
                        self.debug_mode = not self.debug_mode
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
            
            # Simulation
            self.step()
            
            # Rendu
            self.render()
            
            # Timing
            self.clock.tick(self.config.fps)
            
            # Stats de performance
            frame_time = time.time() - frame_start
            self.performance_stats['frame_time'] = frame_time
            self.performance_stats['fps'] = self.clock.get_fps()
            
            self.frame_count += 1
        
        pygame.quit()