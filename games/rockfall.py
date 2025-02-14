#!/usr/bin/env python3

"""
Boulder Dash-inspired game with falling rocks, pushable boulders, and collectible diamonds.
Use arrow keys to move. Collect all diamonds to unlock the exit.
"""

import pygame
import numpy as np

# ----- Game Settings ----- #
CELL_SIZE = 32
FPS = 15

# Cell types
EMPTY = 0
PLAYER = 1
WALL = 2
DIRT = 3
ROCK = 4
DIAMOND = 5
EXIT = 6

# Colors
COLORS = {
    EMPTY: (0, 0, 0),
    WALL: (100, 100, 100),
    DIRT: (139, 69, 19),
    ROCK: (169, 169, 169),
    DIAMOND: (0, 191, 255),
    EXIT: (255, 0, 0),  # Default red, changes to green when diamonds collected
}
PLAYER_COLOR = (0, 0, 255)
EXIT_COLOR_LOCKED = (255, 0, 0)
EXIT_COLOR_UNLOCKED = (0, 255, 0)

# Level definition
level_str = """
WWWWWWWWWWWWWWWWWWWW
W..................W
W..WWW.....D....R..W
W..W..W...WWW......W
W..W..W...W..R..D..W
W..W..WWW.D.W......W
W..P....R..W..WWW..W
W..W..W.D..W..W....W
W..W..WWW..W..W.R..W
W...........W..W...W
W..R..D......D..W..W
W..WWW..R..WWW..W..W
W.......D.......W..W
W.............E.W..W
WWWWWWWWWWWWWWWWWWWW
"""

# Key:
# W = wall
# . = dirt
# R = rock
# D = diamond
# P = player
# E = exit


GRID_HEIGHT = len(level_str.strip().split("\n"))
GRID_WIDTH = len(level_str.strip().split("\n")[0])


def create_grid_from_level(level_definition: str) -> tuple[np.ndarray, list[int], int]:
    """Convert level string to numpy grid and return player position and diamond count"""
    level_lines = level_definition.strip().split("\n")
    grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
    player_pos = [0, 0]
    total_diamonds = 0

    for y, line in enumerate(level_lines):
        for x, char in enumerate(line):
            if char == "W":
                grid[y, x] = WALL
            elif char == ".":
                grid[y, x] = DIRT
            elif char == "R":
                grid[y, x] = ROCK
            elif char == "D":
                grid[y, x] = DIAMOND
                total_diamonds += 1
            elif char == "P":
                player_pos = [y, x]
                grid[y, x] = DIRT
            elif char == "E":
                grid[y, x] = EXIT

    grid[player_pos[0], player_pos[1]] = PLAYER

    return grid, player_pos, total_diamonds


class GameState:
    """Game state container"""

    def __init__(self):
        self.grid, self.player_pos, self.total_diamonds = create_grid_from_level(level_str)
        self.diamonds_collected = 0

    def is_valid_move(self, new_y: int, new_x: int) -> bool:
        """Check if a move to the given coordinates is valid"""
        return (
            0 <= new_y < GRID_HEIGHT
            and 0 <= new_x < GRID_WIDTH
            and self.grid[new_y, new_x] != WALL
        )

    def attempt_push_rock(self, pos: list[int], dx: int) -> bool:
        """Try to push a rock horizontally. Returns True if successful."""
        y, x = pos
        target_x = x + dx  # The cell where the rock is to be pushed

        if 0 <= target_x < GRID_WIDTH and self.grid[y, target_x] == EMPTY:
            self.grid[y, target_x] = ROCK  # Move the rock to the target cell
            self.grid[y, x] = EMPTY  # Clear the original rock position
            return True
        return False

    def move_object(self, y: int, x: int, dy: int, dx: int):
        """Move an object at (y, x) to (y+dy, x+dx)"""
        self.grid[y + dy, x + dx] = self.grid[y, x]
        self.grid[y, x] = EMPTY

    def handle_player_move(self, dy: int, dx: int) -> tuple[list[int], int]:
        """Process player movement, including rock pushing and diamond collection"""
        y, x = self.player_pos
        new_y = y + dy
        new_x = x + dx

        if not self.is_valid_move(new_y, new_x):
            return self.player_pos, 0

        cell = self.grid[new_y, new_x]
        diamonds_gotten = 0

        if cell == ROCK and dx != 0:
            if not self.attempt_push_rock([new_y, new_x], dx):
                return self.player_pos, 0
        elif cell == DIAMOND:
            diamonds_gotten = 1
        elif cell == EXIT:
            if self.diamonds_collected == self.total_diamonds:
                self.player_pos = [new_y, new_x]
                return self.player_pos, 0
            return self.player_pos, 0
        elif cell not in [EMPTY, DIRT]:
            return self.player_pos, 0

        # Update grid with player's new position
        self.move_object(y, x, dy, dx)
        self.player_pos = [new_y, new_x]

        if cell == DIAMOND:
            self.diamonds_collected += 1

        return self.player_pos, diamonds_gotten

    def handle_event(self, event) -> str:
        """Process a single game event. Returns the new game state."""
        if event.type == pygame.QUIT:
            return "quit"

        if event.type != pygame.KEYDOWN:
            return "playing"

        # Handle ESC key to quit
        if event.key == pygame.K_ESCAPE:
            return "quit"

        # Handle movement
        dy = dx = 0
        if event.key == pygame.K_LEFT:
            dx = -1
        elif event.key == pygame.K_RIGHT:
            dx = 1
        elif event.key == pygame.K_UP:
            dy = -1
        elif event.key == pygame.K_DOWN:
            dy = 1
        else:
            return "playing"

        # Process move
        new_pos, diamonds = self.handle_player_move(dy, dx)

        # Check win condition
        if (
            self.grid[new_pos[0], new_pos[1]] == EXIT
            and self.diamonds_collected == self.total_diamonds
        ):
            return "won"

        return "playing"

    def process_single_rock(self, y: int, x: int) -> bool:
        """Handle falling/sliding for a single rock. Returns True if player is crushed."""

        # Try falling straight down
        if self.grid[y + 1, x] == EMPTY:
            self.move_object(y, x, 1, 0)
            return y < GRID_HEIGHT - 2 and self.grid[y + 2, x] == PLAYER

        # Check if rock can slide
        if y < GRID_HEIGHT - 1 and self.grid[y + 1, x] not in [ROCK, DIAMOND]:
            return False

        # Try slide left
        if x > 0:
            if self.grid[y, x - 1] == EMPTY and self.grid[y + 1, x - 1] == EMPTY:
                self.move_object(y, x, 0, -1)
                return False

        # Try slide right
        if x < GRID_WIDTH - 1:
            if self.grid[y, x + 1] == EMPTY and self.grid[y + 1, x + 1] == EMPTY:
                self.move_object(y, x, 0, 1)
                return False

        return False

    def update_rocks(self) -> bool:
        """Process falling and sliding rocks. Returns True if player is crushed."""
        for y in range(GRID_HEIGHT - 2, -1, -1):
            for x in range(GRID_WIDTH):
                if self.grid[y, x] == ROCK:
                    if self.process_single_rock(y, x):
                        return True
        return False


def draw_exit(screen, x, y, diamonds_collected: int, total_diamonds: int):
    """Draw exit as 8-point star with color based on diamond collection status"""
    cell_center = (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2)
    color = EXIT_COLOR_UNLOCKED if diamonds_collected == total_diamonds else EXIT_COLOR_LOCKED

    # Calculate star points
    size = int(CELL_SIZE * 0.707)  # sqrt(2)/2
    # Diamond points
    diamond_points = [
        (cell_center[0], cell_center[1] - CELL_SIZE // 2),
        (cell_center[0] + CELL_SIZE // 2, cell_center[1]),
        (cell_center[0], cell_center[1] + CELL_SIZE // 2),
        (cell_center[0] - CELL_SIZE // 2, cell_center[1]),
    ]
    # Square points
    square_points = [
        (cell_center[0] - size // 2, cell_center[1] - size // 2),
        (cell_center[0] + size // 2, cell_center[1] - size // 2),
        (cell_center[0] + size // 2, cell_center[1] + size // 2),
        (cell_center[0] - size // 2, cell_center[1] + size // 2),
    ]
    pygame.draw.polygon(screen, color, diamond_points)
    pygame.draw.polygon(screen, color, square_points)


def draw_diamond(screen, x: int, y: int):
    """Draw diamond as rotated square"""
    cell_center = (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2)
    diamond_points = [
        (cell_center[0], cell_center[1] - CELL_SIZE // 2),
        (cell_center[0] + CELL_SIZE // 2, cell_center[1]),
        (cell_center[0], cell_center[1] + CELL_SIZE // 2),
        (cell_center[0] - CELL_SIZE // 2, cell_center[1]),
    ]
    pygame.draw.polygon(screen, COLORS[DIAMOND], diamond_points)


def draw_cell(
    screen,
    cell_type: int,
    x: int,
    y: int,
    diamonds_collected: int,
    total_diamonds: int
):
    """Draw a single cell at grid position (x, y)"""
    rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    center = (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2)

    if cell_type in [WALL, DIRT]:
        pygame.draw.rect(screen, COLORS[cell_type], rect)

    elif cell_type == EXIT:
        draw_exit(screen, x, y, diamonds_collected, total_diamonds)

    elif cell_type == ROCK:
        pygame.draw.circle(screen, COLORS[ROCK], center, CELL_SIZE // 2 - 2)

    elif cell_type == DIAMOND:
        draw_diamond(screen, x, y)


def draw_player(screen, player_pos: list[int]):
    """Draw the player character at the given grid position"""
    player_center = (
        player_pos[1] * CELL_SIZE + CELL_SIZE // 2,
        player_pos[0] * CELL_SIZE + CELL_SIZE // 2
    )
    pygame.draw.circle(screen, PLAYER_COLOR, player_center, CELL_SIZE // 3)


def draw_game(
    screen,
    grid: np.ndarray,
    player_pos: list[int],
    diamonds_collected: int,
    total_diamonds: int
):
    """Draw the entire game state"""
    # Clear screen
    screen.fill(COLORS[EMPTY])

    # Draw grid
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = grid[y, x]
            if cell != EMPTY:
                draw_cell(screen, cell, x, y, diamonds_collected, total_diamonds)

    # Draw player
    draw_player(screen, player_pos)


def draw_hud(screen, diamonds_collected: int, total_diamonds: int):
    """Draw the heads-up display (diamond count)"""
    font = pygame.font.Font(None, 36)
    text = font.render(
        f"Diamonds: {diamonds_collected}/{total_diamonds}", True, (255, 255, 255)
    )
    screen.blit(text, (10, 10))


def show_end_screen(screen, game_state: str):
    """Show the final game over or victory screen"""
    if game_state == "won":
        color = (0, 255, 0)
        message = "YOU WIN!"
    elif game_state == "dead":
        color = (255, 0, 0)
        message = "GAME OVER"
    else:
        return

    font = pygame.font.Font(None, 74)
    text = font.render(message, True, color)
    screen.blit(text, (GRID_WIDTH * CELL_SIZE // 4, GRID_HEIGHT * CELL_SIZE // 2))
    pygame.display.flip()
    pygame.time.wait(2000)


def main():
    """Main game loop."""
    pygame.init()
    screen = pygame.display.set_mode(
        (GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE)
    )
    pygame.display.set_caption("Boulder Dash")
    clock = pygame.time.Clock()

    # Initialize game state
    state = GameState()
    game_status = "playing"

    while game_status == "playing":
        clock.tick(FPS)

        # Handle events
        for event in pygame.event.get():
            game_status = state.handle_event(event)
            if game_status == "quit":
                break

        if game_status == "quit":
            break

        # Update rocks
        if state.update_rocks():
            game_status = "dead"

        # Draw current state
        draw_game(
            screen,
            state.grid,
            state.player_pos,
            state.diamonds_collected,
            state.total_diamonds
        )
        draw_hud(screen, state.diamonds_collected, state.total_diamonds)
        pygame.display.flip()

    # Show final screen
    show_end_screen(screen, game_status)
    pygame.quit()


if __name__ == "__main__":
    main()
