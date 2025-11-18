import pygame
import sys

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bouncing Ball Demo")

# Colors
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)

# Ball properties
ball_x = WIDTH // 2
ball_y = HEIGHT // 2
ball_radius = 30
ball_speed_x = 5
ball_speed_y = 4

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Main game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update ball position
    ball_x += ball_speed_x
    ball_y += ball_speed_y

    # Bounce off walls
    if ball_x - ball_radius <= 0 or ball_x + ball_radius >= WIDTH:
        ball_speed_x *= -1
    if ball_y - ball_radius <= 0 or ball_y + ball_radius >= HEIGHT:
        ball_speed_y *= -1

    # Draw everything
    screen.fill(WHITE)
    pygame.draw.circle(screen, BLUE, (ball_x, ball_y), ball_radius)

    # Update display
    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()
sys.exit()
