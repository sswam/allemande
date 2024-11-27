/* This program draws gradient triangles using SDL2 render, backed on GL I guess. */

#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define WINDOW_WIDTH 2560
#define WINDOW_HEIGHT 1440
#define POINTS_PER_SIDE 500

struct point {
	int x;
	int y;
};

struct color {
	uint8_t r;
	uint8_t g;
	uint8_t b;
};

static struct point random_point(void)
{
	struct point p;
	p.x = rand() % WINDOW_WIDTH;
	p.y = rand() % WINDOW_HEIGHT;
	return p;
}

static struct color random_color(void)
{
	struct color c;
	c.r = rand() % 256;
	c.g = rand() % 256;
	c.b = rand() % 256;
	return c;
}

// static void render_filled_circle(SDL_Renderer* renderer, int x0, int y0, int radius) {
// 	for (int y = -radius; y <= radius; y++) {
// 		int width = (int)sqrt(radius * radius - y * y);
// 		SDL_RenderDrawLine(renderer, x0 - width, y0 + y, x0 + width, y0 + y);
// 	}
// }

static void draw_gradient_triangle(SDL_Renderer *renderer,
					struct point p0, struct point p1, struct point p2,
					struct color c0, struct color c1, struct color c2)
{
	SDL_Vertex vertices[3] = {
		{ {p0.x, p0.y}, {c0.r, c0.g, c0.b, 255}, { 0, 0 } },
		{ {p1.x, p1.y}, {c1.r, c1.g, c1.b, 255}, { 0, 0 } },
		{ {p2.x, p2.y}, {c2.r, c2.g, c2.b, 255}, { 0, 0 } }
	};

	SDL_RenderGeometry(renderer, NULL, vertices, 3, NULL, 0);
}

#define MAIN_FUNCTION main

int MAIN_FUNCTION(void)
{
	SDL_Window *window = NULL;
	SDL_Renderer *renderer = NULL;
	int status = EXIT_FAILURE;
	SDL_Event event;
	int running = 1;

	if (SDL_Init(SDL_INIT_VIDEO) < 0) {
		fprintf(stderr, "SDL initialization failed: %s\n", SDL_GetError());
		goto done;
	}

	window = SDL_CreateWindow("Gradient Triangles",
					SDL_WINDOWPOS_UNDEFINED,
					SDL_WINDOWPOS_UNDEFINED,
					WINDOW_WIDTH, WINDOW_HEIGHT,
					SDL_WINDOW_SHOWN);
	if (window == NULL) {
		fprintf(stderr, "Window creation failed: %s\n", SDL_GetError());
		goto cleanup_sdl;
	}

	renderer = SDL_CreateRenderer(window, -1,
								SDL_RENDERER_ACCELERATED |
								SDL_RENDERER_PRESENTVSYNC);
	if (renderer == NULL) {
		fprintf(stderr, "Renderer creation failed: %s\n", SDL_GetError());
		goto cleanup_window;
	}

	srand(time(NULL));

	while (running) {
		while (SDL_PollEvent(&event)) {
			if (event.type == SDL_QUIT)
				running = 0;
		}

		SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
		SDL_RenderClear(renderer);

		for (int i = 0; i < 10000; i++) {
			struct point p0 = random_point();
			struct point p1 = random_point();
			struct point p2 = random_point();
			struct color c0 = random_color();
			struct color c1 = random_color();
			struct color c2 = random_color();

			draw_gradient_triangle(renderer, p0, p1, p2, c0, c1, c2);
		}

		SDL_RenderPresent(renderer);
//		SDL_Delay(2000); /* 2 second delay between new triangles */
	}

	status = EXIT_SUCCESS;

	SDL_DestroyRenderer(renderer);
cleanup_window:
	SDL_DestroyWindow(window);
cleanup_sdl:
	SDL_Quit();
done:
	return status;
}
