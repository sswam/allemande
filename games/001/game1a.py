#!/usr/bin/env python3-allemande

"""
A simple pygame animation with WASD controls for movement.
"""

import sys
import logging
from dataclasses import dataclass

import pygame

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


@dataclass
class Player:
    """Represents the player character."""
    x: int = 400
    y: int = 300
    speed: int = 5
    size: int = 40
    color: tuple[int, int, int] = (255, 0, 0)


def handle_movement(player: Player, keys) -> None:
    """Handle player movement based on keyboard input."""
    if keys[pygame.K_a]:  # left
        player.x -= player.speed
    if keys[pygame.K_d]:  # right
        player.x += player.speed
    if keys[pygame.K_w]:  # up
        player.y -= player.speed
    if keys[pygame.K_s]:  # down
        player.y += player.speed


def keep_in_bounds(player: Player, width: int, height: int) -> bool:
    """Ensure player stays within screen boundaries."""
    radius = player.size // 2
    hit_boundary = False
    if player.x < radius:
        player.x = radius
        hit_boundary = True
    elif player.x > width - radius:
        player.x = width - radius
        hit_boundary = True
    if player.y < radius:
        player.y = radius
        hit_boundary = True
    elif player.y > height - radius:
        player.y = height - radius
        hit_boundary = True
    return hit_boundary


def game1(width: int = 800, height: int = 600, fps: int = 60) -> None:
    """Run the game loop with a movable square."""
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()
    player = Player()

    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # Update game state
        keys = pygame.key.get_pressed()
        handle_movement(player, keys)
        keep_in_bounds(player, width, height)

        # Draw
        screen.fill((0, 0, 0))  # black background
        pygame.draw.rect(
            screen,
            player.color,
            (
                player.x - player.size // 2,
                player.y - player.size // 2,
                player.size,
                player.size,
            ),
        )
        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("--width", type=int, help="screen width in pixels")
    arg("--height", type=int, help="screen height in pixels")
    arg("--fps", type=int, help="frames per second limit")


if __name__ == "__main__":
    main.go(game1, setup_args)
