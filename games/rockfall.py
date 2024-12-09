#!/usr/bin/env python3

import pygame
import numpy as np
import sys

# Initialize Pygame
pygame.init()
CELL_SIZE = 32
GRID_WIDTH = 20
GRID_HEIGHT = 15
screen = pygame.display.set_mode((GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE))
clock = pygame.time.Clock()

# Game elements
EMPTY = 0
WALL = 1
DIRT = 2
ROCK = 3
DIAMOND = 4
PLAYER = 5
EXIT = 6

# Colors
COLORS = {
    EMPTY: (0, 0, 0),
    WALL: (100, 100, 100),
    DIRT: (139, 69, 19),
    ROCK: (169, 169, 169),
    DIAMOND: (0, 191, 255),
    PLAYER: (255, 255, 0),
    EXIT: (0, 255, 0)
}

# Initial level
level = """
WWWWWWWWWWWWWWWWWWWW
W..................W
W...R..D...........W
W..................W
W..WWW.....D.R.....W
W......WWW.........W
W..D..P....R.......W
W..................W
W...R....WWW..D....W
W..................W
W.....D....R.......W
W...WWW............W
W.........D.....E..W
W..................W
WWWWWWWWWWWWWWWWWWWW
"""

# Convert level string to numpy array
grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
player_pos = [0, 0]
total_diamonds = 0

for y, row in enumerate(level.strip().split('\n')):
    for x, char in enumerate(row):
        if char == 'W':
            grid[y, x] = WALL
        elif char == '.':
            grid[y, x] = DIRT
        elif char == 'R':
            grid[y, x] = ROCK
        elif char == 'D':
            grid[y, x] = DIAMOND
            total_diamonds += 1
        elif char == 'P':
            player_pos = [y, x]
            grid[y, x] = EMPTY
        elif char == 'E':
            grid[y, x] = EXIT

diamonds_collected = 0
game_over = False
game_won = False

def check_rock_fall_kill(grid, player_pos):
    if (player_pos[0] > 0 and
        grid[player_pos[0]-1, player_pos[1]] == EMPTY and
        grid[player_pos[0]-2, player_pos[1]] == ROCK):
        return True
    return False

def can_push_rock(grid, player_pos, direction):
    rock_pos = [player_pos[0], player_pos[1] + direction]
    target_pos = [player_pos[0], player_pos[1] + direction * 2]

    # Check if target position is within grid and empty
    if (0 <= target_pos[1] < GRID_WIDTH and
        grid[target_pos[0], target_pos[1]] == EMPTY):
        return True
    return False

def draw_game(screen, grid, player_pos, CELL_SIZE):
    screen.fill((0, 0, 0))

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell_center = (x * CELL_SIZE + CELL_SIZE//2,
                         y * CELL_SIZE + CELL_SIZE//2)

            if grid[y, x] == WALL:
                pygame.draw.rect(screen, COLORS[WALL],
                               (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

            elif grid[y, x] == DIRT:
                pygame.draw.rect(screen, COLORS[DIRT],
                               (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

            elif grid[y, x] == ROCK:
                pygame.draw.circle(screen, COLORS[ROCK],
                                 cell_center, CELL_SIZE//2 - 2)

            elif grid[y, x] == DIAMOND:
                # Draw diamond shape
                diamond_points = [
                    (cell_center[0], cell_center[1] - CELL_SIZE//2),  # top
                    (cell_center[0] + CELL_SIZE//2, cell_center[1]),  # right
                    (cell_center[0], cell_center[1] + CELL_SIZE//2),  # bottom
                    (cell_center[0] - CELL_SIZE//2, cell_center[1])   # left
                ]
                pygame.draw.polygon(screen, COLORS[DIAMOND], diamond_points)

            elif grid[y, x] == EXIT:
                # Draw 8-point star (diamond + square)
                size = int(CELL_SIZE * 0.707)  # sqrt(2)/2
                # Diamond points
                diamond_points = [
                    (cell_center[0], cell_center[1] - CELL_SIZE//2),
                    (cell_center[0] + CELL_SIZE//2, cell_center[1]),
                    (cell_center[0], cell_center[1] + CELL_SIZE//2),
                    (cell_center[0] - CELL_SIZE//2, cell_center[1])
                ]
                # Square points
                square_points = [
                    (cell_center[0] - size//2, cell_center[1] - size//2),
                    (cell_center[0] + size//2, cell_center[1] - size//2),
                    (cell_center[0] + size//2, cell_center[1] + size//2),
                    (cell_center[0] - size//2, cell_center[1] + size//2)
                ]
                pygame.draw.polygon(screen, COLORS[EXIT], diamond_points)
                pygame.draw.polygon(screen, COLORS[EXIT], square_points)

    # Draw player (half-sized circle)
    if not game_over:
        player_center = (player_pos[1] * CELL_SIZE + CELL_SIZE//2,
                        player_pos[0] * CELL_SIZE + CELL_SIZE//2)
        pygame.draw.circle(screen, COLORS[PLAYER],
                         player_center, CELL_SIZE//4)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and not game_over and not game_won:
            new_pos = player_pos.copy()

            if event.key == pygame.K_LEFT:
                new_pos[1] -= 1
                # Check if trying to push rock left
                if (grid[new_pos[0], new_pos[1]] == ROCK and
                    can_push_rock(grid, player_pos, -1)):
                    grid[new_pos[0], new_pos[1] - 1] = ROCK
                    grid[new_pos[0], new_pos[1]] = EMPTY
            elif event.key == pygame.K_RIGHT:
                new_pos[1] += 1
                # Check if trying to push rock right
                if (grid[new_pos[0], new_pos[1]] == ROCK and
                    can_push_rock(grid, player_pos, 1)):
                    grid[new_pos[0], new_pos[1] + 1] = ROCK
                    grid[new_pos[0], new_pos[1]] = EMPTY
            elif event.key == pygame.K_UP:
                new_pos[0] -= 1
            elif event.key == pygame.K_DOWN:
                new_pos[0] += 1

            # Check if move is valid
            move_valid = False
            if (0 <= new_pos[0] < GRID_HEIGHT and
                0 <= new_pos[1] < GRID_WIDTH and
                grid[new_pos[0], new_pos[1]] != WALL and
                grid[new_pos[0], new_pos[1]] != ROCK):

                move_valid = True

                # Collect diamond
                if grid[new_pos[0], new_pos[1]] == DIAMOND:
                    diamonds_collected += 1

                # Check exit
                if grid[new_pos[0], new_pos[1]] == EXIT:
                    if diamonds_collected == total_diamonds:
                        game_won = True
                    else:
                        move_valid = False

            if move_valid:
                # Move player
                grid[new_pos[0], new_pos[1]] = EMPTY
                player_pos = new_pos

    if not game_over and not game_won:
        # Apply gravity to rocks
        for y in range(GRID_HEIGHT-2, -1, -1):
            for x in range(GRID_WIDTH):
                if grid[y, x] == ROCK:
                    # Check if space below is empty and not player position
                    if grid[y+1, x] == EMPTY and [y+1, x] != player_pos:
                        grid[y+1, x] = ROCK
                        grid[y, x] = EMPTY
                        # Check if rock killed player
                        if [y+2, x] == player_pos:
                            game_over = True
                    # Check for sliding
                    elif grid[y+1, x] in [ROCK, DIAMOND]:
                        # Try slide left
                        if (x > 0 and grid[y, x-1] == EMPTY and [y, x-1] != player_pos
                            and grid[y+1, x-1] == EMPTY and [y+1, x-1] != player_pos):
                            grid[y, x-1] = ROCK
                            grid[y, x] = EMPTY
                        # Try slide right
                        elif (x < GRID_WIDTH-1 and grid[y, x+1] == EMPTY and [y, x+1] != player_pos
                              and grid[y+1, x+1] == EMPTY and [y+1, x+1] != player_pos):
                            grid[y, x+1] = ROCK
                            grid[y, x] = EMPTY

        # Check if player is crushed by falling rock
        if check_rock_fall_kill(grid, player_pos):
            game_over = True

    # Draw game
    draw_game(screen, grid, player_pos, CELL_SIZE)

    # Draw game over or win message
    if game_over:
        font = pygame.font.Font(None, 74)
        text = font.render('GAME OVER', True, (255, 0, 0))
        screen.blit(text, (GRID_WIDTH * CELL_SIZE // 4, GRID_HEIGHT * CELL_SIZE // 2))
    elif game_won:
        font = pygame.font.Font(None, 74)
        text = font.render('YOU WIN!', True, (0, 255, 0))
        screen.blit(text, (GRID_WIDTH * CELL_SIZE // 4, GRID_HEIGHT * CELL_SIZE // 2))

    # Draw diamond count
    font = pygame.font.Font(None, 36)
    text = font.render(f'Diamonds: {diamonds_collected}/{total_diamonds}', True, (255, 255, 255))
    screen.blit(text, (10, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()


# TODO maybe mark the player in the grid to simplify sliding, etc
# TODO more functions, less nesting / intentation
