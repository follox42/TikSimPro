# physics_engine/collision/detector.py
"""
Système de détection de collisions vectorielles avancé
"""
import math
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

from ..core.vector import Vector2D
from ..physics.body import PhysicsBody, Circle, Segment, Ring

@dataclass
class CollisionInfo:
    """Information sur une collision"""
    body_a: PhysicsBody
    body_b: PhysicsBody
    contact_point: Vector2D
    normal: Vector2D  # Normale pointant de A vers B
    penetration: float
    collision_type: str  # 'circle-circle', 'circle-segment', etc.
    metadata: Dict = None  # Informations supplémentaires
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class SpatialGrid:
    """Grille spatiale pour optimiser la détection de collisions"""
    
    def __init__(self, world_width: float, world_height: float, cell_size: float = 100.0):
        self.world_width = world_width
        self.world_height = world_height
        self.cell_size = cell_size
        self.cols = int(math.ceil(world_width / cell_size))
        self.rows = int(math.ceil(world_height / cell_size))
        self.grid = {}
        
    def clear(self):
        """Vide la grille"""
        self.grid.clear()
    
    def _get_cell_coords(self, x: float, y: float) -> Tuple[int, int]:
        """Convertit les coordonnées monde en coordonnées de cellule"""
        col = int(x // self.cell_size)
        row = int(y // self.cell_size)
        return (max(0, min(col, self.cols - 1)), max(0, min(row, self.rows - 1)))
    
    def _get_cells_for_body(self, body: PhysicsBody) -> List[Tuple[int, int]]:
        """Retourne toutes les cellules occupées par un corps"""
        min_pos, max_pos = body.get_bounding_box()
        
        min_col, min_row = self._get_cell_coords(min_pos.x, min_pos.y)
        max_col, max_row = self._get_cell_coords(max_pos.x, max_pos.y)
        
        cells = []
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                cells.append((col, row))
        
        return cells
    
    def insert(self, body: PhysicsBody):
        """Insère un corps dans la grille"""
        cells = self._get_cells_for_body(body)
        for cell in cells:
            if cell not in self.grid:
                self.grid[cell] = []
            self.grid[cell].append(body)
    
    def get_potential_collisions(self) -> List[Tuple[PhysicsBody, PhysicsBody]]:
        """Retourne les paires de corps potentiellement en collision"""
        pairs = set()
        
        for cell_bodies in self.grid.values():
            for i in range(len(cell_bodies)):
                for j in range(i + 1, len(cell_bodies)):
                    body_a, body_b = cell_bodies[i], cell_bodies[j]
                    
                    # Éviter les doublons
                    pair = (min(id(body_a), id(body_b)), max(id(body_a), id(body_b)))
                    if pair not in pairs:
                        pairs.add(pair)
                        yield (body_a, body_b)

class CollisionDetector:
    """Détecteur de collisions principal"""
    
    def __init__(self, use_spatial_optimization: bool = True, cell_size: float = 100.0):
        self.use_spatial_optimization = use_spatial_optimization
        self.spatial_grid = None
        self.cell_size = cell_size
        
        # Statistiques
        self.collision_checks = 0
        self.collisions_found = 0
        
    def setup_spatial_grid(self, world_width: float, world_height: float):
        """Configure la grille spatiale"""
        if self.use_spatial_optimization:
            self.spatial_grid = SpatialGrid(world_width, world_height, self.cell_size)
    
    def detect_collisions(self, bodies: List[PhysicsBody]) -> List[CollisionInfo]:
        """Détecte toutes les collisions entre les corps"""
        self.collision_checks = 0
        self.collisions_found = 0
        collisions = []
        
        if self.use_spatial_optimization and self.spatial_grid:
            # Utiliser la grille spatiale
            self.spatial_grid.clear()
            
            # Insérer tous les corps dans la grille
            for body in bodies:
                self.spatial_grid.insert(body)
            
            # Tester les paires potentielles
            for body_a, body_b in self.spatial_grid.get_potential_collisions():
                self.collision_checks += 1
                collision = self._check_collision(body_a, body_b)
                if collision:
                    collisions.append(collision)
                    self.collisions_found += 1
        else:
            # Vérification naïve O(n²)
            for i in range(len(bodies)):
                for j in range(i + 1, len(bodies)):
                    self.collision_checks += 1
                    body_a, body_b = bodies[i], bodies[j]
                    
                    # Skip si les deux sont statiques
                    if body_a.static and body_b.static:
                        continue
                    
                    collision = self._check_collision(body_a, body_b)
                    if collision:
                        collisions.append(collision)
                        self.collisions_found += 1
        
        return collisions
    
    def _check_collision(self, body_a: PhysicsBody, body_b: PhysicsBody) -> Optional[CollisionInfo]:
        """Vérifie la collision entre deux corps spécifiques"""
        # Détermine le type de collision
        type_a = type(body_a).__name__
        type_b = type(body_b).__name__
        
        # Organiser pour avoir des fonctions symétriques
        if (type_a, type_b) in [('Circle', 'Circle')]:
            return self._circle_circle_collision(body_a, body_b)
        elif (type_a, type_b) == ('Circle', 'Segment') or (type_a, type_b) == ('Segment', 'Circle'):
            circle = body_a if type_a == 'Circle' else body_b
            segment = body_a if type_a == 'Segment' else body_b
            return self._circle_segment_collision(circle, segment)
        elif (type_a, type_b) == ('Circle', 'Ring') or (type_a, type_b) == ('Ring', 'Circle'):
            circle = body_a if type_a == 'Circle' else body_b
            ring = body_a if type_a == 'Ring' else body_b
            return self._circle_ring_collision(circle, ring)
        
        return None
    
    def _circle_circle_collision(self, circle_a: Circle, circle_b: Circle) -> Optional[CollisionInfo]:
        """Collision entre deux cercles"""
        distance = circle_a.position.distance_to(circle_b.position)
        radius_sum = circle_a.radius + circle_b.radius
        
        if distance < radius_sum and distance > 0:
            # Collision détectée
            normal = (circle_b.position - circle_a.position).normalized
            penetration = radius_sum - distance
            contact_point = circle_a.position + normal * circle_a.radius
            
            return CollisionInfo(
                body_a=circle_a,
                body_b=circle_b,
                contact_point=contact_point,
                normal=normal,
                penetration=penetration,
                collision_type='circle-circle'
            )
        
        return None
    
    def _circle_segment_collision(self, circle: Circle, segment: Segment) -> Optional[CollisionInfo]:
        """Collision entre un cercle et un segment"""
        # Trouver le point le plus proche sur le segment
        closest_point = segment.closest_point_on_segment(circle.position)
        distance = circle.position.distance_to(closest_point)
        
        if distance < circle.radius + segment.thickness / 2:
            # Collision détectée
            if distance > 0:
                normal = (circle.position - closest_point).normalized
            else:
                # Si le centre du cercle est exactement sur le segment
                normal = segment.get_normal()
            
            penetration = circle.radius + segment.thickness / 2 - distance
            
            return CollisionInfo(
                body_a=circle,
                body_b=segment,
                contact_point=closest_point,
                normal=normal,
                penetration=penetration,
                collision_type='circle-segment'
            )
        
        return None
    
    def _circle_ring_collision(self, circle: Circle, ring: Ring) -> Optional[CollisionInfo]:
        """Collision entre un cercle et un anneau"""
        collision_data = ring.collision_with_circle(circle.position, circle.radius)
        
        if collision_data:
            return CollisionInfo(
                body_a=circle,
                body_b=ring,
                contact_point=collision_data['contact_point'],
                normal=collision_data['normal'],
                penetration=collision_data['penetration'],
                collision_type='circle-ring',
                metadata={'ring_collision_type': collision_data['type']}
            )
        
        return None

class ContinuousCollisionDetector:
    """Détecteur de collisions continues (CCD) pour éviter le tunneling"""
    
    def __init__(self):
        self.max_substeps = 4
        self.min_separation_distance = 0.1
    
    def detect_continuous_collision(self, body_a: PhysicsBody, body_b: PhysicsBody, dt: float) -> Optional[CollisionInfo]:
        """Détecte les collisions continues entre deux corps en mouvement"""
        if isinstance(body_a, Circle) and isinstance(body_b, Circle):
            return self._circle_circle_ccd(body_a, body_b, dt)
        
        return None
    
    def _circle_circle_ccd(self, circle_a: Circle, circle_b: Circle, dt: float) -> Optional[CollisionInfo]:
        """CCD pour deux cercles"""
        # Calculer les positions finales
        final_pos_a = circle_a.position + circle_a.velocity * dt
        final_pos_b = circle_b.position + circle_b.velocity * dt
        
        # Vérifier la collision à t=0
        initial_distance = circle_a.position.distance_to(circle_b.position)
        radius_sum = circle_a.radius + circle_b.radius
        
        if initial_distance < radius_sum:
            # Déjà en collision
            return None
        
        # Vérifier la collision à t=dt
        final_distance = final_pos_a.distance_to(final_pos_b)
        
        if final_distance >= radius_sum:
            # Pas de collision
            return None
        
        # Il y a une collision quelque part dans l'intervalle
        # Utiliser la recherche dichotomique pour trouver le temps de collision
        t_collision = self._binary_search_collision_time(circle_a, circle_b, dt, radius_sum)
        
        if t_collision is not None:
            # Calculer les positions au moment de la collision
            pos_a_collision = circle_a.position + circle_a.velocity * t_collision
            pos_b_collision = circle_b.position + circle_b.velocity * t_collision
            
            normal = (pos_b_collision - pos_a_collision).normalized
            contact_point = pos_a_collision + normal * circle_a.radius
            
            return CollisionInfo(
                body_a=circle_a,
                body_b=circle_b,
                contact_point=contact_point,
                normal=normal,
                penetration=0.0,  # Collision exacte
                collision_type='circle-circle-ccd',
                metadata={'collision_time': t_collision}
            )
        
        return None
    
    def _binary_search_collision_time(self, circle_a: Circle, circle_b: Circle, dt: float, radius_sum: float) -> Optional[float]:
        """Recherche dichotomique du temps de collision"""
        t_min = 0.0
        t_max = dt
        tolerance = 1e-6
        max_iterations = 20
        
        for _ in range(max_iterations):
            t_mid = (t_min + t_max) / 2
            
            pos_a = circle_a.position + circle_a.velocity * t_mid
            pos_b = circle_b.position + circle_b.velocity * t_mid
            distance = pos_a.distance_to(pos_b)
            
            if abs(distance - radius_sum) < tolerance:
                return t_mid
            
            if distance > radius_sum:
                t_min = t_mid
            else:
                t_max = t_mid
            
            if t_max - t_min < tolerance:
                break
        
        return (t_min + t_max) / 2

class QuadTree:
    """Quadtree pour optimisation spatiale avancée"""
    
    def __init__(self, bounds: Tuple[float, float, float, float], max_objects: int = 10, max_levels: int = 5, level: int = 0):
        self.bounds = bounds  # (x, y, width, height)
        self.max_objects = max_objects
        self.max_levels = max_levels
        self.level = level
        self.objects = []
        self.nodes = []
    
    def clear(self):
        """Vide le quadtree"""
        self.objects.clear()
        for node in self.nodes:
            node.clear()
        self.nodes.clear()
    
    def split(self):
        """Divise le nœud en 4 sous-nœuds"""
        x, y, width, height = self.bounds
        sub_width = width / 2
        sub_height = height / 2
        
        # Créer les 4 quadrants
        self.nodes = [
            QuadTree((x + sub_width, y, sub_width, sub_height), self.max_objects, self.max_levels, self.level + 1),  # NE
            QuadTree((x, y, sub_width, sub_height), self.max_objects, self.max_levels, self.level + 1),              # NW
            QuadTree((x, y + sub_height, sub_width, sub_height), self.max_objects, self.max_levels, self.level + 1), # SW
            QuadTree((x + sub_width, y + sub_height, sub_width, sub_height), self.max_objects, self.max_levels, self.level + 1)  # SE
        ]
    
    def get_index(self, body: PhysicsBody) -> int:
        """Détermine dans quel quadrant placer l'objet"""
        x, y, width, height = self.bounds
        vertical_midpoint = x + width / 2
        horizontal_midpoint = y + height / 2
        
        min_pos, max_pos = body.get_bounding_box()
        
        # L'objet peut tenir complètement dans le quadrant supérieur
        top_quadrant = min_pos.y < horizontal_midpoint and max_pos.y < horizontal_midpoint
        # L'objet peut tenir complètement dans le quadrant inférieur
        bottom_quadrant = min_pos.y > horizontal_midpoint
        
        # L'objet peut tenir complètement dans le quadrant gauche
        if min_pos.x < vertical_midpoint and max_pos.x < vertical_midpoint:
            if top_quadrant:
                return 1  # NW
            elif bottom_quadrant:
                return 2  # SW
        # L'objet peut tenir complètement dans le quadrant droit
        elif min_pos.x > vertical_midpoint:
            if top_quadrant:
                return 0  # NE
            elif bottom_quadrant:
                return 3  # SE
        
        return -1  # L'objet ne peut pas tenir dans un quadrant spécifique
    
    def insert(self, body: PhysicsBody):
        """Insère un objet dans le quadtree"""
        if self.nodes:
            index = self.get_index(body)
            if index != -1:
                self.nodes[index].insert(body)
                return
        
        self.objects.append(body)
        
        if len(self.objects) > self.max_objects and self.level < self.max_levels:
            if not self.nodes:
                self.split()
            
            i = 0
            while i < len(self.objects):
                index = self.get_index(self.objects[i])
                if index != -1:
                    obj = self.objects.pop(i)
                    self.nodes[index].insert(obj)
                else:
                    i += 1
    
    def retrieve(self, return_objects: List[PhysicsBody], body: PhysicsBody):
        """Récupère tous les objets qui pourraient entrer en collision avec l'objet donné"""
        index = self.get_index(body)
        if index != -1 and self.nodes:
            self.nodes[index].retrieve(return_objects, body)
        
        return_objects.extend(self.objects)