//#!/usr/bin/env ccx
/* This program searches lines in a text file, like look(1).
 * It can show lines before or after a match if no exact match is found.
 * Version 1.0.2
 */

#include <errno.h>
#include <getopt.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#define MAX_LINE 4096

struct options {
	char *pattern;
	char *filename;
	int before;
	int after;
};

static char *program_name = NULL;

static void usage(FILE *stream, char *argv0)
{
	fprintf(stream, "Usage: %s [OPTIONS] pattern file\n", basename(argv0));
	fprintf(stream, "Options:\n");
	fprintf(stream, "  -h, --help            Print this help message\n");
	fprintf(stream, "  -b, --before          Show line before match if no exact match\n");
	fprintf(stream, "  -a, --after           Show line after match if no exact match\n");
}

static int get_options(int argc, char *argv[], struct options *opts)
{
	int status = -1;
	int c;
	static struct option long_options[] = {
		{"help", no_argument, NULL, 'h'},
		{"before", no_argument, NULL, 'b'},
		{"after", no_argument, NULL, 'a'},
		{NULL, 0, NULL, 0}
	};

	while ((c = getopt_long(argc, argv, "hbas", long_options, NULL)) != -1) {
		switch (c) {
		case 'h':
			usage(stdout, argv[0]);
			exit(EXIT_SUCCESS);
		case 'b':
			opts->before = 1;
			break;
		case 'a':
			opts->after = 1;
			break;
		case '?':
			usage(stderr, argv[0]);
			goto done;
		}
	}

	if (optind >= argc) {
		fprintf(stderr, "Missing pattern argument\n");
		usage(stderr, argv[0]);
		goto done;
	}

	opts->pattern = argv[optind];
	optind++;

	if (optind >= argc) {
		fprintf(stderr, "Missing file argument\n");
		usage(stderr, argv[0]);
		goto done;
	}

	opts->filename = argv[optind];
	status = 0;
done:
	return status;
}

static int search_lines(FILE *input, struct options *opts)
{
	char prev[MAX_LINE] = "";
	char curr[MAX_LINE] = "";
	char next[MAX_LINE] = "";
	int found = 0;
	int cmp;

	if (!fgets(curr, sizeof(curr), input))
		return 0;

	for (;;) {
 	       	if (fgets(next, sizeof(next), input) == NULL)
			strcpy(next, "\xff"); // sentinel value

		cmp = strncmp(opts->pattern, curr, strlen(opts->pattern));

		// fprintf(stderr, "%s,%s,%s: %d\n", prev, curr, next, cmp);

		if (cmp == 0) {
			fputs(curr, stdout);
			found = 1;
		} else if (cmp < 0 && opts->before) {
			fputs(prev, stdout);
			found = 1;
		} else if (strcmp(next, "\xff") == 0 && cmp > 0 && opts->before) {
			fputs(curr, stdout);
			found = 1;
		} else if (cmp < 0 && opts->after) {
			fputs(curr, stdout);
			found = 1;
		}

		if (found || strcmp(next, "\xff") == 0)
			break;

		strcpy(prev, curr);
		strcpy(curr, next);
	}

	return found;
}

#ifdef TEST
#define MAIN_FUNCTION main_testable
#else
#define MAIN_FUNCTION main
#endif

int MAIN_FUNCTION(int argc, char *argv[])
{
	struct options opts = {NULL, NULL, 0, 0};
	FILE *input = NULL;
	int status = EXIT_FAILURE;

	program_name = argv[0];

	if (get_options(argc, argv, &opts) != 0)
		goto done;

	input = fopen(opts.filename, "r");
	if (!input) {
		perror(opts.filename);
		goto done;
	}

	if (search_lines(input, &opts) == 0)
		goto cleanup;

	status = EXIT_SUCCESS;

cleanup:
	if (input)
		fclose(input);
done:
	return status;
}
