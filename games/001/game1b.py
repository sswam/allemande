#!/usr/bin/env python3

"""
A simple pygame animation with WASD controls for movement.
"""

__version__ = "0.1.1"

from boiler import pygame, GameConfig, GameObject, GameEngine

# Create game configuration
config = GameConfig(title="Move the Square!")

# Initialize game engine
engine = GameEngine(config)

# Create player
player = GameObject()

# Load sound effects
engine.load_sound("bump", "sounds/bump.wav")

# Play background music
engine.play_music("music/theme.mp3")

# Main game loop
while engine.running:
    engine.handle_basic_events()

    # Update game state
    engine.handle_movement(player, pygame.key.get_pressed())
    if engine.keep_in_bounds(player):
        engine.play_sound("bump")

    # Draw
    engine.clear_screen()
    engine.draw_rect(player)
    engine.update_display()

engine.quit()
