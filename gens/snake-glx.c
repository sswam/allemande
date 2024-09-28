// 2>/dev/null; set -e; X=${0%.c} ; [ "$X" -nt "$0" ] || cc -o "$X" -I$HOME/kisskit "$0" -lX11 -lGL -lm && hide "$X"; exec "$X" "$@"

#include <X11/Xlib.h>
#include <GL/glx.h>
#include <GL/gl.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>
#include <time.h>

#define WINDOW_WIDTH 800
#define WINDOW_HEIGHT 600
#define GRID_SIZE 20
#define SNAKE_INITIAL_LENGTH 3

typedef struct {
	int x;
	int y;
} Point;

Point snake[100];
int snake_length = SNAKE_INITIAL_LENGTH;
Point food;
enum Direction { UP, DOWN, LEFT, RIGHT } direction = RIGHT;

Display *dpy;
Window win;
GLXContext glc;

void init_x() {
	dpy = XOpenDisplay(NULL);
	if (dpy == NULL) {
		exit(1);
	}

	Window root = DefaultRootWindow(dpy);

	GLint att[] = { GLX_RGBA, GLX_DEPTH_SIZE, 24, GLX_DOUBLEBUFFER, None };
	XVisualInfo *vi = glXChooseVisual(dpy, 0, att);

	XSetWindowAttributes swa;
	swa.colormap = XCreateColormap(dpy, root, vi->visual, AllocNone);
	swa.event_mask = ExposureMask | KeyPressMask;

	win = XCreateWindow(dpy, root, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0, vi->depth, InputOutput, vi->visual, CWColormap | CWEventMask, &swa);
	XMapWindow(dpy, win);
	XStoreName(dpy, win, "Snake Game");

	glc = glXCreateContext(dpy, vi, NULL, GL_TRUE);
	glXMakeCurrent(dpy, win, glc);
}

void init_gl() {
	glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	glOrtho(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0, -1, 1);
	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
}

void init_game() {
	for (int i = 0; i < snake_length; i++) {
		snake[i].x = (WINDOW_WIDTH / 2) - (i * GRID_SIZE);
		snake[i].y = WINDOW_HEIGHT / 2;
	}

	srand(time(NULL));
	food.x = (rand() % (WINDOW_WIDTH / GRID_SIZE)) * GRID_SIZE;
	food.y = (rand() % (WINDOW_HEIGHT / GRID_SIZE)) * GRID_SIZE;
}

void draw_square(int x, int y) {
	glBegin(GL_QUADS);
	glVertex2f(x, y);
	glVertex2f(x + GRID_SIZE, y);
	glVertex2f(x + GRID_SIZE, y + GRID_SIZE);
	glVertex2f(x, y + GRID_SIZE);
	glEnd();
}

void draw() {
	glClear(GL_COLOR_BUFFER_BIT);

	// Draw snake
	glColor3f(0.0, 1.0, 0.0);
	for (int i = 0; i < snake_length; i++) {
		draw_square(snake[i].x, snake[i].y);
	}

	// Draw food
	glColor3f(1.0, 0.0, 0.0);
	draw_square(food.x, food.y);

	glXSwapBuffers(dpy, win);
}

void move_snake() {
	for (int i = snake_length - 1; i > 0; i--) {
		snake[i] = snake[i - 1];
	}

	switch (direction) {
		case UP:    snake[0].y -= GRID_SIZE; break;
		case DOWN:  snake[0].y += GRID_SIZE; break;
		case LEFT:  snake[0].x -= GRID_SIZE; break;
		case RIGHT: snake[0].x += GRID_SIZE; break;
	}

	// Check for collision with food
	if (snake[0].x == food.x && snake[0].y == food.y) {
		snake_length++;
		food.x = (rand() % (WINDOW_WIDTH / GRID_SIZE)) * GRID_SIZE;
		food.y = (rand() % (WINDOW_HEIGHT / GRID_SIZE)) * GRID_SIZE;
	}

	// Check for collision with walls
	if (snake[0].x < 0 || snake[0].x >= WINDOW_WIDTH || snake[0].y < 0 || snake[0].y >= WINDOW_HEIGHT) {
		exit(0);
	}

	// Check for collision with self
	for (int i = 1; i < snake_length; i++) {
		if (snake[0].x == snake[i].x && snake[0].y == snake[i].y) {
			exit(0);
		}
	}
}

int main() {
	init_x();
	init_gl();
	init_game();

	XEvent xev;
	bool running = true;

	while (running) {
		if (XPending(dpy) > 0) {
			XNextEvent(dpy, &xev);
			if (xev.type == KeyPress) {
				KeySym key = XLookupKeysym(&xev.xkey, 0);
				switch (key) {
					case XK_Up:    if (direction != DOWN)  direction = UP;    break;
					case XK_Down:  if (direction != UP)    direction = DOWN;  break;
					case XK_Left:  if (direction != RIGHT) direction = LEFT;  break;
					case XK_Right: if (direction != LEFT)  direction = RIGHT; break;
					case XK_Escape: running = false; break;
				}
			}
		}

		move_snake();
		draw();
		usleep(100000);  // Sleep for 100ms
	}

	glXMakeCurrent(dpy, None, NULL);
	glXDestroyContext(dpy, glc);
	XDestroyWindow(dpy, win);
	XCloseDisplay(dpy);
	return 0;
}

// Certainly! Here's a basic implementation of a Snake game using GLX (OpenGL Extension to the X Window System) in C. This example creates a simple Snake game with basic movement and collision detection.

// To compile and run this game, you'll need to have the necessary development libraries installed. On a Debian-based system, you can install them with:

// sudo apt-get install libx11-dev libgl1-mesa-dev

// Then compile the game with:

// gcc snake-glx.c -o snake-glx -lX11 -lGL -lm

// And run it with:

// ./snake-glx

// This implementation creates a basic Snake game where:
//
// 1. The snake starts in the middle of the screen, moving to the right.
// 2. Use arrow keys to change direction.
// 3. Eat the red food to grow.
// 4. The game ends if you hit the wall or yourself.
// 5. Press ESC to quit the game.
//
// Note that this is a basic implementation and can be improved in many ways, such as adding a score, increasing difficulty, or improving graphics.

