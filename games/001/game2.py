#!/usr/bin/env python3

from boil import *

game = init("Move the Square!", music="theme", volume=0.3)

while playing():
    line((0, 0), (game.width, game.height))
    line((game.width, 0), (0, game.height))
    circle((game.width // 2, game.height // 2), 100, "blue")
    move_player()
    draw_player()
    bump(sound="bump", volume=0.5)
