# ring.py
import pygame
import math
from element import Element

class Ring(Element):
    def __init__(self, center, outer_radius, thickness, color=(255, 100, 100), angle=0):
        super().__init__(center, color, angle)
        self.outer_radius = outer_radius
        self.thickness = thickness
        self.inner_radius = outer_radius - thickness
        
        # Propriétés physiques
        area = math.pi * (outer_radius**2 - self.inner_radius**2)
        self.mass = area
        # Moment d'inertie pour un anneau
        self.moment_of_inertia = 0.5 * self.mass * (outer_radius**2 + self.inner_radius**2)
        
        # Paramètres de l'arc (trouée)
        self.arc_gap_angle = 60  # Degrés
        self.arc_start_angle = 0  # Degrés
    
    def draw(self, surface, bg_color=(30, 30, 30)):
        """Dessine l'anneau avec une approche de polygone d'arc unifié"""
        # Effacer l'arrière-plan où sera dessiné l'anneau
        pygame.draw.circle(surface, bg_color, self.center, self.outer_radius + 1)
        
        # Convertir les angles de degrés en radians
        start_angle = math.radians(self.arc_start_angle)
        end_angle = math.radians((self.arc_start_angle + 360 - self.arc_gap_angle) % 360)
        
        # Si start_angle > end_angle, on traverse le 0
        if start_angle > end_angle:
            end_angle += 2 * math.pi
        
        # Créer les points pour dessiner un polygone qui représente l'anneau avec sa trouée
        points = []
        
        # Nombre de segments pour une apparence lisse
        num_segments = 60
        
        # Points sur l'arc extérieur (dans le sens horaire)
        angle_step = (end_angle - start_angle) / num_segments
        for i in range(num_segments + 1):
            angle = start_angle + i * angle_step
            x = self.center.x + math.cos(angle) * self.outer_radius
            y = self.center.y + math.sin(angle) * self.outer_radius
            points.append((x, y))
        
        # Points sur l'arc intérieur (dans le sens anti-horaire)
        for i in range(num_segments, -1, -1):
            angle = start_angle + i * angle_step
            x = self.center.x + math.cos(angle) * self.inner_radius
            y = self.center.y + math.sin(angle) * self.inner_radius
            points.append((x, y))
        
        # Dessiner le polygone qui représente l'anneau
        if len(points) > 2:
            pygame.draw.polygon(surface, self.color, points)
    
    def collide_external(self, element):
        """Vérifie s'il y a collision avec l'extérieur de l'anneau en utilisant closest_point_on_surface"""
        # Obtenir le point le plus proche sur la surface de l'élément depuis le centre de l'anneau
        closest_point = element.closest_point_on_surface(self.center)
        
        # Calculer la distance entre ce point et le centre de l'anneau
        dist = (closest_point - self.center).length()
        
        # Il y a collision externe si ce point est au-delà du rayon extérieur
        return dist > self.outer_radius
    
    def collide_internal(self, element):
        """Vérifie s'il y a collision avec l'intérieur de l'anneau"""
        # Pour l'intérieur, on utilise l'inverse: le point le plus proche de l'élément depuis le centre
        # Obtenir le point le plus proche sur la surface de l'élément depuis le centre de l'anneau
        closest_point = element.get_point_at_normal(element.center - self.center)

        # Calculer la distance entre ce point et le centre de l'anneau
        dist = (closest_point - self.center).length()
        
        # Il y a collision interne si ce point est à l'intérieur du rayon intérieur
        return dist > self.inner_radius
    
    def collide(self, element):
        # vecteur et distance du centre à l'élément
        to_elem = element.center - self.center
        dist = to_elem.length()

        # calcul de l'angle en degrés [0,360)
        angle = (math.degrees(math.atan2(to_elem.y, to_elem.x)) + 360) % 360

        # bornes de l'arc
        start = self.arc_start_angle % 360
        end   = (start + self.arc_gap_angle) % 360

        # helper pour savoir si on est dans l'angle ouvert
        def in_gap(angle):
            if start < end:
                return start <= angle <= end
            else:
                return angle >= start or angle <= end

        # 1) Si on est dans le secteur de la trouée et entre les deux rayons → pas de collision
        if in_gap(angle) and (self.inner_radius < dist < self.outer_radius):
            return False

        # 2) Sinon on teste les collisions comme d'habitude
        return self.collide_external(element) or self.collide_internal(element)

    def get_collision_normal(self, element):
        """Retourne le vecteur normal de collision (externe ou interne)"""
        # Obtenir le point le plus proche sur la surface de l'élément
        closest_point = element.closest_point_on_surface(self.center)
        
        # Direction depuis le centre de l'anneau vers ce point
        direction = closest_point - self.center
        
        # Si c'est une collision externe, la normale pointe vers l'extérieur
        if self.collide_external(element):
            return direction.normalize()
        
        # Si c'est une collision interne, la normale pointe vers l'intérieur
        elif self.collide_internal(element):
            return -direction.normalize()
        
        # Pas de collision
        return pygame.Vector2(0, 0)
    
    def get_collision_depth(self, element):
        """Retourne la profondeur de pénétration (externe ou interne)"""
        # Obtenir le point le plus proche sur la surface de l'élément
        closest_point = element.closest_point_on_surface(self.center)
        dist = (closest_point - self.center).length()
        
        # Collision externe
        if self.collide_external(element):
            return dist - self.outer_radius
        
        # Collision interne
        if self.collide_internal(element):
            return self.inner_radius - dist
        
        return 0
    
    def is_in_arc_gap(self, point):
        """Vérifie si un point est dans la trouée de l'arc"""
        # Calculer l'angle du point par rapport au centre
        to_point = point - self.center
        angle = (math.degrees(math.atan2(to_point.y, to_point.x)) + 360) % 360
        
        # Calculer l'angle de fin
        end_angle = (self.arc_start_angle + self.arc_gap_angle) % 360
        
        # Vérifier si l'angle est dans la plage de l'arc
        if self.arc_start_angle <= end_angle:
            return self.arc_start_angle <= angle <= end_angle
        else:  # Arc traverse l'angle 0
            return angle >= self.arc_start_angle or angle <= end_angle
    
    def closest_point_on_surface(self, point):
        """Retourne le point le plus proche sur la surface de l'anneau"""
        # Vecteur du centre de l'anneau vers le point
        direction = point - self.center
        distance = direction.length()
        
        # Si le point est au centre, choisir une direction arbitraire
        if distance < 1e-6:
            normalized = pygame.Vector2(1, 0)
        else:
            normalized = direction / distance
        
        # Déterminer si le point est plus proche du cercle intérieur ou extérieur
        if distance < (self.inner_radius + self.outer_radius) / 2:
            # Plus proche du cercle intérieur
            return self.center + normalized * self.inner_radius
        else:
            # Plus proche du cercle extérieur
            return self.center + normalized * self.outer_radius
    
    def get_normal_at_point(self, point):
        """Retourne la normale à la surface au point donné"""
        # Vecteur du centre de l'anneau vers le point
        direction = point - self.center
        distance = direction.length()
        
        # Normaliser
        if distance < 1e-6:
            normalized = pygame.Vector2(1, 0)
        else:
            normalized = direction / distance
        
        # Déterminer si le point est sur le cercle intérieur ou extérieur
        inner_dist = abs(distance - self.inner_radius)
        outer_dist = abs(distance - self.outer_radius)
        
        if inner_dist < outer_dist:
            # Sur le cercle intérieur, la normale pointe vers l'intérieur
            return -normalized
        else:
            # Sur le cercle extérieur, la normale pointe vers l'extérieur
            return normalized
    
    def get_point_at_normal(self, normal):
        """Retourne le point sur la surface dans la direction de la normale"""
        # Normaliser
        normalized = normal.normalize()
        
        # Si la normale pointe vers l'extérieur, choisir le cercle extérieur
        if normalized.dot(normalized) > 0:
            return self.center + normalized * self.outer_radius
        else:
            # Si la normale pointe vers l'intérieur, choisir le cercle intérieur
            return self.center - normalized * self.inner_radius
    
    def distance_to_point(self, point):
        """Calcule la distance de la surface de l'anneau à un point"""
        dist = (point - self.center).length()
        
        # Si le point est entre les deux rayons, la distance est négative
        if self.inner_radius < dist < self.outer_radius:
            return -min(self.outer_radius - dist, dist - self.inner_radius)
        
        # Si le point est à l'intérieur du cercle intérieur
        if dist <= self.inner_radius:
            return self.inner_radius - dist
        
        # Si le point est à l'extérieur du cercle extérieur
        return dist - self.outer_radius
    