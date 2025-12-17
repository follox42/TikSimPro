# src/utils/video/particles.py
"""
Particle system for visual effects on collisions.
"""

import pygame
import math
import random
from typing import Tuple, List


class SimpleParticle:
    """Lightweight particle for visual effects"""

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 color: Tuple[int, int, int], size: float = 3.0,
                 life: float = 0.5, gravity: float = 800):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.gravity = gravity

    def update(self, dt: float) -> bool:
        """Update particle state. Returns True if still alive."""
        self.life -= dt

        # Apply gravity
        self.vy += self.gravity * dt

        # Move particle
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Shrink over time
        self.size = max(0.5, self.size * (1 - dt * 3))

        return self.life > 0

    def render(self, surface: pygame.Surface):
        """Render particle with fade effect"""
        if self.life <= 0:
            return

        # Calculate fade based on remaining life
        fade = self.life / self.max_life

        # Apply fade to color
        col = (
            int(self.color[0] * fade),
            int(self.color[1] * fade),
            int(self.color[2] * fade)
        )

        # Draw particle
        pos = (int(self.x), int(self.y))
        radius = max(1, int(self.size))
        pygame.draw.circle(surface, col, pos, radius)


class ParticleSpawner:
    """Utility class to spawn particles on collisions"""

    @staticmethod
    def spawn_collision_particles(
        x: float, y: float,
        normal_angle: float,
        color: Tuple[int, int, int],
        count: int = 10,
        speed_range: Tuple[float, float] = (150, 400),
        size_range: Tuple[float, float] = (2, 5),
        life_range: Tuple[float, float] = (0.3, 0.6),
        gravity: float = 800,
        spread: float = 0.8
    ) -> List[SimpleParticle]:
        """
        Spawn particles spreading from collision point.

        Args:
            x, y: Collision position
            normal_angle: Angle of the collision normal (radians)
            color: Base color of particles
            count: Number of particles to spawn
            speed_range: Min/max speed of particles
            size_range: Min/max size of particles
            life_range: Min/max lifetime of particles
            gravity: Gravity applied to particles
            spread: Angular spread (radians)
        """
        particles = []

        for _ in range(count):
            # Direction opposite to normal with spread
            angle = normal_angle + math.pi + random.uniform(-spread, spread)
            speed = random.uniform(*speed_range)

            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            size = random.uniform(*size_range)
            life = random.uniform(*life_range)

            # Add color variation for visual interest
            r = min(255, max(0, color[0] + random.randint(-30, 50)))
            g = min(255, max(0, color[1] + random.randint(-30, 50)))
            b = min(255, max(0, color[2] + random.randint(-30, 50)))

            particles.append(SimpleParticle(
                x, y, vx, vy, (r, g, b), size, life, gravity
            ))

        return particles

    @staticmethod
    def spawn_celebration_particles(
        x: float, y: float,
        color: Tuple[int, int, int],
        count: int = 20
    ) -> List[SimpleParticle]:
        """
        Spawn celebration particles in all directions.
        Used for special events like passing through gaps.
        """
        particles = []

        for _ in range(count):
            # Radial explosion
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(200, 600)

            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 200  # Bias upward

            size = random.uniform(3, 7)
            life = random.uniform(0.5, 1.0)

            # Bright varied colors
            r = min(255, max(0, color[0] + random.randint(-20, 80)))
            g = min(255, max(0, color[1] + random.randint(-20, 80)))
            b = min(255, max(0, color[2] + random.randint(-20, 80)))

            particles.append(SimpleParticle(
                x, y, vx, vy, (r, g, b), size, life, gravity=600
            ))

        return particles
