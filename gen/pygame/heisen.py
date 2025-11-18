# Simple Pygame demo
# - Move the blue square with Arrow keys or WASD
# - Avoid the bouncing ball (square turns red on hit)
# - Press ESC or close the window to quit
# Run: pip install pygame && python this_file.py

import sys
import pygame

def main():
    pygame.init()
    pygame.display.set_caption("Heisen's Pygame Demo")

    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Colors
    BG = (28, 32, 38)
    PLAYER_COLOR = (80, 180, 255)
    HIT_COLOR = (255, 90, 110)
    BALL_COLOR = (255, 220, 80)
    TEXT = (220, 220, 230)

    # Player setup
    player_size = 44
    player = pygame.Rect(WIDTH // 2 - player_size // 2, HEIGHT // 2 - player_size // 2, player_size, player_size)
    player_speed = 320  # pixels/sec
    hit_timer = 0.0

    # Bouncing ball setup
    ball_r = 20
    ball_x, ball_y = WIDTH * 0.25, HEIGHT * 0.35
    ball_vx, ball_vy = 240.0, 180.0

    font = pygame.font.Font(None, 24)
    big_font = pygame.font.Font(None, 42)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # seconds since last frame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # Input
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])

        # Normalize diagonal movement
        if dx and dy:
            inv = 0.70710678  # 1/sqrt(2)
            dx *= inv
            dy *= inv

        # Update player position
        player.x += int(dx * player_speed * dt)
        player.y += int(dy * player_speed * dt)
        player.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

        # Update ball position
        ball_x += ball_vx * dt
        ball_y += ball_vy * dt

        # Bounce off edges
        if ball_x - ball_r < 0:
            ball_x = ball_r
            ball_vx *= -1
        elif ball_x + ball_r > WIDTH:
            ball_x = WIDTH - ball_r
            ball_vx *= -1

        if ball_y - ball_r < 0:
            ball_y = ball_r
            ball_vy *= -1
        elif ball_y + ball_r > HEIGHT:
            ball_y = HEIGHT - ball_r
            ball_vy *= -1

        # Collision (rect-circle via bounding box is fine here)
        ball_rect = pygame.Rect(int(ball_x - ball_r), int(ball_y - ball_r), ball_r * 2, ball_r * 2)
        if player.colliderect(ball_rect):
            hit_timer = 0.2  # flash red for 0.2s

        if hit_timer > 0:
            hit_timer -= dt

        # Draw
        screen.fill(BG)

        # Player
        color = HIT_COLOR if hit_timer > 0 else PLAYER_COLOR
        pygame.draw.rect(screen, color, player, border_radius=8)

        # Ball
        pygame.draw.circle(screen, BALL_COLOR, (int(ball_x), int(ball_y)), ball_r)

        # UI text
        info = "Arrows/WASD to move • ESC to quit"
        fps = f"{clock.get_fps():.0f} FPS"
        screen.blit(font.render(info, True, TEXT), (10, HEIGHT - 26))
        screen.blit(font.render(fps, True, TEXT), (WIDTH - 70, 10))
        screen.blit(big_font.render("Heisen's Pygame Demo", True, TEXT), (12, 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

