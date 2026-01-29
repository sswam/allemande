#!/usr/bin/env python3-allemande

"""
Colour test program using pygame to display gradients for monitor calibration.
"""

import sys
import pygame
from pygame.locals import *

from ally import main, logs  # type: ignore

logger = logs.get_logger()


def create_gradient_surface(width: int, height: int, color_func) -> pygame.Surface:
    """Create a surface with a horizontal gradient using the given color function."""
    surface = pygame.Surface((width, height))
    for x in range(width):
        color = color_func(x, width)
        pygame.draw.line(surface, color, (x, 0), (x, height - 1))
    return surface


def grey_gradient(x: int, width: int) -> tuple[int, int, int]:
    """Grey gradient from black to white."""
    value = int(255 * x / (width - 1))
    return (value, value, value)


def red_gradient(x: int, width: int) -> tuple[int, int, int]:
    """Red gradient from black to red."""
    value = int(255 * x / (width - 1))
    return (value, 0, 0)


def green_gradient(x: int, width: int) -> tuple[int, int, int]:
    """Green gradient from black to green."""
    value = int(255 * x / (width - 1))
    return (0, value, 0)


def blue_gradient(x: int, width: int) -> tuple[int, int, int]:
    """Blue gradient from black to blue."""
    value = int(255 * x / (width - 1))
    return (0, 0, value)


def rainbow_gradient(x: int, width: int) -> tuple[int, int, int]:
    """Rainbow gradient for additional testing."""
    hue = int(360 * x / (width - 1))
    return pygame.Color.from_hsva(hue, 100, 100, 100)


def colour_test(istream, ostream) -> None:
    """Run the colour test in fullscreen mode."""
    pygame.init()
    display = pygame.display.set_mode((0, 0), FULLSCREEN)
    width, height = display.get_size()
    pygame.display.set_caption("Colour Test")

    modes = [
        ("Grey", grey_gradient),
        ("Red", red_gradient),
        ("Green", green_gradient),
        ("Blue", blue_gradient),
        ("Rainbow", rainbow_gradient),
    ]
    current_mode = 0

    logger.info("Colour test started. Press SPACE to cycle modes, ESC to quit.")

    running = True
    while running:
        display.fill((0, 0, 0))
        name, func = modes[current_mode]
        surface = create_gradient_surface(width, height, func)
        display.blit(surface, (0, 0))
        pygame.display.flip()

        logger.debug(f"Displaying {name} gradient")

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_SPACE:
                    current_mode = (current_mode + 1) % len(modes)
                    logger.info(f"Switched to {modes[current_mode][0]} mode")

    pygame.quit()
    logger.info("Colour test ended.")


def setup_args(arg):
    """Set up the command-line arguments."""
    pass  # No arguments needed


if __name__ == "__main__":
    main.go(colour_test, setup_args)
