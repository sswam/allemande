#!/usr/bin/env python3

from boil import *

init("Move the Square!", music="theme", volume=0.3)

while playing():
    move_player()
    draw_player()
    bump(sound="bump", volume=0.5)
