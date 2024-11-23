#!/usr/bin/env python3

import pygame
import math
from pygame.color import THECOLORS as COLORS

pygame.init()

WIDTH = 800
HEIGHT = 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Animated Hello World!")

BLACK = (0, 0, 0)
RAINBOW = [(255,0,0), (255,127,0), (255,255,0), (0,255,0),
           (0,0,255), (75,0,130), (148,0,211)]

font = pygame.font.Font(None, 74)
text = "Hello World!"

# Pre-calculate letter surfaces and widths
letters = []
x = 100  # Starting x position
for letter in text:
    surface = font.render(letter, True, COLORS['white'])
    width = surface.get_width()
    letters.append((letter, width))

running = True
clock = pygame.time.Clock()
time = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    x = 100  # Reset x position
    for i, (letter, width) in enumerate(letters):
        y = HEIGHT//2 + math.sin(time + i/2) * 30

        color = RAINBOW[i % len(RAINBOW)]
        letter_surface = font.render(letter, True, color)
        screen.blit(letter_surface, (x, y))

        # Advance x position by actual letter width plus small spacing
        x += width + 2

    time += 0.1
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
