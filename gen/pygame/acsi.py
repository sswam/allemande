import pygame
import sys

# --- Initialization ---
# This must be called before any other pygame functions.
pygame.init()

# --- Constants ---
# Using constants makes your code easier to read and modify.
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SIZE = 50
PLAYER_SPEED = 5

# Colors (RGB tuples)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)

# --- Set up the display ---
# Creates the main window for our game.
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simple Pygame Demo")

# --- Game State ---
# The player is represented by a Rect object. We start it in the center.
# A pygame.Rect stores a position (x, y) and a size (width, height).
player_rect = pygame.Rect(
    (SCREEN_WIDTH - PLAYER_SIZE) // 2,
    (SCREEN_HEIGHT - PLAYER_SIZE) // 2,
    PLAYER_SIZE,
    PLAYER_SIZE
)

# A clock is used to control the frame rate.
clock = pygame.time.Clock()

# --- Main Game Loop ---
# The loop will continue running as long as this variable is True.
running = True
while running:
    # --- 1. Event Handling ---
    # Pygame processes all user input and window events in a queue.
    # We must loop through this queue in each frame.
    for event in pygame.event.get():
        # Check if the user clicked the window's close button.
        if event.type == pygame.QUIT:
            running = False
        # The pygame.QUIT event is the only one we *must* handle.

    # --- 2. Update Game State ---
    # This section updates game objects based on input and game logic.

    # Get a dictionary of all currently pressed keys.
    keys_pressed = pygame.key.get_pressed()

    # Update player position based on which arrow key is down.
    # We also check boundaries to keep the player on the screen.
    if keys_pressed[pygame.K_LEFT] and player_rect.left > 0:
        player_rect.x -= PLAYER_SPEED
    if keys_pressed[pygame.K_RIGHT] and player_rect.right < SCREEN_WIDTH:
        player_rect.x += PLAYER_SPEED
    if keys_pressed[pygame.K_UP] and player_rect.top > 0:
        player_rect.y -= PLAYER_SPEED
    if keys_pressed[pygame.K_DOWN] and player_rect.bottom < SCREEN_HEIGHT:
        player_rect.y += PLAYER_SPEED

    # --- 3. Drawing ---
    # This section handles all rendering to the screen.
    # It should happen *after* all game state has been updated.

    # First, fill the screen with a background color.
    # This clears the previous frame.
    screen.fill(BLACK)

    # Now, draw the player rectangle onto the screen surface.
    pygame.draw.rect(screen, BLUE, player_rect)

    # --- 4. Update the Display ---
    # This command pushes everything we've drawn in this frame to the actual
    # display that the user sees.
    pygame.display.flip()

    # --- 5. Control Frame Rate ---
    # This tells pygame to wait long enough to cap the frame rate at 60 FPS.
    # It helps make movement speed consistent across different computers.
    clock.tick(60)

# --- Cleanup ---
# Once the `running` variable is False, the loop exits.
# We call quit functions to clean up pygame's resources.
pygame.quit()
sys.exit()

