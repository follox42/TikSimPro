# physics_engine/core/utils.py
"""
Utilitaires pour le moteur de physique
"""
import math
import random
from typing import Tuple, List
from .vector import Vector2D

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Limite une valeur entre min et max"""
    return max(min_val, min(max_val, value))

def lerp(a: float, b: float, t: float) -> float:
    """Interpolation linéaire"""
    return a + (b - a) * t

def map_range(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """Mappe une valeur d'une plage vers une autre"""
    return out_min + (out_max - out_min) * ((value - in_min) / (in_max - in_min))

def random_vector(min_mag: float = 0, max_mag: float = 1) -> Vector2D:
    """Génère un vecteur aléatoire"""
    angle = random.uniform(0, 2 * math.pi)
    magnitude = random.uniform(min_mag, max_mag)
    return Vector2D(math.cos(angle) * magnitude, math.sin(angle) * magnitude)

def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    """Conversion HSV vers RGB"""
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))

def rainbow_color(t: float, saturation: float = 1.0, value: float = 1.0) -> Tuple[int, int, int]:
    """Génère une couleur arc-en-ciel"""
    hue = (t % 1.0)
    return hsv_to_rgb(hue, saturation, value)

def distance_point_to_line(point: Vector2D, line_start: Vector2D, line_end: Vector2D) -> float:
    """Distance d'un point à une ligne"""
    line_vec = line_end - line_start
    point_vec = point - line_start
    
    if line_vec.magnitude_squared == 0:
        return point_vec.magnitude
    
    t = max(0, min(1, point_vec.dot(line_vec) / line_vec.magnitude_squared))
    projection = line_start + line_vec * t
    return point.distance_to(projection)

def polygon_contains_point(polygon: List[Vector2D], point: Vector2D) -> bool:
    """Test si un point est dans un polygone (ray casting)"""
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0].x, polygon[0].y
    
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n].x, polygon[i % n].y
        
        if point.y > min(p1y, p2y):
            if point.y <= max(p1y, p2y):
                if point.x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (point.y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or point.x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside

def smooth_step(edge0: float, edge1: float, x: float) -> float:
    """Fonction de lissage"""
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def ease_in_out_quad(t: float) -> float:
    """Fonction d'easing quadratique"""
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t