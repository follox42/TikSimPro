# physics_engine/physics/body.py
"""
Corps physiques pour le moteur de physique
"""
import pygame
import math
from typing import List, Optional, Tuple, Union
from abc import ABC, abstractmethod

from ..core.vector import Vector2D
from ..core.utils import rainbow_color, hsv_to_rgb

class PhysicsBody(ABC):
    """Classe de base pour tous les corps physiques"""
    
    def __init__(self, position: Vector2D, mass: float = 1.0, static: bool = False):
        # Propriétés physiques
        self.position = position.copy()
        self.velocity = Vector2D(0, 0)
        self.acceleration = Vector2D(0, 0)
        self.mass = mass
        self.inv_mass = 0.0 if static else 1.0 / mass
        self.static = static
        
        # Propriétés matérielles
        self.restitution = 0.8  # Coefficient de rebond
        self.friction = 0.3
        self.drag_coefficient = 0.1
        
        # Forces accumulées
        self.forces = []
        
        # Propriétés visuelles
        self.color = (255, 255, 255)
        self.visible = True
        self.glow = False
        self.glow_radius = 0
        self.trail_enabled = False
        self.trail_points = []
        self.trail_max_length = 50
        
        # Référence au moteur
        self.engine = None
        
        # Tags pour l'identification
        self.tags = set()
        
        # Callbacks personnalisés
        self.on_collision = None
    
    def add_force(self, force: Vector2D):
        """Ajoute une force au corps"""
        self.forces.append(force)
    
    def add_impulse(self, impulse: Vector2D):
        """Ajoute une impulsion au corps"""
        if not self.static:
            self.velocity += impulse * self.inv_mass
    
    def add_tag(self, tag: str):
        """Ajoute un tag"""
        self.tags.add(tag)
    
    def has_tag(self, tag: str) -> bool:
        """Vérifie si le corps a un tag"""
        return tag in self.tags
    
    def update_trail(self):
        """Met à jour la trainée"""
        if self.trail_enabled:
            self.trail_points.append(self.position.copy())
            if len(self.trail_points) > self.trail_max_length:
                self.trail_points.pop(0)
    
    def render_trail(self, screen: pygame.Surface):
        """Rendu de la trainée"""
        if not self.trail_enabled or len(self.trail_points) < 2:
            return
        
        for i in range(1, len(self.trail_points)):
            alpha = i / len(self.trail_points)
            color = tuple(int(c * alpha) for c in self.color)
            width = max(1, int(alpha * 3))
            
            start = self.trail_points[i-1].tuple()
            end = self.trail_points[i].tuple()
            
            try:
                pygame.draw.line(screen, color, start, end, width)
            except:
                pass  # Ignore invalid coordinates
    
    def render_glow(self, screen: pygame.Surface):
        """Rendu de l'effet de lueur"""
        if not self.glow or self.glow_radius <= 0:
            return
        
        # Créer une surface pour l'effet de lueur
        glow_surf = pygame.Surface((self.glow_radius * 4, self.glow_radius * 4), pygame.SRCALPHA)
        center = (self.glow_radius * 2, self.glow_radius * 2)
        
        # Dégradé radial
        for r in range(self.glow_radius, 0, -2):
            alpha = int(30 * (1 - r / self.glow_radius))
            color = (*self.color, alpha)
            pygame.draw.circle(glow_surf, color, center, r)
        
        # Blitter sur l'écran
        glow_pos = (self.position.x - self.glow_radius * 2, 
                   self.position.y - self.glow_radius * 2)
        screen.blit(glow_surf, glow_pos, special_flags=pygame.BLEND_ADD)
    
    @abstractmethod
    def render(self, screen: pygame.Surface):
        """Rendu du corps (à implémenter dans les sous-classes)"""
        pass
    
    @abstractmethod
    def get_bounding_box(self) -> Tuple[Vector2D, Vector2D]:
        """Retourne la bounding box (min, max)"""
        pass

class Circle(PhysicsBody):
    """Corps physique circulaire"""
    
    def __init__(self, position: Vector2D, radius: float, mass: float = 1.0, static: bool = False):
        super().__init__(position, mass, static)
        self.radius = radius
        self.original_radius = radius
        
        # Propriétés visuelles spécifiques
        self.outline_width = 0
        self.outline_color = (255, 255, 255)
        self.pulsing = False
        self.pulse_speed = 1.0
        self.pulse_amplitude = 0.1
        self.pulse_phase = 0.0
        
        # Animation
        self.rotation = 0.0
        self.angular_velocity = 0.0
        
        # Textures/patterns
        self.pattern = None  # 'stripes', 'checker', etc.
        self.pattern_density = 10
    
    def update_pulse(self, dt: float):
        """Met à jour l'animation de pulsation"""
        if self.pulsing:
            self.pulse_phase += self.pulse_speed * dt
            scale = 1.0 + math.sin(self.pulse_phase) * self.pulse_amplitude
            self.radius = self.original_radius * scale
    
    def update_rotation(self, dt: float):
        """Met à jour la rotation"""
        self.rotation += self.angular_velocity * dt
    
    def render(self, screen: pygame.Surface):
        """Rendu du cercle"""
        if not self.visible:
            return
        
        # Trainée
        self.render_trail(screen)
        
        # Lueur
        self.render_glow(screen)
        
        # Position à l'écran
        pos = (int(self.position.x), int(self.position.y))
        radius = int(self.radius)
        
        if radius <= 0:
            return
        
        # Cercle principal
        if self.pattern == 'stripes':
            self._render_striped_circle(screen, pos, radius)
        elif self.pattern == 'checker':
            self._render_checkered_circle(screen, pos, radius)
        else:
            pygame.draw.circle(screen, self.color, pos, radius)
        
        # Contour
        if self.outline_width > 0:
            pygame.draw.circle(screen, self.outline_color, pos, radius, self.outline_width)
    
    def _render_striped_circle(self, screen: pygame.Surface, pos: Tuple[int, int], radius: int):
        """Rendu d'un cercle avec motif rayé"""
        # Créer une surface temporaire
        temp_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        temp_center = (radius, radius)
        
        # Dessiner les rayures
        stripe_width = max(1, radius // self.pattern_density)
        for i in range(-radius, radius, stripe_width * 2):
            color = self.color if (i // stripe_width) % 2 == 0 else (0, 0, 0, 0)
            pygame.draw.rect(temp_surf, color, (i + radius, 0, stripe_width, radius * 2))
        
        # Masquer avec un cercle
        mask_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(mask_surf, (255, 255, 255, 255), temp_center, radius)
        temp_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Blitter sur l'écran
        screen.blit(temp_surf, (pos[0] - radius, pos[1] - radius))
    
    def _render_checkered_circle(self, screen: pygame.Surface, pos: Tuple[int, int], radius: int):
        """Rendu d'un cercle avec motif damier"""
        # Similaire aux rayures mais en damier
        pygame.draw.circle(screen, self.color, pos, radius)
    
    def get_bounding_box(self) -> Tuple[Vector2D, Vector2D]:
        """Bounding box du cercle"""
        min_pos = Vector2D(self.position.x - self.radius, self.position.y - self.radius)
        max_pos = Vector2D(self.position.x + self.radius, self.position.y + self.radius)
        return (min_pos, max_pos)

class Segment(PhysicsBody):
    """Segment de ligne pour les collisions"""
    
    def __init__(self, start: Vector2D, end: Vector2D, thickness: float = 5.0, static: bool = True):
        center = (start + end) / 2
        super().__init__(center, float('inf'), static)
        
        self.start = start.copy()
        self.end = end.copy()
        self.thickness = thickness
        self.original_thickness = thickness
        
        # Propriétés visuelles
        self.rounded_ends = True
        self.dashed = False
        self.dash_length = 10
        self.dash_gap = 5
        
        # Animation
        self.flow_effect = False
        self.flow_speed = 1.0
        self.flow_phase = 0.0
    
    def get_length(self) -> float:
        """Longueur du segment"""
        return self.start.distance_to(self.end)
    
    def get_direction(self) -> Vector2D:
        """Direction normalisée du segment"""
        return (self.end - self.start).normalized
    
    def get_normal(self) -> Vector2D:
        """Normale perpendiculaire au segment"""
        direction = self.get_direction()
        return Vector2D(-direction.y, direction.x)
    
    def closest_point_on_segment(self, point: Vector2D) -> Vector2D:
        """Point le plus proche sur le segment"""
        line_vec = self.end - self.start
        point_vec = point - self.start
        
        if line_vec.magnitude_squared == 0:
            return self.start.copy()
        
        t = max(0, min(1, point_vec.dot(line_vec) / line_vec.magnitude_squared))
        return self.start + line_vec * t
    
    def distance_to_point(self, point: Vector2D) -> float:
        """Distance du point au segment"""
        closest = self.closest_point_on_segment(point)
        return point.distance_to(closest)
    
    def update_flow(self, dt: float):
        """Met à jour l'effet de flow"""
        if self.flow_effect:
            self.flow_phase += self.flow_speed * dt
    
    def render(self, screen: pygame.Surface):
        """Rendu du segment"""
        if not self.visible:
            return
        
        start_pos = self.start.tuple()
        end_pos = self.end.tuple()
        thickness = max(1, int(self.thickness))
        
        try:
            if self.dashed:
                self._render_dashed_line(screen, start_pos, end_pos, thickness)
            elif self.flow_effect:
                self._render_flow_line(screen, start_pos, end_pos, thickness)
            else:
                pygame.draw.line(screen, self.color, start_pos, end_pos, thickness)
                
                if self.rounded_ends:
                    pygame.draw.circle(screen, self.color, start_pos, thickness // 2)
                    pygame.draw.circle(screen, self.color, end_pos, thickness // 2)
        except:
            pass  # Ignore invalid coordinates
    
    def _render_dashed_line(self, screen: pygame.Surface, start: tuple, end: tuple, thickness: int):
        """Rendu d'une ligne pointillée"""
        line_vec = Vector2D(end[0] - start[0], end[1] - start[1])
        length = line_vec.magnitude
        
        if length == 0:
            return
        
        direction = line_vec / length
        pattern_length = self.dash_length + self.dash_gap
        
        current_pos = 0
        drawing = True
        
        while current_pos < length:
            segment_length = min(self.dash_length if drawing else self.dash_gap, length - current_pos)
            
            if drawing:
                seg_start = (start[0] + direction.x * current_pos, 
                           start[1] + direction.y * current_pos)
                seg_end = (start[0] + direction.x * (current_pos + segment_length),
                         start[1] + direction.y * (current_pos + segment_length))
                pygame.draw.line(screen, self.color, seg_start, seg_end, thickness)
            
            current_pos += segment_length
            drawing = not drawing
    
    def _render_flow_line(self, screen: pygame.Surface, start: tuple, end: tuple, thickness: int):
        """Rendu d'une ligne avec effet de flow"""
        # Dessiner la ligne de base plus sombre
        base_color = tuple(c // 2 for c in self.color)
        pygame.draw.line(screen, base_color, start, end, thickness)
        
        # Dessiner des segments lumineux qui se déplacent
        line_vec = Vector2D(end[0] - start[0], end[1] - start[1])
        length = line_vec.magnitude
        
        if length == 0:
            return
        
        direction = line_vec / length
        flow_segment_length = 20
        
        # Position du segment lumineux basée sur la phase
        flow_pos = (self.flow_phase * self.flow_speed) % (length + flow_segment_length)
        
        if flow_pos < length:
            seg_start_pos = max(0, flow_pos - flow_segment_length)
            seg_end_pos = min(length, flow_pos)
            
            if seg_end_pos > seg_start_pos:
                seg_start = (start[0] + direction.x * seg_start_pos,
                           start[1] + direction.y * seg_start_pos)
                seg_end = (start[0] + direction.x * seg_end_pos,
                         start[1] + direction.y * seg_end_pos)
                
                # Couleur plus brillante pour l'effet
                bright_color = tuple(min(255, c + 100) for c in self.color)
                pygame.draw.line(screen, bright_color, seg_start, seg_end, thickness)
    
    def get_bounding_box(self) -> Tuple[Vector2D, Vector2D]:
        """Bounding box du segment"""
        min_x = min(self.start.x, self.end.x) - self.thickness
        min_y = min(self.start.y, self.end.y) - self.thickness
        max_x = max(self.start.x, self.end.x) + self.thickness
        max_y = max(self.start.y, self.end.y) + self.thickness
        
        return (Vector2D(min_x, min_y), Vector2D(max_x, max_y))

class Ring(PhysicsBody):
    """Anneau pour les simulations de type TikTok"""
    
    def __init__(self, center: Vector2D, inner_radius: float, outer_radius: float, 
                 gap_angle: float = 0, gap_start: float = 0, static: bool = True):
        super().__init__(center, float('inf'), static)
        
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.gap_angle = gap_angle  # Angle du gap en degrés
        self.gap_start = gap_start  # Angle de début du gap en degrés
        
        # Propriétés d'animation
        self.rotation = 0.0
        self.rotation_speed = 0.0  # degrés par seconde
        
        # Propriétés visuelles
        self.gradient_enabled = False
        self.gradient_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        self.segments = 100  # Nombre de segments pour le rendu
        
        # Animation de couleur
        self.color_shift_enabled = False
        self.color_shift_speed = 1.0
        self.color_phase = 0.0
    
    def update_rotation(self, dt: float):
        """Met à jour la rotation"""
        self.rotation += self.rotation_speed * dt
        self.rotation = self.rotation % 360
    
    def update_color_shift(self, dt: float):
        """Met à jour le décalage de couleur"""
        if self.color_shift_enabled:
            self.color_phase += self.color_shift_speed * dt
    
    def has_gap(self) -> bool:
        """Vérifie si l'anneau a un gap"""
        return self.gap_angle > 0
    
    def point_in_gap(self, point: Vector2D) -> bool:
        """Vérifie si un point est dans le gap"""
        if not self.has_gap():
            return False
        
        # Angle du point par rapport au centre
        relative_pos = point - self.position
        angle = math.degrees(math.atan2(relative_pos.y, relative_pos.x))
        angle = (angle + 360) % 360  # Normaliser à [0, 360]
        
        # Angle du gap avec rotation
        gap_start_rotated = (self.gap_start + self.rotation) % 360
        gap_end = (gap_start_rotated + self.gap_angle) % 360
        
        # Vérifier si l'angle est dans le gap
        if gap_start_rotated <= gap_end:
            return gap_start_rotated <= angle <= gap_end
        else:  # Le gap traverse 0°
            return angle >= gap_start_rotated or angle <= gap_end
    
    def collision_with_circle(self, circle_pos: Vector2D, circle_radius: float) -> dict:
        """Détection de collision avec un cercle"""
        distance = self.position.distance_to(circle_pos)
        
        # Vérifier si le cercle est dans la zone de l'anneau
        if distance + circle_radius < self.inner_radius:
            return None  # Complètement à l'intérieur
        
        if distance - circle_radius > self.outer_radius:
            return None  # Complètement à l'extérieur
        
        # Vérifier le gap
        if self.has_gap() and self.point_in_gap(circle_pos):
            return None  # Dans le gap
        
        # Collision détectée
        collision_info = {}
        
        if distance < self.inner_radius + circle_radius:
            # Collision avec le bord intérieur
            normal = (circle_pos - self.position).normalized
            penetration = self.inner_radius + circle_radius - distance
            collision_info = {
                'type': 'inner',
                'normal': normal,
                'penetration': penetration,
                'contact_point': self.position + normal * self.inner_radius
            }
        elif distance + circle_radius > self.outer_radius:
            # Collision avec le bord extérieur
            normal = (self.position - circle_pos).normalized
            penetration = circle_radius + distance - self.outer_radius
            collision_info = {
                'type': 'outer',
                'normal': normal,
                'penetration': penetration,
                'contact_point': self.position + (circle_pos - self.position).normalized * self.outer_radius
            }
        
        return collision_info
    
    def render(self, screen: pygame.Surface):
        """Rendu de l'anneau"""
        if not self.visible:
            return
        
        center = (int(self.position.x), int(self.position.y))
        
        if self.gradient_enabled:
            self._render_gradient_ring(screen, center)
        else:
            self._render_solid_ring(screen, center)
    
    def _render_solid_ring(self, screen: pygame.Surface, center: tuple):
        """Rendu d'un anneau couleur unie"""
        thickness = int(self.outer_radius - self.inner_radius)
        if thickness <= 0:
            return
        
        # Calculer la couleur
        color = self.color
        if self.color_shift_enabled:
            hue = (self.color_phase / 360.0) % 1.0
            color = hsv_to_rgb(hue, 1.0, 1.0)
        
        if not self.has_gap():
            # Anneau complet
            pygame.draw.circle(screen, color, center, int(self.outer_radius), thickness)
        else:
            # Anneau avec gap - dessiner par segments
            self._render_segmented_ring(screen, center, color)
    
    def _render_segmented_ring(self, screen: pygame.Surface, center: tuple, color: tuple):
        """Rendu d'un anneau segmenté avec gap"""
        # Angles en radians
        gap_start_rad = math.radians(self.gap_start + self.rotation)
        gap_end_rad = math.r