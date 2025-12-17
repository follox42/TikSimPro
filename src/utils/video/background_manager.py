# src/utils/video/background_manager.py
"""
Background manager with multiple modes for satisfying visuals.
"""

import pygame
import colorsys
import math
from enum import Enum
from typing import Dict, Any, Tuple, Optional, List
import random


class BackgroundMode(Enum):
    """Available background modes"""
    ANIMATED_GRADIENT = "animated_gradient"
    SOLID_PASTEL = "solid_pastel"
    STATIC_GRADIENT = "static_gradient"
    BLACK = "black"  # Default fallback


class BackgroundManager:
    """
    Manages background rendering with multiple satisfying modes.
    """

    # Predefined pastel palette
    PASTEL_COLORS = [
        (255, 179, 186),  # Rose
        (255, 223, 186),  # Peach
        (255, 255, 186),  # Yellow
        (186, 255, 201),  # Mint green
        (186, 225, 255),  # Sky blue
        (232, 186, 255),  # Lavender
        (255, 186, 230),  # Pink
        (201, 201, 255),  # Periwinkle
    ]

    # Gradient presets (top_color, bottom_color)
    GRADIENT_PRESETS = [
        ((30, 30, 60), (10, 10, 30)),      # Dark blue
        ((40, 20, 40), (15, 10, 25)),      # Dark purple
        ((20, 40, 40), (10, 20, 25)),      # Dark teal
        ((50, 30, 20), (20, 15, 10)),      # Dark warm
        ((25, 25, 35), (10, 10, 15)),      # Neutral dark
    ]

    def __init__(self, width: int, height: int, mode: BackgroundMode = BackgroundMode.BLACK):
        self.width = width
        self.height = height
        self.mode = mode

        # For SOLID_PASTEL mode
        self.pastel_color: Optional[Tuple[int, int, int]] = None

        # For STATIC_GRADIENT mode
        self.gradient_top: Tuple[int, int, int] = (30, 30, 60)
        self.gradient_bottom: Tuple[int, int, int] = (10, 10, 30)

        # For ANIMATED_GRADIENT mode
        self.animation_speed = 30  # Degrees per second
        self.current_hue = random.uniform(0, 360)
        self.saturation = 0.3  # Low saturation for pleasant look
        self.value = 0.15  # Low value for dark but colorful background

        # Pre-rendered gradient surface (for static gradient)
        self._gradient_surface: Optional[pygame.Surface] = None

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure background based on mode.

        Config options:
        - mode: BackgroundMode or string
        - pastel_color: (r, g, b) for SOLID_PASTEL
        - gradient_top: (r, g, b) for STATIC_GRADIENT
        - gradient_bottom: (r, g, b) for STATIC_GRADIENT
        - animation_speed: float for ANIMATED_GRADIENT
        - saturation: float (0-1) for ANIMATED_GRADIENT
        - value: float (0-1) for ANIMATED_GRADIENT
        """
        # Set mode
        mode = config.get("mode", self.mode)
        if isinstance(mode, str):
            try:
                self.mode = BackgroundMode(mode)
            except ValueError:
                self.mode = BackgroundMode.BLACK
        else:
            self.mode = mode

        # Mode-specific config
        if self.mode == BackgroundMode.SOLID_PASTEL:
            self.pastel_color = config.get("pastel_color")
            if not self.pastel_color:
                # Random pastel from palette
                self.pastel_color = random.choice(self.PASTEL_COLORS)

        elif self.mode == BackgroundMode.STATIC_GRADIENT:
            if "gradient_top" in config and "gradient_bottom" in config:
                self.gradient_top = config["gradient_top"]
                self.gradient_bottom = config["gradient_bottom"]
            else:
                # Random preset
                preset = random.choice(self.GRADIENT_PRESETS)
                self.gradient_top, self.gradient_bottom = preset
            # Pre-render gradient
            self._prerender_gradient()

        elif self.mode == BackgroundMode.ANIMATED_GRADIENT:
            self.animation_speed = config.get("animation_speed", 30)
            self.saturation = config.get("saturation", 0.3)
            self.value = config.get("value", 0.15)
            self.current_hue = config.get("start_hue", random.uniform(0, 360))

    def _prerender_gradient(self) -> None:
        """Pre-render static gradient for performance"""
        self._gradient_surface = pygame.Surface((self.width, self.height))

        for y in range(self.height):
            # Linear interpolation
            t = y / self.height
            r = int(self.gradient_top[0] * (1 - t) + self.gradient_bottom[0] * t)
            g = int(self.gradient_top[1] * (1 - t) + self.gradient_bottom[1] * t)
            b = int(self.gradient_top[2] * (1 - t) + self.gradient_bottom[2] * t)

            pygame.draw.line(self._gradient_surface, (r, g, b), (0, y), (self.width, y))

    def render(self, surface: pygame.Surface, time_elapsed: float = 0.0) -> None:
        """
        Render background to surface.

        Args:
            surface: Pygame surface to render to
            time_elapsed: Time since start (seconds) for animations
        """
        if self.mode == BackgroundMode.ANIMATED_GRADIENT:
            self._render_animated_gradient(surface, time_elapsed)
        elif self.mode == BackgroundMode.SOLID_PASTEL:
            self._render_solid_pastel(surface)
        elif self.mode == BackgroundMode.STATIC_GRADIENT:
            self._render_static_gradient(surface)
        else:
            # Default black
            surface.fill((0, 0, 0))

    def _render_animated_gradient(self, surface: pygame.Surface, time_elapsed: float) -> None:
        """
        Render smooth color animation - satisfying style.
        Creates a vertical gradient that shifts colors over time.
        """
        # Update hue based on time
        current_hue = (self.current_hue + self.animation_speed * time_elapsed) % 360

        # Create complementary hue for gradient bottom
        bottom_hue = (current_hue + 30) % 360  # Slight hue shift

        # Convert HSV to RGB
        r1, g1, b1 = colorsys.hsv_to_rgb(current_hue / 360, self.saturation, self.value)
        r2, g2, b2 = colorsys.hsv_to_rgb(bottom_hue / 360, self.saturation * 0.8, self.value * 0.6)

        top_color = (int(r1 * 255), int(g1 * 255), int(b1 * 255))
        bottom_color = (int(r2 * 255), int(g2 * 255), int(b2 * 255))

        # Render gradient (optimized: fewer lines for better performance)
        step = 4  # Render every 4 pixels
        for y in range(0, self.height, step):
            t = y / self.height
            r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
            g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
            b = int(top_color[2] * (1 - t) + bottom_color[2] * t)

            pygame.draw.rect(surface, (r, g, b), (0, y, self.width, step))

    def _render_solid_pastel(self, surface: pygame.Surface) -> None:
        """Render single pleasant pastel color"""
        if self.pastel_color:
            # Darken pastel for background (keep it subtle)
            darkened = (
                self.pastel_color[0] // 8,
                self.pastel_color[1] // 8,
                self.pastel_color[2] // 8
            )
            surface.fill(darkened)
        else:
            surface.fill((20, 20, 25))

    def _render_static_gradient(self, surface: pygame.Surface) -> None:
        """Render pre-rendered static gradient"""
        if self._gradient_surface:
            surface.blit(self._gradient_surface, (0, 0))
        else:
            # Fallback: render on the fly
            self._prerender_gradient()
            if self._gradient_surface:
                surface.blit(self._gradient_surface, (0, 0))
            else:
                surface.fill((0, 0, 0))

    @classmethod
    def random_mode(cls) -> BackgroundMode:
        """Get a random background mode (excluding BLACK)"""
        modes = [
            BackgroundMode.ANIMATED_GRADIENT,
            BackgroundMode.SOLID_PASTEL,
            BackgroundMode.STATIC_GRADIENT
        ]
        return random.choice(modes)

    @classmethod
    def create_random(cls, width: int, height: int) -> 'BackgroundManager':
        """Create a BackgroundManager with random mode and settings"""
        mode = cls.random_mode()
        manager = cls(width, height, mode)
        manager.configure({"mode": mode})
        return manager
