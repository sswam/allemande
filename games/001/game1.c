/* This program creates an interactive graphical display with random lines,
	* circles, and a recursive Sierpinski gasket pattern that grows over time.
	*/

#include <GL/glut.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <SDL2/SDL.h>
#include <SDL2/SDL_mixer.h>

#define _USE_MATH_DEFINES

#define WINDOW_TITLE "Sierpinski"
#define WINDOW_WIDTH 3440
#define WINDOW_HEIGHT 1440

/* Global state */
struct game_state {
	double x0, y0;
	double x1, y1;
	double x2, y2;
	double f;
} state;

static Mix_Music *music = NULL;

static void cleanup(void)
{
	if (music) {
		Mix_FreeMusic(music);
		music = NULL;
	}
	Mix_CloseAudio();
	SDL_Quit();
}

static int init_audio(void)
{
	if (SDL_Init(SDL_INIT_AUDIO) < 0) {
		fprintf(stderr, "SDL init failed: %s\n", SDL_GetError());
		return -1;
	}

	if (Mix_OpenAudio(44100, MIX_DEFAULT_FORMAT, 2, 2048) < 0) {
		fprintf(stderr, "SDL_mixer init failed: %s\n", Mix_GetError());
		return -1;
	}

	music = Mix_LoadMUS("music/theme.ogg");
	if (!music) {
		fprintf(stderr, "Failed to load music: %s\n", Mix_GetError());
		return -1;
	}

	if (Mix_PlayMusic(music, -1) < 0) {
		fprintf(stderr, "Failed to play music: %s\n", Mix_GetError());
		return -1;
	}

	return 0;
}

static void init_gl(void)
{
	glClearColor(0.0f, 0.0f, 0.0f, 0.0f);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	gluOrtho2D(0.0, (GLdouble)WINDOW_WIDTH, (GLdouble)WINDOW_HEIGHT, 0.0);
}

static void draw_line(double x0, double y0, double x1, double y1)
{
	glBegin(GL_LINES);
	glVertex2d(x0, y0);
	glVertex2d(x1, y1);
	glEnd();
}

static void draw_circle(double cx, double cy, double radius)
{
	int segments = 32;
	double theta = 2.0 * M_PI / segments;

	glBegin(GL_POLYGON);
	for (int i = 0; i < segments; i++) {
		double x = cx + radius * cos(i * theta);
		double y = cy + radius * sin(i * theta);
		glVertex2d(x, y);
	}
	glEnd();
}

static void draw_random_lines(void)
{
	for (int i = 0; i < 10000; i++) {
		double x0 = rand() % WINDOW_WIDTH;
		double y0 = rand() % WINDOW_HEIGHT;
		double x1 = rand() % WINDOW_WIDTH;
		double y1 = rand() % WINDOW_HEIGHT;
		double mx = (x0 + x1) / 2;
		double my = (y0 + y1) / 2;

		glColor3f(0.0, 0.0, 1.0);
		draw_line(x0, y0, x1, y1);

		glColor3f((double)(rand() % 256) / 255.0, (double)(rand() % 256) / 255.0,
			  (double)(rand() % 256) / 255.0);
		draw_circle(mx, my, rand() % 34 + 2);
	}
}

static void draw_tri(double x0, double y0, double x1, double y1, double x2, double y2)
{
	draw_line(x0, y0, x1, y1);
	draw_line(x1, y1, x2, y2);
	draw_line(x2, y2, x0, y0);
}

static void mid_point(double x0, double y0, double x1, double y1, double *mx, double *my)
{
	*mx = (x0 + x1) / 2;
	*my = (y0 + y1) / 2;
}

static void sierpinski_gasket(double x0, double y0, double x1, double y1, double x2, double y2,
			      int depth)
{
	if (depth == 0)
		return;

	double mx0, my0, mx1, my1, mx2, my2;

	mid_point(x0, y0, x1, y1, &mx0, &my0);
	mid_point(x1, y1, x2, y2, &mx1, &my1);
	mid_point(x2, y2, x0, y0, &mx2, &my2);

	draw_tri(mx0, my0, mx1, my1, mx2, my2);

	sierpinski_gasket(x0, y0, mx0, my0, mx2, my2, depth - 1);
	sierpinski_gasket(mx0, my0, x1, y1, mx1, my1, depth - 1);
	sierpinski_gasket(mx2, my2, mx1, my1, x2, y2, depth - 1);
}

static void reset_triangle(void)
{
	state.x0 = WINDOW_WIDTH / 2;
	state.y0 = 0;
	state.x1 = state.x0 + (WINDOW_HEIGHT - 1) * tan(30 * M_PI / 180);
	state.y1 = WINDOW_HEIGHT - 1;
	state.x2 = state.x0 - (WINDOW_HEIGHT - 1) * tan(30 * M_PI / 180);
	state.y2 = WINDOW_HEIGHT - 1;
}

static void display(void)
{
	glClear(GL_COLOR_BUFFER_BIT);

	draw_random_lines();
	glColor3f(1.0, 1.0, 1.0);

	sierpinski_gasket(state.x0, state.y0, state.x1, state.y1, state.x2, state.y2, 10);
	sierpinski_gasket(state.x0, state.y0, state.x1, state.y1,
			  state.x0 + (state.x1 - state.x0) * 2, state.y0, 10);
	sierpinski_gasket(state.x0, state.y0, state.x2, state.y2,
			  state.x0 - (state.x1 - state.x0) * 2, state.y0, 10);

	state.x0 = (state.x0 - WINDOW_WIDTH / 2) * state.f + WINDOW_WIDTH / 2;
	state.y0 *= state.f;
	state.x1 = (state.x1 - WINDOW_WIDTH / 2) * state.f + WINDOW_WIDTH / 2;
	state.y1 *= state.f;
	state.x2 = (state.x2 - WINDOW_WIDTH / 2) * state.f + WINDOW_WIDTH / 2;
	state.y2 *= state.f;

	if (state.y1 >= WINDOW_HEIGHT * 2 / state.f)
		reset_triangle();

	glutSwapBuffers();
	glutPostRedisplay();
}

static void init_state(void)
{
	state.f = pow(2, 1.0 / 35.0);
	reset_triangle();
}

int main(int argc, char *argv[])
{
	srand(time(NULL));

	if (init_audio() < 0) {
		cleanup();
		return EXIT_FAILURE;
	}

	glutInit(&argc, argv);
	glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB);
	glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT);
	glutCreateWindow(WINDOW_TITLE);

	init_gl();
	init_state();

	glutDisplayFunc(display);
	atexit(cleanup);
	glutMainLoop();

	return EXIT_SUCCESS;
}
