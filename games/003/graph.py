#!/usr/bin/env python3

"""

Uses the boil game engine for graphics.

Resolution: 2560x1440
Background music: "theme" at 30% volume
"""

from boil import *
from random import randint
from math import *


x0, x1 = -100, 100
y0, y1 = -220, 220
x_tick, y_tick = 10, 10

def fn(x):
	return x*9/5+32


x0, x1 = -2*pi, 2*pi
y0, y1 = -1, 1
x_tick, y_tick = 1/2*pi, 1/2

def fn(x):
	return cos(x)



x0, x1 = -1, 1
y0, y1 = -1, 1
x_tick, y_tick = 1/2, 1/2

def fn(x):
	return sqrt(1-x**2)
def fn2(x):
	return -sqrt(1-x**2)

fns = [fn, fn2]



x0, x1 = -3, 3
y0, y1 = -1, 1

def fn(x):
	y = sin(x)
	return y


fns = [lambda x: sin(x), lambda x: cos(x)]


game = init("Graph", music="theme2", volume=0.3, width=1440, height=1440)

margin = 50

xp0 = margin
xp1 = game.width - 1 - margin

yp0 = game.height - 1 - margin
yp1 = margin




def main():
	while playing():
		# draw x-axis
		yaxis_p = y_to_pixel(0)
		line((xp0, yaxis_p), (xp1, yaxis_p))

		# draw y-axis
		xaxis_p = x_to_pixel(0)
		line((xaxis_p, yp0), (xaxis_p, yp1))

		# draw ticks on the x-axis
		xt0 = x0 - x0 % x_tick
		xt1 = x1 - x1 % x_tick
		x = xt0
		while x <= xt1:
			xp = x_to_pixel(x)
			line((xp, yaxis_p - 5), (xp, yaxis_p + 5))
			x += x_tick

		# draw ticks on the y-axis
		yt0 = y0 - y0 % y_tick
		yt1 = y1 - y1 % y_tick
		y = yt0
		while y <= yt1:
			yp = y_to_pixel(y)
			line((xaxis_p - 5, yp), (xaxis_p + 5, yp))
			y += y_tick

		for fn in fns:
			plot_function(fn)

def plot_function(fn):
	# loop over each x across the window and plot the graph
	for xp in range(xp0, xp1 + 1):
		x = pixel_to_x(xp)
		y = fn(x)
		yp = y_to_pixel(y)

		if xp == xp0:
			move((xp, yp))
		else:
			draw((xp, yp), "red")


def point(p, color="white"):
    """Draw a point"""
    circle(p, 1, color)

def pixel_to_x(xp):
	x = (xp - xp0) / (xp1 - xp0) * (x1 - x0) + x0
	return x

def pixel_to_y(yp):
	y = (yp - yp0) / (yp1 - yp0) * (y1 - y0) + y0
	return y

def x_to_pixel(x):
	xp = (x - x0) / (x1-x0) * (xp1 - xp0) + xp0
	return xp

def y_to_pixel(y):
	yp = (y - y0) / (y1-y0) * (yp1 - yp0) + yp0
	return yp


main()