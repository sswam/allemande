#!/usr/bin/env python3

import pygame
import sys
from math import radians, cos, sin

# Initialize Pygame
pygame.init()

# Set up display
width, height = 800, 600
window = pygame.display.set_mode((width, height))
pygame.display.set_caption("Tiny Space Game")

# Define colors
black = (0, 0, 0)
white = (255, 255, 255)

# Triangle settings
triangle_pos = [width // 2, height // 2]
triangle_angle = 0
triangle_speed = 5
triangle_size = 20

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Controls
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        triangle_angle -= 5
    if keys[pygame.K_RIGHT]:
        triangle_angle += 5
    if keys[pygame.K_UP]:
        triangle_pos[0] += triangle_speed * cos(radians(triangle_angle))
        triangle_pos[1] += triangle_speed * sin(radians(triangle_angle))

    # Wrap around the screen
    triangle_pos[0] %= width
    triangle_pos[1] %= height

    # Clear screen
    window.fill(black)

    # Draw the triangle
    point1 = (triangle_pos[0] + (1.5 * triangle_size) * cos(radians(triangle_angle)),
              triangle_pos[1] + (1.5 * triangle_size) * sin(radians(triangle_angle)))
    point2 = (triangle_pos[0] + triangle_size * cos(radians(triangle_angle + 120)),
              triangle_pos[1] + triangle_size * sin(radians(triangle_angle + 120)))
    point3 = (triangle_pos[0] + triangle_size * cos(radians(triangle_angle + 240)),
              triangle_pos[1] + triangle_size * sin(radians(triangle_angle + 240)))

    pygame.draw.polygon(window, white, [point1, point2, point3])

    # Update the display
    pygame.display.flip()

    # Frame rate
    pygame.time.Clock().tick(60)

pygame.quit()
