#!/usr/bin/env python3

"""
Functional interface for simple pygame-based games.
"""

from pathlib import Path

from boiler import pygame, GameConfig, GameObject, GameEngine

__version__ = "0.1.2"


# Global state
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


def playing() -> bool:
    """Check if game is still running."""
    engine.update_display()
    engine.handle_basic_events()
    engine.clear_screen()
    if not engine.running:
        engine.quit()
    return engine.running


def init(title: str = "Game", music=None, volume=0.3) -> None:
    """Initialize the game with optional title."""
    global config, engine, player
    config = GameConfig(title=title)
    engine = GameEngine(config)
    player = GameObject()
    load_sounds()
    if music is not None:
        play_music(music, volume=volume)


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
