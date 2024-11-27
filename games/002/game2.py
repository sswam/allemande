#!/usr/bin/env python3

"""

Uses the boil game engine for graphics.

Resolution: 2560x1440
Background music: "theme" at 30% volume
"""

from boil import *
from random import randint
from math import *

# Initialize game window
game = init("Gradients", music="theme", volume=0.3, width=2560, height=1440)

def random_point():
    x = randint(0, game.width-1)
    y = randint(0, game.height-1)
    return x, y

def random_triangle():
    x0, y0 = random_point()
    x1, y1 = random_point()
    x2, y2 = random_point()
    return x0, y0, x1, y1, x2, y2

def random_color():
    r = randint(0, 255)
    g = randint(0, 255)
    b = randint(0, 255)
    return r, g, b

def tri(x0, y0, x1, y1, x2, y2):
    """Draw a triangle by connecting three points"""
    move((x0, y0))
    draw((x1, y1))
    draw((x2, y2))
    draw((x0, y0))


def point(p, color="white"):
    """Draw a point"""
    circle(p, 1, color)

# main program

def blend(a, x0, x1):
    x = (1-a)*x0 + a*x1
    return x

def draw_gradient_triangle():
    global x0, y0, x1, y1, x2, y2, c0, c1, c2
    for i in range(0, 501):
        a = i / 500

        x3 = blend(a, x0, x1)
        y3 = blend(a, y0, y1)
 
        r0, g0, b0 = c0
        r1, g1, b1 = c1
        r2, g2, b2 = c2

        r3 = blend(a, r0, r1)
        g3 = blend(a, g0, g1)
        b3 = blend(a, b0, b1)

        c3 = r3, g3, b3

        for j in range(0, 501):
            b = j / 500

            # point
            x4 = blend(b, x3, x2)
            y4 = blend(b, y3, y2)

            # color            
            r4 = blend(b, r3, r2)
            g4 = blend(b, g3, g2)
            b4 = blend(b, b3, b2)

            c4 = r4, g4, b4

            circle((x4, y4), 6, c4)

# Main game loop
while playing():
    # tri(x0, y0, x1, y1, x2, y2)

    # count from 0 to 1 by 0.01s

    # work out a point on the first side that far along
    # draw a dot at this point

    for i in range(5):
        x0, y0, x1, y1, x2, y2 = random_triangle()

        c0 = random_color()
        c1 = random_color()
        c2 = random_color()

        draw_gradient_triangle()
