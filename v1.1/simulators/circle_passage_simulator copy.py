# arc_circle_simulator.py
import pygame
import math
from circle import Circle
from ring import Ring

class ArcCircleSimulator:
    def __init__(self, width=800, height=800):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Arc Circle Simulator")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Couleurs
        self.bg_color = (30, 30, 30)
        self.ring_color = (255, 100, 100)
        self.ball_color = (255, 255, 255)
        
        # Centre
        self.center = pygame.Vector2(width // 2, height // 2)
        
        # Créer les éléments
        self.elements = {}
        
        # Créer l'anneau
        self.elements['ring'] = Ring(self.center, 200, 10, self.ring_color)
        self.elements['ring'].immovable = True

        # Créer la balle
        ring = self.elements['ring']
        ball_start_pos = self.center + pygame.Vector2(0, ring.inner_radius * 0.5)
        self.elements['ball'] = Circle(ball_start_pos, 20, self.ball_color)
        self.elements['ball'].velocity = pygame.Vector2(2, 1)
        
        # Force de gravité
        self.gravity = pygame.Vector2(0, 981)
        
        # Variable pour suivre si l'anneau est visible
        self.ring_visible = True
    
    def update(self, dt):
        # Si l'anneau n'est plus visible, ne rien faire
        if not self.ring_visible:
            # Juste mettre à jour la balle pour qu'elle continue de bouger
            ball = self.elements['ball']
            ball.apply_force(self.gravity)
            ball.update(dt)
            return
        
        # Mettre à jour l'angle de l'arc de l'anneau
        ring = self.elements['ring']
        ring.arc_start_angle = (ring.arc_start_angle + 1) % 360
        
        # Récupérer les éléments
        ball = self.elements['ball']
        
        # Appliquer la gravité à la balle
        ball.apply_force(self.gravity)
        ball.apply_force(pygame.Vector2(200, 0))
        
        # Mettre à jour la position des éléments
        for element in self.elements.values():
            element.update(dt)
        
        # Collision avec l'anneau
        ring.resolve_collision(ball)
        
        # Vérifier si la balle a traversé la trouée et est sortie de l'anneau
        ball_to_center = ball.center - self.center
        distance = ball_to_center.length()
        
        # Si la balle est dans la trouée et a dépassé le rayon extérieur
        if ring.is_in_arc_gap(ball.center) and distance > ring.outer_radius + ball.radius:
            # Faire disparaître l'anneau
            self.ring_visible = False
    
    def draw(self):
        self.screen.fill(self.bg_color)
        
        # Dessiner l'anneau avec sa trouée (seulement s'il est visible)
        if self.ring_visible:
            self.elements['ring'].draw(self.screen, self.bg_color)
        
        # Dessiner la balle
        self.elements['ball'].draw(self.screen)
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            self.update(dt)
            self.draw()
        
        pygame.quit()

# Utilisation
if __name__ == "__main__":
    sim = ArcCircleSimulator()
    sim.run()