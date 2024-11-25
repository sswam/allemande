#!/usr/bin/env python3

"""
Functional interface for simple pygame-based games.
"""

from pathlib import Path

from boiler import pygame, GameConfig, GameObject, GameEngine

__version__ = "0.1.2"


# Global state
game = None
config = None
engine = None
player = None

moved = False
bumped = False
dragging = False


def move_player(keys=True, mouse=True) -> None:
    """Handle player movement using keyboard and mouse."""
    global moved, bumped, dragging
    x0, y0 = player.x, player.y

    # Handle keyboard movement only if not being dragged
    if keys and not engine.dragging:
        engine.move_with_keyboard(player, pygame.key.get_pressed())

    # Handle mouse dragging
    if mouse:
        engine.move_with_mouse(player)
        dragging = engine.dragging

    # Check if player moved or bumped into a wall
    x1, y1 = player.x, player.y
    engine.keep_in_bounds(player)
    x2, y2 = player.x, player.y

    moved = (x2, y2) != (x0, y0)
    bumped = (x2, y2) != (x1, y1)


def draw_player() -> None:
    """Draw the player object."""
    engine.draw_rect(player)


class Game:
    width = 800
    height = 600


def playing() -> bool:
    """Check if game is still running."""
    engine.update_display()
    engine.handle_basic_events()
    engine.clear_screen()
    if not engine.running:
        engine.quit()
    return engine.running


def init(title: str = "Game", music=None, volume=0.3, width=800, height=600) -> None:
    """Initialize the game with optional title."""
    global game, config, engine, player
    config = GameConfig(title=title, width=width, height=height)
    engine = GameEngine(config)
    player = GameObject()
    load_sounds()
    if music is not None:
        play_music(music, volume=volume)
    game = Game()
    game.width, game.height = config.width, config.height
    return game


def load_sound(name: str, path: str) -> None:
    """Load a sound effect."""
    engine.load_sound(name, path)


def play_sound(name: str, volume=1.0) -> None:
    """Play a loaded sound effect."""
    engine.play_sound(name, volume=volume)


def play_music(name: str, volume=1.0, loop: bool = True) -> None:
    """Start playing background music."""
    if name is None:
        return
    path = f"music/{name}.ogg"
    engine.play_music(path, volume=volume, loop=loop)


def load_sounds(dir="sounds") -> None:
    """Load all sound files in a directory."""
    if not Path(dir).is_dir():
        return
    for file in Path(dir).iterdir():
        if file.suffix == ".ogg":
            engine.load_sound(file.stem, str(file))


def bump(sound="bump", volume=1.0) -> None:
    """Play a bump sound effect."""
    if bumped:
        play_sound(sound, volume=volume)


class Context:
    colour = (255, 255, 255)
    p = (0, 0)


context = Context()


def color(r, g, b) -> tuple[int, int, int]:
    """Set the drawing color."""
    context.colour = (r, g, b)


def line(p0, p1, color=None, width=1) -> None:
    """Draw a line from (x0, y0) to (x1, y1)."""
    color = color or context.colour
    pygame.draw.line(engine.screen, color, p0, p1, width=width)
    context.p = p1


def circle(pos, radius, color=None, width=0) -> None:
    """Draw a circle at (x, y) with given radius."""
    color = color or context.colour
    pygame.draw.circle(engine.screen, color, pos, radius, width=width)
    context.p = pos


def move(p) -> None:
    """Move the drawing cursor to (x, y)."""
    context.p = p


def draw(p, color=None, width=1) -> None:
    """Draw a line from the current cursor position to (x, y)."""
    line(context.p, p, color=color, width=width)


def triangle(p0, p1, p2, color=None, width=0) -> None:
    """Draw a triangle with vertices at (x0, y0), (x1, y1), and (x2, y2)."""
    color = color or context.colour
    pygame.draw.polygon(engine.screen, color, (p0, p1, p2), width=width)
    context.p = p2
