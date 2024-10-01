#Here's a simple Python program using pygame to draw a circle:
#```python
import pygame

pygame.init()

screen = pygame.display.set_mode((800, 600))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((255, 255, 255))

    # Draw a circle
    pygame.draw.circle(screen, (0, 0, 255), (400, 300), 75)

    pygame.display.flip()

pygame.quit()
#```
#
#This program:
#
#- Initializes pygame
#- Sets up an 800x600 pixel display surface
#- Checks for QUIT events to end the program
#- Fills the background with white
#- Uses pygame.draw.circle() to draw a blue circle at (400, 300) with radius 75
#- Updates the display with pygame.display.flip()
#- Quits pygame when done
#
#This will show a window with a blue circle on a white background. Let me know if you have any questions!#
