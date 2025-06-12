import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

pygame.init()
display = (500, 500)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
gluOrtho2D(0, 1, 0, 1)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    glClear(GL_COLOR_BUFFER_BIT)
    glBegin(GL_QUADS)
    glVertex2f(0.2, 0.2)
    glVertex2f(0.8, 0.2)
    glVertex2f(0.8, 0.8)
    glVertex2f(0.2, 0.8)
    glEnd()
    pygame.display.flip()

pygame.quit()
