#!/usr/bin/env python3

"""A simple bouncing rectangle animation using Pygame."""

import pygame

# Define some constants
WIDTH, HEIGHT = 800, 600
FPS = 60

# Initialize Pygame
pygame.init()  # pylint: disable=no-member

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
running = True

# Initialize rectangle and speeds
rect = pygame.Rect(100, 200, 50, 20)
speed_x = 5
speed_y = 7

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # pylint: disable=no-member
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:  # pylint: disable=no-member
        running = False

    screen.fill((0, 0, 0))

    rect.x += speed_x
    rect.y += speed_y

    if rect.left < 0 or rect.right > WIDTH:
        speed_x *= -1
    elif rect.top < 0 or rect.bottom > HEIGHT:
        speed_y *= -1

    # Draw everything
    pygame.draw.rect(screen, (255, 0, 0), rect)

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()  # pylint: disable=no-member
