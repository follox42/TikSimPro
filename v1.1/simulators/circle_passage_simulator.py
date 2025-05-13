import pygame
import math

class ArcCircleSimulator:
    def __init__(self, width=800, height=800):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.running = True

        # Objets du jeu
        self.center = pygame.Vector2(width // 2, height // 2)
        self.circle_radius = 200
        self.ball_radius = 20
        self.ball_pos = self.center + pygame.Vector2(self.circle_radius - 50, 0)
        self.ball_vel = pygame.Vector2(0, 0)
        self.gravity = pygame.Vector2(0, 0.2)

        # Arc
        self.arc_gap_angle = 60  # Degrés
        self.arc_start_angle = 0  # Degrés
        self.arc_speed = 1  # Degrés/frame

    def update(self, dt):
        # Mettre à jour l'arc
        self.arc_start_angle = (self.arc_start_angle + self.arc_speed) % 360

        # Appliquer la gravité
        self.ball_vel += self.gravity
        self.ball_pos += self.ball_vel

        # Collision avec l'anneau (extérieur & intérieur)
        to_center = self.ball_pos - self.center
        dist = to_center.length()

        # Collide extérieur
        if dist + self.ball_radius > self.circle_radius:
            normal = to_center.normalize()
            self.ball_pos = self.center + normal * (self.circle_radius - self.ball_radius)
            self.ball_vel.reflect_ip(normal)
            self.ball_vel *= 0.8

        # Collide intérieur
        inner_radius = self.circle_radius - 10  # Exemple : 30px d'épaisseur d'anneau
        if dist - self.ball_radius < inner_radius:
            normal = to_center.normalize()
            self.ball_pos = self.center + normal * (inner_radius + self.ball_radius)
            self.ball_vel.reflect_ip(normal)
            self.ball_vel *= 0.8


    def draw(self):
        self.screen.fill((30, 30, 30))

        # Cercle principal
        pygame.draw.circle(self.screen, (100, 100, 255), self.center, self.circle_radius, 5)

        # Arc tournant
        start_rad = math.radians(self.arc_start_angle)
        end_rad = math.radians(self.arc_start_angle + 360 - self.arc_gap_angle)
        rect = pygame.Rect(
            self.center.x - self.circle_radius,
            self.center.y - self.circle_radius,
            self.circle_radius * 2,
            self.circle_radius * 2
        )
        pygame.draw.arc(self.screen, (255, 100, 100), rect, start_rad, end_rad, 10)

        # Balle
        pygame.draw.circle(self.screen, (255, 255, 255), self.ball_pos, self.ball_radius)

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

# Utilisation simple :
if __name__ == "__main__":
    sim = ArcCircleSimulator()
    sim.run()
