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
	int exec_mode;
};

/* Print usage information */
static void usage(FILE *stream, char *argv0)
{
	fprintf(stream, "Usage: %s [OPTIONS] [MESSAGE]\n", basename(argv0));
	fprintf(stream, "Display MESSAGE in a window, reading from stdin if MESSAGE not provided.\n");
	fprintf(stream, "Close the window by pressing a key or clicking the mouse.\n");
	fprintf(stream, "Options:\n");
	fprintf(stream, "  -h, --help         Print this help message\n");
	fprintf(stream, "  -s, --size SIZE    Set the font size (default: %d)\n", DEFAULT_SIZE);
	fprintf(stream, "  -e, --exec         Exec command on losing focus\n");
}

/* Get options from the command line */
int get_options(int argc, char *argv[], struct options *opts)
{
	int status = -1;
	int c;
	static struct option long_options[] = {
		{ "help", no_argument, /*@null@ */ NULL, (int) 'h' },
		{ "size", required_argument, /*@null@ */ NULL, (int) 's' },
		{ "exec", no_argument, /*@null@ */ NULL, (int) 'e' },
		{ /*@null@ */ NULL, 0, /*@null@ */ NULL, 0 }
	};

	while ((c = getopt_long(argc, argv, "hs:e", long_options, NULL)) != -1) {
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
		case 'e':
			opts->exec_mode = 1;
			break;
		case '?':
			fprintf(stderr, "Unknown option or missing argument\n\n");
			usage(stderr, argv[0]);
			goto fail;
		default:
			abort();
		}
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
	char **command = NULL;
	int command_argc = 0;

	_opts.size = DEFAULT_SIZE;
	_opts.exec_mode = 0;
	opts = &_opts;
	status = EXIT_FAILURE;
	display = NULL;
	window = 0;
	font = NULL;
	draw = NULL;
	text = NULL;

	if ((get_options(argc, argv, opts)) != 0)
		goto fail;

	// after get_options, before text allocation
	if (opts->exec_mode) {
		if (optind >= argc) {
			fprintf(stderr, "No message provided for exec mode\n");
			goto fail;
		}
		text = strdup(argv[optind]);
		if (text == NULL) {
			perror("Failed to allocate memory for message");
			goto fail;
		}
		command_argc = argc - optind - 1;
		if (command_argc > 0) {
			command = malloc((command_argc + 1) * sizeof(char *));
			if (command == NULL) {
				perror("Failed to allocate memory for command");
				goto fail;
			}
			for (int i = 0; i < command_argc; i++) {
				command[i] = argv[optind + 1 + i];
			}
			command[command_argc] = NULL;
			// duplicate new argv[0]
			command[0] = strdup(command[0]);
			if (command[0] == NULL) {
				perror("Failed to duplicate command argv[0]");
				free(command);
				command = NULL;
				goto fail;
			}
		}
		optind = argc; // consume all
	} else {
		// existing text allocation code
		if (optind < argc) {
			size_t total_len = 0;
			for (int i = optind; i < argc; i++) {
				total_len += strlen(argv[i]) + 1; // +1 for space or null
			}
			if ((text = malloc(total_len)) == NULL) {
				perror("Failed to allocate memory for message");
				goto fail;
			}
			char *p = text;
			for (int i = optind; i < argc; i++) {
				strcpy(p, argv[i]);
				p += strlen(argv[i]);
				if (i + 1 < argc) {
					*p++ = ' ';
				}
			}
			*p = '\0';
		} else {
			if ((text = read_stdin()) == NULL) {
				perror("Failed to read from stdin");
				goto fail;
			}
		}
	}

	if ((display = XOpenDisplay(NULL)) == NULL) {
		perror("Cannot open display");
		goto fail;
	}
	screen = DefaultScreen(display);

	window = XCreateSimpleWindow(display, RootWindow(display, screen), 0, 0, DEFAULT_WIDTH, DEFAULT_HEIGHT, 1, BlackPixel(display, screen), WhitePixel(display, screen));
	XSelectInput(display, window, ExposureMask | KeyPressMask | ButtonPressMask | FocusChangeMask);
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
			// remove extents calculation since unused
			// calculate line_height once after font load, but for now keep as secondary fix
			int line_height = font->ascent + font->descent;
			int y = font->ascent + 10;
			// Create a mutable copy of text because strtok modifies its input
			char *text_copy = strdup(text);
			if (text_copy == NULL) {
				perror("Failed to duplicate text for strtok");
				goto fail;
			}
			char *line = strtok(text_copy, "\n");
			while (line != NULL) {
				XftDrawString8(draw, &color, font, 10, y, (XftChar8 *)line, strlen(line));
				y += line_height;
				line = strtok(NULL, "\n");
			}
			free(text_copy); // Free the duplicated text
		} else if (event.type == KeyPress) {
			KeySym keysym = XLookupKeysym(&event.xkey, 0);
			if (keysym == XK_q || keysym == XK_Escape) {
				break;
			}
		} else if (event.type == FocusOut && opts->exec_mode && command) {
			execvp(command[0], command);
			perror("Failed to exec command");
			// If exec fails, continue or exit? But according to guidance, return error, but since in loop, perhaps break
			break;
		}
	}

	XftColorFree(display, DefaultVisual(display, screen), DefaultColormap(display, screen), &color);
	XftDrawDestroy(draw);
	XftFontClose(display, font);
	XCloseDisplay(display);
	status = EXIT_SUCCESS;
fail:
	if (command) {
		free(command[0]);
		free(command);
	}
	free(text);
	return status;
}

/* known issues:
	* 1. Unused calculation of XftTextExtents8 in Expose handler; suggest removal if not intended for centering or width checks.
	* 2. Potential inefficiency in recalculating line_height per Expose event; consider computing once after font load.
*/
