import pygame
import sys, math

# Configuration
WIDTH, HEIGHT = 800, 800
CENTER = pygame.math.Vector2(WIDTH//2, HEIGHT//2)
OUTER_RADIUS = 200
THICKNESS = 10
INNER_RADIUS = OUTER_RADIUS - THICKNESS
ARC_GAP_ANGLE = 60  # degrees gap
ARC_START_ANGLE = 0  # initial
BALL_RADIUS = 20
BALL_COLOR = (255, 255, 255)
BALL_POS = CENTER + pygame.math.Vector2(0, INNER_RADIUS*0.5)
BALL_VEL = pygame.math.Vector2(200, -150)
GRAVITY = pygame.math.Vector2(0, 981)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

arc_start = ARC_START_ANGLE

while True:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Met à jour la position de l'arc
    arc_start = (arc_start + 60 * dt) % 360
    start_rad = math.radians(arc_start + ARC_GAP_ANGLE)
    end_rad   = math.radians(arc_start + 360)

    # Applique la physique
    #BALL_VEL += GRAVITY * dt
    #BALL_POS += BALL_VEL * dt

    # Collision
    to_ball = BALL_POS - CENTER
    dist = to_ball.length()
    angle = (math.degrees(math.atan2(to_ball.y, to_ball.x)) + 360) % 360

    # Détection de la trouée
    gap_start = arc_start % 360
    gap_end   = (gap_start + ARC_GAP_ANGLE) % 360
    def in_gap(a):
        if gap_start < gap_end:
            return gap_start <= a <= gap_end
        return a >= gap_start or a <= gap_end

    normal = None
    tangent = None
    collision_point = None

    # Rebond intérieur
    if dist + BALL_RADIUS <= INNER_RADIUS:
        normal = (-to_ball).normalize()
        tangent = pygame.math.Vector2(-normal.y, normal.x)
        collision_point = CENTER + (-normal) * INNER_RADIUS

        v_norm = BALL_VEL.dot(normal) * normal
        v_tan = BALL_VEL.dot(tangent) * tangent

        BALL_VEL = v_tan - v_norm
        BALL_POS = CENTER + (-normal) * (INNER_RADIUS + BALL_RADIUS + 1)

    # Dessin
    screen.fill((30,30,30))
    # Draw ring arc
    rect = pygame.Rect(0,0, OUTER_RADIUS*2, OUTER_RADIUS*2)
    rect.center = CENTER
    pygame.draw.arc(screen, (255,100,100), rect, start_rad, end_rad, THICKNESS)

    # ---DEBUG---
    # velocité
    pygame.draw.line(screen, (255,0,0), BALL_POS, BALL_POS + BALL_VEL, 3)  # velocité en rouge

    # normal
    Vnormal = (-to_ball)
    print(to_ball)
    print(Vnormal)
    Vtangent = pygame.math.Vector2(-Vnormal.y, Vnormal.x)
    pygame.draw.line(screen, (0,255,0), CENTER, Vnormal, 3)  # vecteur normal en vert

    # scale for drawing
    pygame.draw.line(screen, (0,0,255), CENTER, BALL_POS + Vtangent * (BALL_POS.y-CENTER.y), 3)  # vecteur tangente en bleu

    pygame.draw.line(screen, (0,0,255), CENTER, BALL_POS + Vtangent * (BALL_POS.y-CENTER.y), 3)  # tangente en bleu

    # Draw ball
    pygame.draw.circle(screen, BALL_COLOR, BALL_POS, BALL_RADIUS)

    pygame.display.flip()