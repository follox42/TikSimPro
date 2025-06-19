# physics_engine/collision/resolver.py
"""
Résolveur de collisions avec différentes stratégies
"""
from typing import List
from ..core.vector import Vector2D
from .detector import CollisionInfo

class CollisionResolver:
    """Résolveur de collisions principal"""
    
    def __init__(self):
        self.position_correction = True
        self.position_correction_factor = 0.8
        self.velocity_threshold = 0.01
        
    def resolve_collisions(self, collisions: List[CollisionInfo], dt: float):
        """Résout toutes les collisions"""
        for collision in collisions:
            self.resolve_collision(collision, dt)
    
    def resolve_collision(self, collision: CollisionInfo, dt: float):
        """Résout une collision individuelle"""
        body_a = collision.body_a
        body_b = collision.body_b
        normal = collision.normal
        penetration = collision.penetration
        
        # Correction de position
        if self.position_correction and penetration > 0:
            self._resolve_position(body_a, body_b, normal, penetration)
        
        # Résolution de vitesse
        self._resolve_velocity(body_a, body_b, normal, collision)
        
        # Callbacks de collision
        if body_a.on_collision:
            body_a.on_collision(body_a, body_b, collision)
        if body_b.on_collision:
            body_b.on_collision(body_b, body_a, collision)
    
    def _resolve_position(self, body_a, body_b, normal: Vector2D, penetration: float):
        """Corrige les positions pour séparer les objets"""
        # Calcul de la masse totale inverse
        inv_mass_a = 0 if body_a.static else body_a.inv_mass
        inv_mass_b = 0 if body_b.static else body_b.inv_mass
        total_inv_mass = inv_mass_a + inv_mass_b
        
        if total_inv_mass <= 0:
            return
        
        # Correction proportionnelle à la masse inverse
        correction = normal * (penetration * self.position_correction_factor / total_inv_mass)
        
        if not body_a.static:
            body_a.position -= correction * inv_mass_a
        if not body_b.static:
            body_b.position += correction * inv_mass_b
    
    def _resolve_velocity(self, body_a, body_b, normal: Vector2D, collision: CollisionInfo):
        """Résout les vitesses après collision"""
        # Vitesses relatives
        relative_velocity = body_b.velocity - body_a.velocity
        velocity_along_normal = relative_velocity.dot(normal)
        
        # Ne pas résoudre si les objets se séparent déjà
        if velocity_along_normal > 0:
            return
        
        # Coefficient de restitution
        restitution = min(body_a.restitution, body_b.restitution)
        
        # Calcul de l'impulsion
        impulse_scalar = -(1 + restitution) * velocity_along_normal
        
        # Masses
        inv_mass_a = 0 if body_a.static else body_a.inv_mass
        inv_mass_b = 0 if body_b.static else body_b.inv_mass
        
        impulse_scalar /= inv_mass_a + inv_mass_b
        impulse = normal * impulse_scalar
        
        # Appliquer l'impulsion
        if not body_a.static:
            body_a.velocity -= impulse * inv_mass_a
        if not body_b.static:
            body_b.velocity += impulse * inv_mass_b
        
        # Friction
        self._apply_friction(body_a, body_b, normal, impulse_scalar)
    
    def _apply_friction(self, body_a, body_b, normal: Vector2D, impulse_scalar: float):
        """Applique la friction lors de la collision"""
        # Vitesse relative
        relative_velocity = body_b.velocity - body_a.velocity
        
        # Composante tangentielle
        tangent = relative_velocity - normal * relative_velocity.dot(normal)
        
        if tangent.magnitude < self.velocity_threshold:
            return
        
        tangent = tangent.normalized
        
        # Magnitude de la friction
        friction_magnitude = -relative_velocity.dot(tangent)
        
        # Coefficient de friction combiné
        mu = math.sqrt(body_a.friction * body_b.friction)
        
        # Impulsion de friction
        if abs(friction_magnitude) < impulse_scalar * mu:
            # Friction statique
            friction_impulse = tangent * friction_magnitude
        else:
            # Friction dynamique
            friction_impulse = tangent * (-impulse_scalar * mu)
        
        # Masses
        inv_mass_a = 0 if body_a.static else body_a.inv_mass
        inv_mass_b = 0 if body_b.static else body_b.inv_mass
        
        # Appliquer la friction
        if not body_a.static:
            body_a.velocity -= friction_impulse * inv_mass_a
        if not body_b.static:
            body_b.velocity += friction_impulse * inv_mass_b

import math  # Import nécessaire pour la friction