from boil import *
from random import randint 
from math import *

game = init("Move the Square!", music="theme", volume=0.3, width=2560, height=1440)

def draw_lines():
    for i in range(1000):
        x0 = randint(0, game.width)
        y0 = randint(0, game.height)
        x1 = randint(0, game.width)
        y1 = randint(0, game.height)

        mx = (x0 + x1) / 2
        my = (y0 + y1) / 2

        line((x0, y0), (x1, y1), color="blue")
        r = randint(0, 255)
        g = randint(0, 255)
        b = randint(0, 255)
        circle((mx, my), randint(2, 35), color=(r, g, b))

x0 = game.width / 2
y0 = 0
x1 = x0 + (game.height - 1) * tan(radians(30))
y1 = (game.height - 1)
x2 = x0 - (game.height - 1) * tan(radians(30))
y2 = (game.height - 1)

def tri(x0, y0, x1, y1, x2, y2):
    move((x0, y0))
    draw((x1, y1))
    draw((x2, y2))
    draw((x0, y0))

def mid(x0, y0, x1, y1):
    mx = (x0 + x1) / 2
    my = (y0 + y1) / 2
    return mx, my

def sierpinski_gasket(x0, y0, x1, y1, x2, y2, depth):
    if depth == 0:
        return
    # tri(x0, y0, x1, y1, x2, y2)
    mx0, my0 = mid(x0, y0, x1, y1)
    mx1, my1 = mid(x1, y1, x2, y2)
    mx2, my2 = mid(x2, y2, x0, y0)
    tri(mx0, my0, mx1, my1, mx2, my2)
    sierpinski_gasket(x0, y0, mx0, my0, mx2, my2, depth - 1)
    sierpinski_gasket(mx0, my0, x1, y1, mx1, my1, depth - 1)
    sierpinski_gasket(mx2, my2, mx1, my1, x2, y2, depth - 1)

f = 2 ** (1/35)

while playing():
    draw_lines()

    sierpinski_gasket(x0, y0, x1, y1, x2, y2, 8)
    sierpinski_gasket(x0, y0, x1, y1, x0 + (x1-x0)*2, y0, 8)
    sierpinski_gasket(x0, y0, x2, y2, x0 - (x1-x0)*2, y0, 8)
#    sierpinski_gasket(x0, y0, x1, y1, x2, y2, 9)

    x0 = (x0 - game.width / 2) * f + game.width / 2
    y0 *= f
    x1 = (x1 - game.width / 2) * f + game.width / 2
    y1 *= f
    x2 = (x2 - game.width / 2) * f + game.width / 2
    y2 *= f
    if y1 >= game.height * 2 / f:
        x0 = game.width / 2
        y0 = 0
        x1 = x0 + (game.height - 1) * tan(radians(30))
        y1 = (game.height - 1)
        x2 = x0 - (game.height - 1) * tan(radians(30))
        y2 = (game.height - 1)









 
    # line((0, 0), (game.width, game.height))
    # line((game.width, 0), (0, game.height))
    # triangle((100, 100), (700, 100), (400, 500), "yellow")
    # circle((game.width // 2, game.height // 2), 100, "blue")
    # move_player()
    # draw_player()
    # bump(sound="bump", volume=0.5)
