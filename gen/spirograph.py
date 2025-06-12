import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import argparse
import random

def spirograph_points(R, r, d, num_points=10000, cycles=100):
    # R: fixed circle radius
    # r: rolling circle radius
    # d: pen distance from center of rolling circle
    points = []
    for i in range(num_points):
        t = 2 * math.pi * cycles * i / num_points
        x = (R - r) * math.cos(t) + d * math.cos((R - r) * t / r)
        y = (R - r) * math.sin(t) - d * math.sin((R - r) * t / r)
        points.append((x, y))
    return points

def normalize_points(points):
    xs, ys = zip(*points)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    norm = []
    for x, y in points:
        nx = (x - min_x) / (max_x - min_x)
        ny = (y - min_y) / (max_y - min_y)
        norm.append((nx, ny))
    return norm

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--R', type=float, help='Fixed circle radius')
    parser.add_argument('--r', type=float, help='Rolling circle radius')
    parser.add_argument('--d', type=float, help='Pen offset')
    return parser.parse_args()

args = parse_args()

R = args.R if args.R is not None else random.uniform(3, 8)
r = args.r if args.r is not None else random.uniform(1, R-1)
d = args.d if args.d is not None else random.uniform(0.5, R)

pygame.init()
display = (600, 600)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
gluOrtho2D(0, 1, 0, 1)

print(f"Using R={R:.2f}, r={r:.2f}, d={d:.2f}")

points = spirograph_points(R, r, d)
points = normalize_points(points)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(0.2, 0.7, 1.0)
    glBegin(GL_LINE_STRIP)
    for x, y in points:
        glVertex2f(x, y)
    glEnd()
    pygame.display.flip()

pygame.quit()

