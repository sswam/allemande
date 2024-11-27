#!/usr/bin/env python3

"""
Sierpinski Triangle Visualization
Creates an animated visualization of the Sierpinski triangle fractal with random lines and circles.
Uses the boil game engine for graphics.

Resolution: 2560x1440
Background music: "theme" at 30% volume
"""

from boil import *
from random import randint
from math import *

# Initialize game window
game = init("Sierpinski", music="theme", volume=0.3, width=2560, height=1440)

def draw_lines():
    """Draw random lines with colored circles at their midpoints"""
    for i in range(1000):
        x0 = randint(0, game.width)
        y0 = randint(0, game.height)
        x1 = randint(0, game.width)
        y1 = randint(0, game.height)

        # Calculate midpoint for circle placement
        mx = (x0 + x1) / 2
        my = (y0 + y1) / 2

        line((x0, y0), (x1, y1), color="blue")
        # Generate random RGB colors for circles
        r = randint(0, 255)
        g = randint(0, 255)
        b = randint(0, 255)
        circle((mx, my), randint(2, 35), color=(r, g, b))

def init_triangle():
    """Initialize the main triangle vertices based on window dimensions"""
    global x0, y0, x1, y1, x2, y2
    x0 = game.width / 2
    y0 = 0
    x1 = x0 + (game.height - 1) * tan(radians(30))
    y1 = (game.height - 1)
    x2 = x0 - (game.height - 1) * tan(radians(30))
    y2 = (game.height - 1)

def tri(x0, y0, x1, y1, x2, y2):
    """Draw a triangle by connecting three points"""
    move((x0, y0))
    draw((x1, y1))
    draw((x2, y2))
    draw((x0, y0))

def mid(x0, y0, x1, y1):
    """Calculate midpoint between two points"""
    mx = (x0 + x1) / 2
    my = (y0 + y1) / 2
    return mx, my

def sierpinski_gasket(x0, y0, x1, y1, x2, y2, depth):
    """Recursively draw Sierpinski triangle to specified depth"""
    if depth == 0:
        return

    # Calculate midpoints of triangle sides
    mx0, my0 = mid(x0, y0, x1, y1)
    mx1, my1 = mid(x1, y1, x2, y2)
    mx2, my2 = mid(x2, y2, x0, y0)
    tri(mx0, my0, mx1, my1, mx2, my2)

    # Recursive calls for three smaller triangles
    sierpinski_gasket(x0, y0, mx0, my0, mx2, my2, depth - 1)
    sierpinski_gasket(mx0, my0, x1, y1, mx1, my1, depth - 1)
    sierpinski_gasket(mx2, my2, mx1, my1, x2, y2, depth - 1)

# Initialize starting triangle
init_triangle()

# Growth factor for animation
f = 2 ** (1/35)

# Main game loop
while playing():
    draw_lines()

    # Draw three connected Sierpinski triangles
    sierpinski_gasket(x0, y0, x1, y1, x2, y2, 8)
    sierpinski_gasket(x0, y0, x1, y1, x0 + (x1-x0)*2, y0, 8)
    sierpinski_gasket(x0, y0, x2, y2, x0 - (x1-x0)*2, y0, 8)

    # Scale triangle vertices for animation
    x0 = (x0 - game.width / 2) * f + game.width / 2
    y0 *= f
    x1 = (x1 - game.width / 2) * f + game.width / 2
    y1 *= f
    x2 = (x2 - game.width / 2) * f + game.width / 2
    y2 *= f

    # Reset triangle when it grows too large
    if y1 >= game.height * 2 / f:
        init_triangle()
