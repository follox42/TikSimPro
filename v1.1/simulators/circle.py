# circle.py
import pygame
import math
from element import Element

class Circle(Element):
    def __init__(self, center, radius, color=(255, 255, 255), angle=0):
        super().__init__(center, color, angle)
        self.radius = radius
        
        # Propriétés physiques spécifiques aux cercles
        self.mass = math.pi * radius * radius
        self.moment_of_inertia = 0.5 * self.mass * radius * radius
    
    def contains(self, point):
        """Vérifie si un point est à l'intérieur du cercle"""
        return (point - self.center).length() <= self.radius
    
    def draw(self, surface, color=None):
        """Dessine le cercle sur la surface"""
        if color is None:
            color = self.color
        pygame.draw.circle(surface, color, self.center, self.radius)
        
        # Dessiner une ligne pour montrer la rotation
        end_point = self.center + pygame.Vector2(
            math.cos(math.radians(self.angle)), 
            math.sin(math.radians(self.angle))
        ) * self.radius
        pygame.draw.line(surface, (0, 0, 0), self.center, end_point, 2)
    
    def collide(self, element):
        """Gère la collision avec un autre élément de manière générique"""
        # Vérifier la distance entre notre centre et le point le plus proche de l'autre élément
        closest_point = element.closest_point_on_surface(self.center)
        return (closest_point - self.center).length() <= self.radius
    
    def get_collision_normal(self, other_element):
        """Retourne le vecteur normal de collision avec un autre élément de manière générique"""
        # Trouver le point le plus proche sur l'autre élément
        closest_point = other_element.closest_point_on_surface(self.center)
        
        # Calculer la normale - du point proche vers le centre du cercle
        normal = self.center - closest_point
        
        # Éviter la division par zéro si les points sont identiques
        if normal.length() == 0:
            return pygame.Vector2(1, 0)  # Direction arbitraire
        
        return normal.normalize()
    
    def get_collision_depth(self, other_element):
        """Retourne la profondeur de pénétration avec un autre élément"""
        # Trouver le point le plus proche sur l'autre élément
        closest_point = other_element.closest_point_on_surface(self.center)
        
        # Calculer la distance de ce point à notre centre
        distance = (closest_point - self.center).length()
        
        # La profondeur est notre rayon moins cette distance
        # (si positif, il y a collision)
        return self.radius - distance
    
    def get_point_at_normal(self, normal):
        """Retourne le point sur la surface du cercle dans la direction de la normale donnée"""
        # S'assurer que la normale est normalisée
        normalized = normal.normalize()
        
        # Le point sur la surface du cercle dans la direction de la normale est:
        # centre + rayon * direction normalisée
        return self.center + normalized * self.radius
    
    def closest_point_on_surface(self, point):
        """Retourne le point le plus proche sur la surface du cercle"""
        # Vecteur du centre vers le point
        direction = point - self.center
        
        # Si le point est au centre, choisir une direction arbitraire
        if direction.length() == 0:
            direction = pygame.Vector2(1, 0)
        
        # Normaliser et multiplier par le rayon
        direction = direction.normalize() * self.radius
        
        # Retourner le point sur la surface du cercle
        return self.center + direction
    
    def distance_to_point(self, point):
        """Calcule la distance de la surface du cercle à un point"""
        center_to_point = point - self.center
        distance = center_to_point.length()
        
        # Si le point est à l'intérieur du cercle, retourne une distance négative
        if distance <= self.radius:
            return distance - self.radius
            
        # Sinon, retourne la distance positive du point à la surface
        return distance - self.radius
    
    def get_normal_at_point(self, point):
        """Retourne la normale à la surface au point donné"""
        # Pour un cercle, la normale pointe du centre vers le point
        # Si le point est exactement au centre, retournez une normale arbitraire
        if point == self.center:
            return pygame.Vector2(1, 0)
        
        normal = point - self.center
        return normal.normalize()
    
    def is_inside_arc(self, center, radius, start_angle, arc_length):
        """Vérifie si le cercle est dans un secteur angulaire"""
        # Calculer l'angle du cercle par rapport au centre de l'arc
        to_center = self.center - center
        angle = (math.degrees(math.atan2(to_center.y, to_center.x)) + 360) % 360
        
        # Calculer l'angle de fin
        end_angle = (start_angle + arc_length) % 360
        
        # Vérifier si l'angle est dans la plage de l'arc
        if start_angle <= end_angle:
            return start_angle <= angle <= end_angle
        else:  # Arc traverse l'angle 0
            return angle >= start_angle or angle <= end_angle