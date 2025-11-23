#!/usr/bin/env ccx
// CC: gcc
// CPPFLAGS: -D_GNU_SOURCE
// CFLAGS: -Wall -Wextra -Werror -Wstrict-prototypes -g -ggdb
// INPUTS:
// LDFLAGS:
// LDLIBS: -lX11 -lXft
// PKGS: x11 xft

/* This program is a simple X11 application that displays a message like
 * xmessage, with controllable font size. It reads the message from stdin and
 * exits on Q or Esc keypress */

#include <X11/Xlib.h>
#include <X11/Xft/Xft.h>
#include <errno.h>
#include <getopt.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define DEFAULT_SIZE 24
#define DEFAULT_WIDTH 400
#define DEFAULT_HEIGHT 200

/* Options structure */
struct options {
	int size;
};

/* Print usage information */
static void usage(FILE *stream, char *argv0)
{
	fprintf(stream, "Usage: %s [OPTIONS]\n", basename(argv0));
	fprintf(stream, "Read message from stdin and display in a window with specified font size.\n");
	fprintf(stream, "Close the window by pressing a key or clicking the mouse.\n");
	fprintf(stream, "Options:\n");
	fprintf(stream, "  -h, --help         Print this help message\n");
	fprintf(stream, "  -s, --size SIZE    Set the font size (default: %d)\n", DEFAULT_SIZE);
}

/* Get options from the command line */
int get_options(int argc, char *argv[], struct options *opts)
{
	int status = -1;
	int c;
	static struct option long_options[] = {
		{ "help", no_argument, /*@null@ */ NULL, (int) 'h' },
		{ "size", required_argument, /*@null@ */ NULL, (int) 's' },
		{ /*@null@ */ NULL, 0, /*@null@ */ NULL, 0 }
	};

	while ((c = getopt_long(argc, argv, "hs:", long_options, NULL)) != -1) {
		switch (c) {
		case 'h':
			usage(stdout, argv[0]);
			exit(0);
		case 's':
			opts->size = atoi(optarg);
			if (opts->size <= 0) {
				fprintf(stderr, "Font size must be positive\n");
				goto fail;
			}
			break;
		case '?':
			fprintf(stderr, "Unknown option or missing argument\n\n");
			usage(stderr, argv[0]);
			goto fail;
		default:
			abort();
		}
	}

	if (optind < argc) {
		fprintf(stderr, "Unexpected argument: %s\n\n", argv[optind]);
		usage(stderr, argv[0]);
		goto fail;
	}

	status = 0;
fail:
	return status;
}

/* Read message from stdin into a dynamically allocated string */
static char *read_stdin(void)
{
	char *text;
	size_t capacity;
	size_t pos;

	capacity = 1024;
	if ((text = malloc(capacity)) == NULL)
		goto fail;
	pos = 0;

	while (!feof(stdin)) {
		size_t n;
		if (pos + 1 >= capacity) {
			capacity *= 2;
			if ((text = realloc(text, capacity)) == NULL)
				goto fail;
		}
		n = fread(text + pos, 1, capacity - pos - 1, stdin);
		if (n == 0)
			break;
		pos += n;
	}
	text[pos] = '\0';
	return text;

fail:
	free(text);
	return NULL;
}

#ifdef TEST
#define MAIN_FUNCTION main_testable
#else
#define MAIN_FUNCTION main
#endif

/* Main function */
int MAIN_FUNCTION(int argc, char *argv[])
{
	int status;
	struct options _opts;
	struct options *opts;
	Display *display;
	int screen;
	Window window;
	XEvent event;
	XftFont *font;
	XftDraw *draw;
	XftColor color;
	char *text;

	_opts.size = DEFAULT_SIZE;
	opts = &_opts;
	status = EXIT_FAILURE;
	display = NULL;
	window = 0;
	font = NULL;
	draw = NULL;
	text = NULL;

	if ((get_options(argc, argv, opts)) != 0)
		goto fail;

	if ((text = read_stdin()) == NULL) {
		perror("Failed to read from stdin");
		goto fail;
	}

	if ((display = XOpenDisplay(NULL)) == NULL) {
		perror("Cannot open display");
		goto fail;
	}
	screen = DefaultScreen(display);

	window = XCreateSimpleWindow(display, RootWindow(display, screen), 0, 0, DEFAULT_WIDTH, DEFAULT_HEIGHT, 1, BlackPixel(display, screen), WhitePixel(display, screen));
	XSelectInput(display, window, ExposureMask | KeyPressMask | ButtonPressMask);
	XMapWindow(display, window);

	if ((font = XftFontOpen(display, screen, XFT_FAMILY, XftTypeString, "DejaVu Sans", XFT_SIZE, XftTypeDouble, (double) opts->size, NULL)) == NULL) {
		perror("Cannot load font");
		goto fail;
	}

	if ((draw = XftDrawCreate(display, window, DefaultVisual(display, screen), DefaultColormap(display, screen))) == NULL) {
		perror("Cannot create Xft draw");
		goto fail;
	}

	if (!XftColorAllocName(display, DefaultVisual(display, screen), DefaultColormap(display, screen), "black", &color)) {
		perror("Cannot allocate color");
		goto fail;
	}

	while (1) {
		XNextEvent(display, &event);
		if (event.type == Expose) {
			int x;
			int y;
			x = 10;
			y = opts->size + 10;
			XftDrawString8(draw, &color, font, x, y, (XftChar8 *) text, strlen(text));
		} else if (event.type == KeyPress) {
			KeySym keysym = XLookupKeysym(&event.xkey, 0);
			if (keysym == XK_q || keysym == XK_Escape) {
				break;
			}
		}
	}

	XftColorFree(display, DefaultVisual(display, screen), DefaultColormap(display, screen), &color);
	XftDrawDestroy(draw);
	XftFontClose(display, font);
	XCloseDisplay(display);
	status = EXIT_SUCCESS;
fail:
	free(text);
	return status;
}
