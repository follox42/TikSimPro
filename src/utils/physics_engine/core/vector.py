# physics_engine/core/vector.py
"""
Classe Vector2D optimisée pour les calculs de physique
"""
import math
from typing import Union, Tuple

class Vector2D:
    """Vecteur 2D avec opérations vectorielles optimisées"""
    
    __slots__ = ['x', 'y']  # Optimisation mémoire
    
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = float(x)
        self.y = float(y)
    
    # Opérateurs mathématiques
    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Vector2D':
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def __rmul__(self, scalar: float) -> 'Vector2D':
        return self.__mul__(scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector2D':
        return Vector2D(self.x / scalar, self.y / scalar)
    
    def __iadd__(self, other: 'Vector2D') -> 'Vector2D':
        self.x += other.x
        self.y += other.y
        return self
    
    def __isub__(self, other: 'Vector2D') -> 'Vector2D':
        self.x -= other.x
        self.y -= other.y
        return self
    
    def __imul__(self, scalar: float) -> 'Vector2D':
        self.x *= scalar
        self.y *= scalar
        return self
    
    def __neg__(self) -> 'Vector2D':
        return Vector2D(-self.x, -self.y)
    
    # Propriétés vectorielles
    @property
    def magnitude(self) -> float:
        """Magnitude (longueur) du vecteur"""
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    @property
    def magnitude_squared(self) -> float:
        """Magnitude au carré (évite sqrt pour optimisation)"""
        return self.x * self.x + self.y * self.y
    
    @property
    def normalized(self) -> 'Vector2D':
        """Vecteur normalisé (longueur 1)"""
        mag = self.magnitude
        if mag == 0:
            return Vector2D(0, 0)
        return Vector2D(self.x / mag, self.y / mag)
    
    def normalize(self) -> 'Vector2D':
        """Normalise ce vecteur (modifie en place)"""
        mag = self.magnitude
        if mag > 0:
            self.x /= mag
            self.y /= mag
        return self
    
    def dot(self, other: 'Vector2D') -> float:
        """Produit scalaire"""
        return self.x * other.x + self.y * other.y
    
    def cross(self, other: 'Vector2D') -> float:
        """Produit vectoriel (scalaire en 2D)"""
        return self.x * other.y - self.y * other.x
    
    def distance_to(self, other: 'Vector2D') -> float:
        """Distance vers un autre vecteur"""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)
    
    def distance_squared_to(self, other: 'Vector2D') -> float:
        """Distance au carré (évite sqrt)"""
        dx = self.x - other.x
        dy = self.y - other.y
        return dx * dx + dy * dy
    
    def angle_to(self, other: 'Vector2D') -> float:
        """Angle vers un autre vecteur (en radians)"""
        return math.atan2(other.y - self.y, other.x - self.x)
    
    def rotate(self, angle: float) -> 'Vector2D':
        """Rotation (radians)"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Vector2D(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )
    
    def reflect(self, normal: 'Vector2D') -> 'Vector2D':
        """Réflexion par rapport à une normale"""
        # v' = v - 2(v·n)n
        return self - 2 * self.dot(normal) * normal
    
    def project_onto(self, other: 'Vector2D') -> 'Vector2D':
        """Projection sur un autre vecteur"""
        other_mag_sq = other.magnitude_squared
        if other_mag_sq == 0:
            return Vector2D(0, 0)
        return other * (self.dot(other) / other_mag_sq)
    
    def lerp(self, other: 'Vector2D', t: float) -> 'Vector2D':
        """Interpolation linéaire"""
        return self + (other - self) * t
    
    def copy(self) -> 'Vector2D':
        """Copie du vecteur"""
        return Vector2D(self.x, self.y)
    
    def tuple(self) -> Tuple[float, float]:
        """Conversion en tuple"""
        return (self.x, self.y)
    
    def __str__(self) -> str:
        return f"Vector2D({self.x:.2f}, {self.y:.2f})"
    
    def __repr__(self) -> str:
        return f"Vector2D({self.x}, {self.y})"