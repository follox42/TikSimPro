# element.py
from abc import ABC, abstractmethod
import pygame
import math

penetration_slop = 0.5   # en pixels
correction_percent = 0  # entre 0.2 et 0.8 selon votre goût

class Element(ABC):
    def __init__(self, center, color=(255, 255, 255), angle=0):
        # Propriétés communes à tous les éléments
        self.center = pygame.Vector2(center)
        self.color = color
        self.angle = angle  # en degrés
        self.velocity = pygame.Vector2(0, 0)
        self.angular_velocity = 0
        self.mass = 1.0
        self.moment_of_inertia = 1.0  # Résistance à la rotation
        self.restitution = 0.8  # Coefficient de restitution (rebond)
        self.friction = 0.2  # Friction
        self.immovable = False
    
    def update(self, dt=1.0):
        """Met à jour la position et rotation de l'élément"""
        self.center += self.velocity * dt
        self.angle = (self.angle + self.angular_velocity * dt) % 360
    
    def apply_force(self, force, dt=1.0):
        """Applique une force à l'élément"""
        self.velocity += force * dt / self.mass
    
    def apply_torque(self, torque, dt=1.0):
        """Applique un couple à l'élément, modifiant sa vitesse angulaire"""
        self.angular_velocity += torque * dt / self.moment_of_inertia
    
    def apply_impulse(self, impulse, contact_point=None):
        """Applique une impulsion à l'élément"""
        self.velocity += impulse / self.mass
        
        # Si un point de contact est fourni, calculer le couple généré
        if contact_point:
            r = contact_point - self.center
            torque = r.cross(impulse)  # Utiliser la méthode cross si disponible, sinon calculer r.x * impulse.y - r.y * impulse.x
            self.angular_velocity += torque / self.moment_of_inertia
    
    @abstractmethod
    def draw(self, surface):
        """Dessine l'élément sur la surface"""
        pass
    
    @abstractmethod
    def collide(self, element):
        """Vérifie s'il y a collision avec un autre élément"""
        pass
    
    @abstractmethod
    def get_collision_normal(self, other_element):
        """Retourne le vecteur normal de collision avec un autre élément"""
        pass
    
    @abstractmethod
    def get_collision_depth(self, other_element):
        """Retourne la profondeur de pénétration avec un autre élément"""
        pass
    
    @abstractmethod
    def get_point_at_normal(self, normal):
        """Retourne le point sur la surface de l'élément dans la direction de la normale donnée"""
        pass
    
    @abstractmethod
    def closest_point_on_surface(self, point):
        """Retourne le point le plus proche sur la surface de l'élément depuis un point donné"""
        pass
    
    @abstractmethod
    def distance_to_point(self, point):
        """Calcule la distance de la surface de l'élément à un point"""
        pass
    
    @abstractmethod
    def get_normal_at_point(self, point):
        """Retourne la normale à la surface au point donné"""
        pass
    
    def resolve_collision(self, other_element):
        """Résout la collision avec un autre élément"""
        # Vérifier s'il y a collision
        if not self.collide(other_element):
            return False
        
        # Calculer le vecteur normal de collision
        normal = self.get_collision_normal(other_element)
        
        # Calculer la profondeur de pénétration
        depth = self.get_collision_depth(other_element)
        
        # Point de contact approximatif
        contact_point = self.closest_point_on_surface(other_element.center)
        
        # Séparer les éléments (correction de position)
        only_depth = max(depth - penetration_slop, 0)
        if only_depth > 0:
            # on ne pousse qu'une fraction percent
            correction = normal * (only_depth * correction_percent)
            inv_mass_sum = 1/self.mass + 1/other_element.mass
            # séparation proportionnelle aux masses
            self.center -= correction * (1/self.mass) / inv_mass_sum
            other_element.center += correction * (1/other_element.mass) / inv_mass_sum
        
        # Calculer la vitesse relative au point de contact
        rel_velocity = other_element.velocity - self.velocity
        
        # Calculer la vitesse relative le long de la normale
        normal_velocity = rel_velocity.dot(normal)
        
        # Si les objets s'éloignent déjà, ne pas appliquer d'impulsion
        if normal_velocity > 0:
            return False
        
        # Calculer l'impulsion (coefficient de restitution combiné)
        restitution = min(self.restitution, other_element.restitution)
        j = -(1 + restitution) * normal_velocity / inv_mass_sum
        
        # Appliquer l'impulsion
        impulse = normal * j
        if not self.immovable:
            self.apply_impulse(-impulse, contact_point)
        if not other_element.immovable:
            other_element.apply_impulse(impulse, contact_point)
        
        return True
    
    # Méthodes utilitaires pour transformer entre espaces monde et local
    def _world_to_local(self, point):
        """Convertit un point de l'espace monde à l'espace local de l'élément"""
        # Traduire le point relatif au centre de l'élément
        translated = point - self.center
        
        # Appliquer la rotation inverse
        rad_angle = -math.radians(self.angle)
        cos_a = math.cos(rad_angle)
        sin_a = math.sin(rad_angle)
        
        x = translated.x * cos_a - translated.y * sin_a
        y = translated.x * sin_a + translated.y * cos_a
        
        return pygame.Vector2(x, y)
    
    def _local_to_world(self, point):
        """Convertit un point de l'espace local à l'espace monde"""
        # Appliquer la rotation
        rad_angle = math.radians(self.angle)
        cos_a = math.cos(rad_angle)
        sin_a = math.sin(rad_angle)
        
        x = point.x * cos_a - point.y * sin_a
        y = point.x * sin_a + point.y * cos_a
        
        # Traduire le point au centre de l'élément
        return pygame.Vector2(x, y) + self.center
    
    def _world_to_local_direction(self, direction):
        """Convertit une direction de l'espace monde à l'espace local de l'élément"""
        rad_angle = -math.radians(self.angle)
        cos_a = math.cos(rad_angle)
        sin_a = math.sin(rad_angle)
        
        x = direction.x * cos_a - direction.y * sin_a
        y = direction.x * sin_a + direction.y * cos_a
        
        return pygame.Vector2(x, y)
    
    def _local_to_world_direction(self, direction):
        """Convertit une direction de l'espace local à l'espace monde"""
        rad_angle = math.radians(self.angle)
        cos_a = math.cos(rad_angle)
        sin_a = math.sin(rad_angle)
        
        x = direction.x * cos_a - direction.y * sin_a
        y = direction.x * sin_a + direction.y * cos_a
        
        return pygame.Vector2(x, y)