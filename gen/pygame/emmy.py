import pygame

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption('Simple Pygame Demo')
clock = pygame.time.Clock()

# Square properties
x, y = 180, 130
speed = 5
size = 40

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        x -= speed
    if keys[pygame.K_RIGHT]:
        x += speed
    if keys[pygame.K_UP]:
        y -= speed
    if keys[pygame.K_DOWN]:
        y += speed

    screen.fill((30, 30, 30))
    pygame.draw.rect(screen, (0, 120, 255), (x, y, size, size))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()

