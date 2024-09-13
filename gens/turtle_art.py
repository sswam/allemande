import turtle
import math

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def draw_prime_fib_art(size):
    screen = turtle.Screen()
    screen.setup(800, 800)
    screen.bgcolor("black")

    t = turtle.Turtle()
    t.speed(0)
    t.hideturtle()

    colors = ["red", "orange", "yellow", "green", "blue", "purple"]

    for i in range(size):
        if is_prime(i):
            t.pencolor(colors[i % len(colors)])
            t.circle(fibonacci(i % 20) * 5, steps=i % 8 + 3)
            t.right(fibonacci(i % 10) * 10)
        else:
            t.penup()
            t.forward(fibonacci(i % 15))
            t.left(137.5)
            t.pendown()

    screen.exitonclick()

draw_prime_fib_art(100)

