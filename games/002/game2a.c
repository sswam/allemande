/* This program draws gradient triangles using SDL2, plotting points instead
* of circles. It demonstrates basic graphics and animation concepts.
*/

#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define WINDOW_WIDTH 2560
#define WINDOW_HEIGHT 1440
#define POINTS_PER_SIDE 500

/* Unused parameters */
static void unused_parameters(int argc, char *argv[])
{
	(void)argc;
	(void)argv;
}

struct point {
	int x;
	int y;
};

struct color {
	uint8_t r;
	uint8_t g;
	uint8_t b;
};

static uint32_t *framebuffer;

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
	c.r = (uint8_t)(rand() % 256);
	c.g = (uint8_t)(rand() % 256);
	c.b = (uint8_t)(rand() % 256);
	return c;
}

static int blend_int(int a, int x0, int x1)
{
	return x0 + ((x1 - x0) * a) / (POINTS_PER_SIDE - 1);
}

static void draw_gradient_triangle(uint32_t *pixels, struct point p0, struct point p1,
								struct point p2, struct color c0, struct color c1,
								struct color c2)
{
	for (int i = 0; i < POINTS_PER_SIDE; i++) {
		int x3 = blend_int(i, p0.x, p1.x);
		int y3 = blend_int(i, p0.y, p1.y);

		int r3 = blend_int(i, c0.r, c1.r);
		int g3 = blend_int(i, c0.g, c1.g);
		int b3 = blend_int(i, c0.b, c1.b);

		for (int j = 0; j < POINTS_PER_SIDE; j++) {
			int x4 = blend_int(j, x3, p2.x);
			int y4 = blend_int(j, y3, p2.y);

			int r4 = blend_int(j, r3, c2.r);
			int g4 = blend_int(j, g3, c2.g);
			int b4 = blend_int(j, b3, c2.b);

			if (x4 >= 0 && x4 < WINDOW_WIDTH && y4 >= 0 && y4 < WINDOW_HEIGHT) {
				pixels[y4 * WINDOW_WIDTH + x4] = (0xFF000000 | (r4 << 16) | (g4 << 8) | b4);
			}
		}
	}
}

int main(int argc, char *argv[])
{
	SDL_Window *window = NULL;
	SDL_Renderer *renderer = NULL;
	SDL_Texture *texture = NULL;
	int status = EXIT_FAILURE;
	SDL_Event event;
	int running = 1;

	unused_parameters(argc, argv);

	if (SDL_Init(SDL_INIT_VIDEO) < 0) {
		fprintf(stderr, "SDL initialization failed: %s\n", SDL_GetError());
		goto done;
	}

	window = SDL_CreateWindow("Gradient Triangles", SDL_WINDOWPOS_UNDEFINED,
							SDL_WINDOWPOS_UNDEFINED, WINDOW_WIDTH, WINDOW_HEIGHT,
							SDL_WINDOW_SHOWN);
	if (!window) {
		fprintf(stderr, "Window creation failed: %s\n", SDL_GetError());
		goto cleanup_sdl;
	}

	renderer = SDL_CreateRenderer(window, -1,
								SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
	if (!renderer) {
		fprintf(stderr, "Renderer creation failed: %s\n", SDL_GetError());
		goto cleanup_window;
	}

	texture = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_RGBA8888,
							SDL_TEXTUREACCESS_STREAMING, WINDOW_WIDTH, WINDOW_HEIGHT);
	if (!texture) {
		fprintf(stderr, "Texture creation failed: %s\n", SDL_GetError());
		goto cleanup_renderer;
	}

	framebuffer = calloc(WINDOW_WIDTH * WINDOW_HEIGHT, sizeof(uint32_t));
	if (!framebuffer) {
		fprintf(stderr, "Failed to allocate framebuffer\n");
		goto cleanup_texture;
	}

	srand(time(NULL));

	while (running) {
		while (SDL_PollEvent(&event)) {
			if (event.type == SDL_QUIT)
				running = 0;
		}

		memset(framebuffer, 0, WINDOW_WIDTH * WINDOW_HEIGHT * sizeof(uint32_t));

		for (int i = 0; i < 5; i++) {
			struct point p0 = random_point();
			struct point p1 = random_point();
			struct point p2 = random_point();
			struct color c0 = random_color();
			struct color c1 = random_color();
			struct color c2 = random_color();

			draw_gradient_triangle(framebuffer, p0, p1, p2, c0, c1, c2);
		}

		SDL_UpdateTexture(texture, NULL, framebuffer, WINDOW_WIDTH * sizeof(uint32_t));
		SDL_RenderCopy(renderer, texture, NULL, NULL);
		SDL_RenderPresent(renderer);
	}

	status = EXIT_SUCCESS;

	free(framebuffer);
cleanup_texture:
	SDL_DestroyTexture(texture);
cleanup_renderer:
	SDL_DestroyRenderer(renderer);
cleanup_window:
	SDL_DestroyWindow(window);
cleanup_sdl:
	SDL_Quit();
done:
	return status;
}

// I'll modify the code to use a 2D array for rendering and optimize the color calculations. Here's the optimized version:

// Key changes:
// 1. Added a framebuffer array to store pixels
// 2. Changed color blending to use integer math
// 3. Changed rendering to use a texture and update it all at once
// 4. Added proper error handling for texture creation and framebuffer allocation
// 5. Fixed unused parameter warnings
// 6. Improved cleanup handling using goto
// 7. Added bounds checking in fill_circle
//
// This version should be significantly faster as it:
// 1. Uses integer math instead of floating point
// 2. Updates the screen all at once instead of per-pixel
// 3. Uses a more efficient memory access pattern
// 4. Reduces the number of SDL calls
