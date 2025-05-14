import pygame
import sys
import math
import random

# Configuration
WIDTH, HEIGHT = 800, 800
CENTER = pygame.math.Vector2(WIDTH//2, HEIGHT//2)
GRAVITY = pygame.math.Vector2(0, 400)

# Configuration des anneaux
MIN_RADIUS = 100
GAP_RADIUS = 20  # Espace entre les anneaux
NB_ARC = 5  # Moins d'anneaux pour clarifier la vidéo
THICKNESS = 15  # Anneaux plus épais pour meilleure visibilité
GAP_ANGLE = 60
ROTATION_SPEED = 60

# Paramètres pour des rebonds satisfaisants
ELASTICITY = 1.02  # Légèrement super-élastique pour des rebonds plus vifs

class Particle:
    def __init__(self, pos, vel, color, size, life):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
    
    def update(self, dt):
        self.pos += self.vel * dt
        self.life -= dt
        return self.life > 0
    
    def draw(self, screen):
        alpha = int(255 * (self.life / self.max_life))
        color = (*self.color[:3], alpha)
        
        # Create a surface for the particle with alpha
        surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (self.size, self.size), self.size)
        
        screen.blit(surf, (self.pos.x - self.size, self.pos.y - self.size))

class Ball:
    def __init__(self, pos, vel: pygame.math.Vector2, radius=20, color=(255, 255, 255), elasticity=ELASTICITY):
        self.pos = pos
        self.vel = vel
        self.radius = radius
        self.color = color
        self.elasticity = elasticity
        self.collision = False
        self.in_gap = False
        self.hit_flash = 0  # Timer pour le flash lors d'un impact
        self.prev_pos = pos.copy()  # Position précédente pour détecter les rebonds
        self.trail = []  # Pour stocker les positions précédentes
        self.impact_particles = []  # Particules lors des impacts
    
    def update(self, dt, gravity):
        self.prev_pos = self.pos.copy()
        self.vel += gravity * dt
        self.pos += self.vel * dt
        
        # Ajoute la position actuelle à la traînée
        self.trail.append((self.pos.copy(), self.hit_flash > 0))
        
        # Limite la taille de la traînée
        if len(self.trail) > 10:
            self.trail.pop(0)
        
        # Met à jour le timer de flash
        if self.hit_flash > 0:
            self.hit_flash -= dt
        
        # Mise à jour des particules d'impact
        self.impact_particles = [p for p in self.impact_particles if p.update(dt)]
        
        # Réinitialise les états de collision
        self.collision = False
        self.in_gap = False
    
    def create_impact_particles(self, normal):
        """Crée des particules lors d'un impact"""
        impact_point = self.pos - normal * self.radius
        impact_speed = self.vel.length() * 0.2
        
        for _ in range(10):
            # Direction aléatoire autour de la normale réfléchie
            angle = random.uniform(-math.pi/3, math.pi/3)
            rot_normal = pygame.math.Vector2(
                normal.x * math.cos(angle) - normal.y * math.sin(angle),
                normal.x * math.sin(angle) + normal.y * math.cos(angle)
            )
            
            # Vitesse aléatoire
            vel = rot_normal * random.uniform(impact_speed * 0.5, impact_speed * 1.5)
            
            # Couleur blanche avec une teinte de la couleur de la balle
            r, g, b = self.color
            color = (
                min(255, r + 100),
                min(255, g + 100),
                min(255, b + 100),
                255
            )
            
            # Taille et durée de vie aléatoires
            size = random.uniform(2, 5)
            life = random.uniform(0.2, 0.4)
            
            # Ajoute la particule
            self.impact_particles.append(Particle(impact_point, vel, color, size, life))
    
    def draw(self, screen, debug=False):
        # Dessine la traînée
        for i, (pos, is_flash) in enumerate(self.trail):
            alpha = int(150 * (i / len(self.trail)))
            size = self.radius * (0.3 + 0.7 * i / len(self.trail))
            
            # Couleur de traînée (normale ou flash)
            if is_flash:
                trail_color = (255, 255, 255, alpha)
            else:
                trail_color = (*self.color, alpha)
            
            # Crée une surface avec transparence pour la traînée
            trail_surf = pygame.Surface((int(size*2), int(size*2)), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, trail_color, (int(size), int(size)), int(size))
            screen.blit(trail_surf, (pos.x - size, pos.y - size))
        
        # Dessine les particules d'impact
        for particle in self.impact_particles:
            particle.draw(screen)
            
        # Détermine la couleur en fonction de l'état
        draw_color = self.color
        if self.collision:
            draw_color = (255, 100, 100)  # Rouge en cas de collision
        elif self.in_gap:
            draw_color = (100, 255, 100)  # Vert si dans la trouée
        
        # Flash blanc lors d'un impact
        if self.hit_flash > 0:
            flash_color = (
                min(255, draw_color[0] + int(150 * (self.hit_flash / 0.1))),
                min(255, draw_color[1] + int(150 * (self.hit_flash / 0.1))),
                min(255, draw_color[2] + int(150 * (self.hit_flash / 0.1)))
            )
            pygame.draw.circle(screen, flash_color, self.pos, self.radius * 1.1)
        
        # Dessine la balle
        pygame.draw.circle(screen, draw_color, self.pos, self.radius)
        
        # Ajoute un reflet pour donner du volume
        highlight_pos = (self.pos.x - self.radius * 0.3, self.pos.y - self.radius * 0.3)
        highlight_radius = self.radius * 0.4
        highlight_surf = pygame.Surface((highlight_radius*2, highlight_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(highlight_surf, (255, 255, 255, 100), (highlight_radius, highlight_radius), highlight_radius)
        screen.blit(highlight_surf, (highlight_pos[0] - highlight_radius, highlight_pos[1] - highlight_radius))
        
        if debug:
            # Vecteur vitesse (rouge)
            pygame.draw.line(screen, (255, 0, 0), self.pos, self.vel * 0.1 + self.pos, 3)

class Ring:
    def __init__(self, center, outer_radius, thickness, gap_angle=0, rotation_speed=0, color=(255, 100, 100)):
        self.center = center
        self.outer_radius = outer_radius
        self.thickness = thickness
        self.inner_radius = outer_radius - thickness
        self.gap_angle = gap_angle
        self.rotation_speed = rotation_speed
        self.arc_start = 0
        self.color = color
        self.state = "circle"  # "circle", "arc", "disappearing", "gone"
        self.disappear_timer = 1.0  # Durée de l'animation de disparition
        self.particles = []
        self.glow_intensity = 0  # Intensité du halo quand la balle est proche
        
    def update(self, dt, ball_pos=None):
        if self.state == "arc":
            # Mettre à jour la rotation de l'arc
            self.arc_start = (self.arc_start + self.rotation_speed * dt) % 360
            
            # Mise à jour du halo quand la balle est proche
            if ball_pos:
                dist_to_ball = (ball_pos - self.center).length()
                # Intensité basée sur la distance de la balle au bord intérieur
                proximity = max(0, 1 - abs(dist_to_ball - self.inner_radius) / (self.thickness * 2))
                self.glow_intensity = proximity * 0.8  # Max 80% d'intensité
            
        elif self.state == "disappearing":
            # Mettre à jour le timer de disparition
            self.disappear_timer -= dt
            if self.disappear_timer <= 0:
                self.state = "gone"
            
            # Générer des particules pendant la disparition
            if random.random() < 15 * dt:  # Ajuster ce nombre pour plus/moins de particules
                self.create_particle()
        
        # Mettre à jour les particules
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def create_particle(self):
        # Choisir un angle aléatoire
        angle = random.uniform(0, math.pi * 2)
        radius = random.uniform(self.inner_radius, self.outer_radius)
        
        # Position basée sur le centre et l'angle
        pos = (
            self.center.x + math.cos(angle) * radius,
            self.center.y + math.sin(angle) * radius
        )
        
        # Vecteur de vélocité s'éloignant du centre
        dir_vec = pygame.math.Vector2(math.cos(angle), math.sin(angle))
        vel = dir_vec * random.uniform(50, 250)  # Vitesse plus élevée pour des particules plus dynamiques
        
        # Légère variation de couleur
        color_var = 50  # Plus de variation
        base_color = self.color
        color = (
            min(255, max(0, base_color[0] + random.randint(-color_var, color_var))),
            min(255, max(0, base_color[1] + random.randint(-color_var, color_var))),
            min(255, max(0, base_color[2] + random.randint(-color_var, color_var))),
            255
        )
        
        # Taille et durée de vie aléatoires
        size = random.uniform(2, 6)  # Particules plus grosses
        life = random.uniform(0.5, 1.5)
        
        # Créer et ajouter la particule
        self.particles.append(Particle(pos, vel, color, size, life))
    
    def activate(self):
        if self.state == "circle":
            self.state = "arc"
    
    def trigger_disappear(self):
        if self.state == "arc":
            self.state = "disappearing"
            
            # Génère beaucoup de particules immédiatement
            for _ in range(100):  # Plus de particules pour un effet plus spectaculaire
                self.create_particle()
    
    def get_gap_angles(self):
        gap_start = self.arc_start % 360
        gap_end = (self.arc_start + self.gap_angle) % 360
        return gap_start, gap_end
    
    def is_in_gap(self, angle):
        if self.state != "arc" or self.gap_angle == 0:
            return False
            
        gap_start, gap_end = self.get_gap_angles()
        angle = angle % 360
        
        if gap_start <= gap_end:
            return gap_start <= angle <= gap_end
        else:
            return angle >= gap_start or angle <= gap_end
    
    def check_collision(self, ball: Ball):
        if self.state in ["disappearing", "gone"]:
            return False
            
        # Vecteur du centre vers la balle
        to_ball = ball.pos - self.center
        dist = to_ball.length()
        
        # Calcul de l'angle de la balle par rapport au centre
        angle = (-math.degrees(math.atan2(to_ball.y, to_ball.x))) % 360
        
        # Vérifie si la balle traverse la trouée
        if self.state == "arc" and self.is_in_gap(angle) and dist + ball.radius >= self.inner_radius and dist - ball.radius <= self.outer_radius:
            ball.in_gap = True
            return False
        
        # Vérifie si la balle touche la bordure du cercle
        if dist + ball.radius >= self.inner_radius and dist - ball.radius <= self.outer_radius:
            # On simplifie la détection: vérifier séparément les collisions intérieure et extérieure
            
            # Collision avec le bord intérieur
            if abs(dist - self.inner_radius) <= ball.radius:
                # La normale pointe vers l'extérieur (du centre vers la balle)
                normal = to_ball.normalize()
                # Calcul du rebond normal
                dot_product = ball.vel.dot(normal)
                print("dot_product", dot_product, "normal", normal, "ball.vel", ball.vel)
                
                # Reflète la vitesse
                ball.vel = ball.vel - 2 * dot_product * normal * ELASTICITY
                # Effets visuels
                ball.hit_flash = 0.1
                ball.create_impact_particles(normal)
                self.glow_intensity = 0.5
                ball.collision = True
                return True

        return False
    
    def draw(self, screen, debug=False):
        if self.state == "gone":
            # Ne rien dessiner si l'anneau a disparu
            pass
        elif self.state == "circle":
            # Dessine un cercle complet avec effet de halo si activé
            if self.glow_intensity > 0:
                # Dessine un halo autour de l'anneau
                for i in range(5):
                    alpha = int(100 * self.glow_intensity) - i * 20
                    if alpha <= 0:
                        continue
                    glow_color = (*self.color, alpha)
                    
                    # Crée une surface avec transparence
                    outer_glow = pygame.Surface((self.outer_radius*2 + i*4, self.outer_radius*2 + i*4), pygame.SRCALPHA)
                    pygame.draw.circle(outer_glow, glow_color, (outer_glow.get_width()//2, outer_glow.get_height()//2), 
                                      self.outer_radius + i*2, 2)
                    screen.blit(outer_glow, (self.center.x - outer_glow.get_width()//2, self.center.y - outer_glow.get_height()//2))
                    
                    inner_glow = pygame.Surface((self.inner_radius*2 + i*4, self.inner_radius*2 + i*4), pygame.SRCALPHA)
                    pygame.draw.circle(inner_glow, glow_color, (inner_glow.get_width()//2, inner_glow.get_height()//2), 
                                      self.inner_radius - i*2, 2)
                    screen.blit(inner_glow, (self.center.x - inner_glow.get_width()//2, self.center.y - inner_glow.get_height()//2))
            
            # Dessine l'anneau principal
            pygame.draw.circle(screen, self.color, self.center, self.outer_radius, self.thickness)
            
        elif self.state in ["arc", "disappearing"]:
            # Dessine un arc avec trouée
            start_rad = math.radians(self.arc_start + self.gap_angle)
            end_rad = math.radians(self.arc_start + 360)
            
            rect = pygame.Rect(0, 0, self.outer_radius*2, self.outer_radius*2)
            rect.center = self.center
            
            # Ajuster l'alpha si en train de disparaître
            if self.state == "disappearing":
                alpha = int(255 * self.disappear_timer)
                color = (*self.color[:3], alpha)
                
                # Créer une surface avec alpha
                surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.arc(surf, color, 
                               pygame.Rect(0, 0, rect.width, rect.height), 
                               start_rad, end_rad, self.thickness)
                screen.blit(surf, rect.topleft)
            else:
                # Dessine un halo autour de l'arc si activé
                if self.glow_intensity > 0:
                    # Dessine un halo autour de l'arc
                    glow_color = (*self.color, int(100 * self.glow_intensity))
                    glow_surf = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
                    pygame.draw.arc(glow_surf, 
                                   glow_color, 
                                   pygame.Rect(5, 5, rect.width, rect.height), 
                                   start_rad, end_rad, self.thickness + 5)
                    screen.blit(glow_surf, (rect.topleft[0] - 5, rect.topleft[1] - 5))
                
                # Dessine l'arc principal
                pygame.draw.arc(screen, self.color, rect, start_rad, end_rad, self.thickness)
            
            if debug and self.state == "arc":
                # Visualisation de la trouée
                gap_start, gap_end = self.get_gap_angles()
                gap_line_start = self.center + pygame.math.Vector2(
                    math.cos(math.radians(-gap_start)), math.sin(math.radians(-gap_start))
                ) * self.inner_radius
                gap_line_end = self.center + pygame.math.Vector2(
                    math.cos(math.radians(-gap_end)), math.sin(math.radians(-gap_end))
                ) * self.inner_radius
                
                pygame.draw.line(screen, (255, 0, 255), self.center, gap_line_start, 2)
                pygame.draw.line(screen, (255, 0, 255), self.center, gap_line_end, 2)
        
        # Dessine le contour intérieur pour la visualisation
        if self.state != "gone" and debug:
            pygame.draw.circle(screen, (50, 50, 50), self.center, self.inner_radius, 1)
            pygame.draw.circle(screen, (50, 50, 50), self.center, self.outer_radius, 1)
        
        # Dessiner les particules
        for particle in self.particles:
            particle.draw(screen)

# Fonction principale
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Satisfying Bounces")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    
    # Création des anneaux avec des couleurs vives pour TikTok
    rings: list[Ring] = []
    colors = [
        (255, 100, 100),  # Rouge
        (100, 255, 100),  # Vert
        (100, 100, 255),  # Bleu
        (255, 255, 100),  # Jaune
        (255, 100, 255),  # Rose
    ]
    
    for i in range(NB_ARC):
        ring_radius = MIN_RADIUS + i * (THICKNESS + GAP_RADIUS)
        rings.append(Ring(
            CENTER, 
            outer_radius=ring_radius,
            thickness=THICKNESS,
            gap_angle=GAP_ANGLE,
            rotation_speed=ROTATION_SPEED * (1 if i % 2 == 0 else -1),  # Alternance du sens de rotation
            color=colors[i % len(colors)]
        ))

    # Le premier anneau (le plus intérieur) est un arc qui tourne, les autres sont des cercles
    rings[0].state = "arc"
    
    # Initialisation de la balle au centre
    ball = Ball(
        pos=CENTER.copy(),
        vel=pygame.math.Vector2(150, 0),  # Vitesse initiale plus élevée
        radius=20,
        color=(200, 220, 255)  # Bleu clair pour contraste
    )
    
    # États du jeu
    debug_mode = False
    current_level = 0
    game_won = False
    
    running = True
    while running:
        dt = min(clock.tick(60) / 1000.0, 0.1)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Reset game
                    ball.pos = CENTER.copy()
                    ball.vel = pygame.math.Vector2(150, 0)
                    ball.trail = []
                    ball.impact_particles = []
                    ball.hit_flash = 0
                    current_level = 0
                    game_won = False
                    
                    # Réinitialiser les anneaux
                    for i, ring in enumerate(rings):
                        ring.particles = []
                        ring.disappear_timer = 1.0
                        ring.glow_intensity = 0
                        if i == 0:
                            ring.state = "arc"
                        else:
                            ring.state = "circle"
                
                elif event.key == pygame.K_d:
                    # Toggle debug mode
                    debug_mode = not debug_mode
                
                elif event.key == pygame.K_UP:
                    # Impulsion vers le haut
                    ball.vel.y -= 200
                    
                elif event.key == pygame.K_DOWN:
                    # Impulsion vers le bas
                    ball.vel.y += 200
                    
                elif event.key == pygame.K_LEFT:
                    # Impulsion vers la gauche
                    ball.vel.x -= 200
                    
                elif event.key == pygame.K_RIGHT:
                    # Impulsion vers la droite
                    ball.vel.x += 200
        
        # Mettre à jour les anneaux
        for ring in rings:
            ring.update(dt, ball.pos)
        
        # Mettre à jour la balle
        ball.update(dt, GRAVITY)
        
        # Vérifier les collisions et passages de niveaux
        for i, ring in enumerate(rings):
            # Vérifier les collisions
            ring.check_collision(ball)
            
            # Vérifier si la balle passe dans la trouée
            if i == current_level and ring.state == "arc":
                to_ball = ball.pos - ring.center
                angle = (-math.degrees(math.atan2(to_ball.y, to_ball.x))) % 360
                dist = to_ball.length()
                
                # Vérifier si la balle passe à travers la trouée
                in_gap = ring.is_in_gap(angle)
                near_boundary = abs(dist - ring.inner_radius) < ball.radius * 1.5
                
                if in_gap and near_boundary:
                    # La balle passe à travers la trouée
                    ring.trigger_disappear()
                    
                    # Passer au niveau suivant
                    current_level += 1
                    if current_level < len(rings):
                        rings[current_level].activate()
                    else:
                        game_won = True
        
        # Fond avec léger dégradé
        screen.fill((15, 15, 25))
        
        # Dessiner les anneaux du plus grand au plus petit pour l'ordre correct de superposition
        for ring in reversed(rings):
            ring.draw(screen, debug_mode)
        
        # Dessiner la balle
        ball.draw(screen, debug_mode)
        
        # Afficher les informations de jeu
        level_text = f"Niveau: {current_level+1}/{len(rings)}"
        if game_won:
            level_text = "Vous avez gagné! Appuyez sur ESPACE pour recommencer."
        
        level_surface = font.render(level_text, True, (255, 255, 255))
        screen.blit(level_surface, (10, 10))
        
        # Instructions
        controls = [
            "ESPACE: Recommencer le jeu",
            "Flèches: Appliquer une impulsion",
            "D: Mode debug on/off"
        ]
        
        for i, text in enumerate(controls):
            help_surface = font.render(text, True, (200, 200, 200))
            screen.blit(help_surface, (10, HEIGHT - 90 + i * 25))
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()