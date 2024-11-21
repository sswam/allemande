#!/usr/bin/env python3-allemande

"""
Boilerplate and utilities for simple pygame-based games.
"""

import os
import sys
import logging
from dataclasses import dataclass
from pathlib import Path

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import pygame.mixer as mixer

__version__ = "0.1.0"

logger = logs.get_logger()


@dataclass
class GameConfig:
    """Basic game configuration."""
    width: int = 800
    height: int = 600
    fps: int = 60
    title: str = "Game"
    bg_color: tuple[int, int, int] = (0, 0, 0)


@dataclass
class GameObject:
    """Base class for game objects."""
    x: int = 400
    y: int = 300
    speed: int = 5
    size: int = 40
    color: tuple[int, int, int] = (255, 0, 0)


class GameEngine:
    """Basic game engine with common functionality."""

    def __init__(self, config: GameConfig):
        pygame.init()
        mixer.init()
        self.screen = pygame.display.set_mode((config.width, config.height))
        pygame.display.set_caption(config.title)
        self.clock = pygame.time.Clock()
        self.config = config
        self.sounds: dict[str, mixer.Sound] = {}
        self.running = True

    def load_sound(self, name: str, path: str) -> None:
        """Load a sound effect."""
        self.sounds[name] = mixer.Sound(path)

    def play_sound(self, name: str, volume=1.0) -> None:
        """Play a loaded sound effect."""
        if name in self.sounds:
            sound = self.sounds[name]
            sound.set_volume(volume)
            sound.play()

    def play_music(self, path: str, volume=1.0, loop: bool = True) -> None:
        """Start playing background music."""
        mixer.music.load(path)
        mixer.music.set_volume(volume)
        mixer.music.play(-1 if loop else 0)

    def stop_music(self) -> None:
        """Stop the background music."""
        mixer.music.stop()

    def handle_basic_events(self) -> None:
        """Handle basic events like quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE):
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                self.toggle_music()

    def toggle_music(self) -> None:
        if mixer.music.get_busy():
            mixer.music.pause()
        else:
            mixer.music.unpause()

    def handle_movement(self, obj: GameObject, keys) -> None:
        """Handle WASD movement for an object."""
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            obj.x -= obj.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            obj.x += obj.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            obj.y -= obj.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            obj.y += obj.speed

    def keep_in_bounds(self, obj: GameObject) -> bool:
        """Keep object within screen boundaries."""
        obj.x = max(obj.size // 2, min(self.config.width - obj.size // 2, obj.x))
        obj.y = max(obj.size // 2, min(self.config.height - obj.size // 2, obj.y))

    def draw_rect(self, obj: GameObject) -> None:
        """Draw a rectangular game object."""
        pygame.draw.rect(
            self.screen,
            obj.color,
            (
                obj.x - obj.size // 2,
                obj.y - obj.size // 2,
                obj.size,
                obj.size,
            ),
        )

    def clear_screen(self) -> None:
        """Clear the screen with background color."""
        self.screen.fill(self.config.bg_color)

    def update_display(self) -> None:
        """Update the display and maintain FPS."""
        pygame.display.flip()
        self.clock.tick(self.config.fps)

    def quit(self) -> None:
        """Clean up and quit pygame."""
        pygame.quit()
        sys.exit()
