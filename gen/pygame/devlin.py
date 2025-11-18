"""Simple Pygame Demo - Player-controlled square"""
import pygame


def main() -> None:
    """Run a simple pygame demo with a moveable player square."""
    # Initialize pygame and create window
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Simple Pygame Demo - Use Arrow Keys")
    clock = pygame.time.Clock()

    # Colors
    BLACK = (0, 0, 0)
    GREEN = (0, 255, 0)

    # Player properties
    player_x = 375
    player_y = 275
    player_size = 50
    player_speed = 5

    # Main game loop
    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update - handle keyboard input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= player_speed
        if keys[pygame.K_RIGHT] and player_x < 800 - player_size:
            player_x += player_speed
        if keys[pygame.K_UP] and player_y > 0:
            player_y -= player_speed
        if keys[pygame.K_DOWN] and player_y < 600 - player_size:
            player_y += player_speed

        # Render
        screen.fill(BLACK)
        pygame.draw.rect(screen, GREEN, (player_x, player_y, player_size, player_size))
        pygame.display.flip()

        # Control frame rate
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
