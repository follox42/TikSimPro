# rectangle.py
import pygame
import math
from element import Element

class Rectangle(Element):
    def __init__(self, center, width, height, color=(255, 255, 255), angle=0):
        super().__init__(center, color, angle)
        self.width = width
        self.height = height
        
        # Propriétés physiques spécifiques aux rectangles
        self.mass = width * height
        self.moment_of_inertia = (1/12) * self.mass * (width*width + height*height)
    
    def get_corners(self):
        """Retourne les quatre coins du rectangle"""
        half_w = self.width / 2
        half_h = self.height / 2
        
        # Positions des coins par rapport au centre (sans rotation)
        corners = [
            pygame.Vector2(-half_w, -half_h),  # Haut-gauche
            pygame.Vector2(half_w, -half_h),   # Haut-droite
            pygame.Vector2(half_w, half_h),    # Bas-droite
            pygame.Vector2(-half_w, half_h)    # Bas-gauche
        ]
        
        # Appliquer la rotation et translation
        return [self._local_to_world(corner) for corner in corners]
    
    def draw(self, surface, color=None):
        """Dessine le rectangle sur la surface"""
        if color is None:
            color = self.color
        
        # Obtenir les coins du rectangle avec rotation
        corners = self.get_corners()
        
        # Dessiner le rectangle
        pygame.draw.polygon(surface, color, corners)
        
        # Dessiner une ligne pour montrer la rotation
        center_to_corner = corners[1] - self.center  # Centre vers coin haut-droite
        midpoint = self.center + center_to_corner * 0.5
        pygame.draw.line(surface, (0, 0, 0), self.center, midpoint, 2)
    
    def contains(self, point):
        """Vérifie si un point est à l'intérieur du rectangle"""
        # Transformer le point dans l'espace local du rectangle
        local_point = self._world_to_local(point)
        
        # Vérifier si le point est dans les limites du rectangle
        half_w = self.width / 2
        half_h = self.height / 2
        
        return (abs(local_point.x) <= half_w and 
                abs(local_point.y) <= half_h)
    
    def closest_point_on_surface(self, point):
        """Retourne le point le plus proche sur la surface du rectangle"""
        # Transformer le point dans l'espace local du rectangle
        local_point = self._world_to_local(point)
        
        # Calculer les limites du rectangle
        half_w = self.width / 2
        half_h = self.height / 2
        
        # Si le point est à l'intérieur du rectangle, trouver le bord le plus proche
        if abs(local_point.x) <= half_w and abs(local_point.y) <= half_h:
            # Calculer la distance aux quatre bords
            dist_left = half_w + local_point.x
            dist_right = half_w - local_point.x
            dist_top = half_h + local_point.y
            dist_bottom = half_h - local_point.y
            
            # Trouver la distance minimale
            min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
            
            # Ajuster le point pour qu'il soit sur le bord le plus proche
            if min_dist == dist_left:
                local_point.x = -half_w
            elif min_dist == dist_right:
                local_point.x = half_w
            elif min_dist == dist_top:
                local_point.y = -half_h
            else:  # min_dist == dist_bottom
                local_point.y = half_h
        else:
            # Limiter les coordonnées du point aux limites du rectangle
            local_point.x = max(-half_w, min(local_point.x, half_w))
            local_point.y = max(-half_h, min(local_point.y, half_h))
        
        # Transformer le point local en point monde
        return self._local_to_world(local_point)
    
    def get_normal_at_point(self, point):
        """Retourne la normale à la surface au point donné"""
        # Transformer le point dans l'espace local du rectangle
        local_point = self._world_to_local(point)
        
        # Calculer les limites du rectangle
        half_w = self.width / 2
        half_h = self.height / 2
        
        # Tolérance pour comparer les flottants
        epsilon = 1e-6
        
        # Déterminer sur quel côté se trouve le point
        local_normal = pygame.Vector2(0, 0)
        
        if abs(local_point.x - half_w) < epsilon:  # Côté droit
            local_normal = pygame.Vector2(1, 0)
        elif abs(local_point.x + half_w) < epsilon:  # Côté gauche
            local_normal = pygame.Vector2(-1, 0)
        elif abs(local_point.y - half_h) < epsilon:  # Côté bas
            local_normal = pygame.Vector2(0, 1)
        elif abs(local_point.y + half_h) < epsilon:  # Côté haut
            local_normal = pygame.Vector2(0, -1)
        
        # Transformer la normale locale en normale monde
        world_normal = self._local_to_world_direction(local_normal)
        return world_normal.normalize()
    
    def collide(self, element):
        """Gère la collision avec un autre élément"""
        if isinstance(element, Rectangle):
            # TODO: Implémenter la collision entre deux rectangles (SAT)
            return False
        else:
            # Pour les autres types d'éléments (comme Circle), utiliser leur méthode de collision
            return element.collide(self)
    
    def get_collision_normal(self, other_element):
        """Retourne le vecteur normal de collision avec un autre élément"""
        if isinstance(other_element, Rectangle):
            # TODO: Implémenter pour deux rectangles
            return pygame.Vector2(0, 0)
        else:
            # Pour d'autres types d'éléments, utiliser le point le plus proche
            closest_point = self.closest_point_on_surface(other_element.center)
            return -self.get_normal_at_point(closest_point)  # Inverse car c'est la normale sortante
    
    def get_collision_depth(self, other_element):
        """Retourne la profondeur de pénétration avec un autre élément"""
        if isinstance(other_element, Rectangle):
            # TODO: Implémenter pour deux rectangles
            return 0
        elif hasattr(other_element, 'radius'):  # Probablement un Circle
            closest_point = self.closest_point_on_surface(other_element.center)
            distance = (closest_point - other_element.center).length()
            return other_element.radius - distance
        else:
            return 0
    
    def distance_to_point(self, point):
        """Calcule la distance de la surface du rectangle à un point"""
        closest = self.closest_point_on_surface(point)
        return (point - closest).length()
    
    def get_point_at_normal(self, normal):
        """Retourne le point sur la surface du rectangle dans la direction de la normale donnée"""
        # Transformer la normale dans l'espace local du rectangle
        local_normal = self._world_to_local_direction(normal)
        local_normal = local_normal.normalize()
        
        half_w = self.width / 2
        half_h = self.height / 2
        
        # Déterminer quel côté du rectangle correspond à cette normale
        local_point = pygame.Vector2(0, 0)
        
        if abs(local_normal.x) > abs(local_normal.y):
            # Normale orientée horizontalement
            local_point.x = half_w * (1 if local_normal.x > 0 else -1)
            local_point.y = 0
        else:
            # Normale orientée verticalement
            local_point.x = 0
            local_point.y = half_h * (1 if local_normal.y > 0 else -1)
        
        # Transformer le point local en