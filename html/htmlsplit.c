/* Split HTML content into one tag per line, making it easier to process
 * with line-oriented tools.
 */

#define _GNU_SOURCE
#include <errno.h>
#include <getopt.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_BUFFER 4096
#define DEFAULT_CHUNK_SIZE 4096

struct options {
	size_t chunk_size;
};

static void usage(FILE *stream, char *argv0)
{
	fprintf(stream, "Usage: %s [OPTIONS]\n", basename(argv0));
	fprintf(stream, "Options:\n");
	fprintf(stream, "  -h, --help            Print this help message\n");
	fprintf(stream, "  -c, --chunk-size=SIZE Buffer size for reading (default: %d)\n",
		DEFAULT_CHUNK_SIZE);
}

static int get_options(int argc, char *argv[], struct options *opts)
{
	int status = -1;
	int c;
	/*@null@*/ static struct option long_options[] = {
	    {"help", no_argument, /*@null@*/ NULL, (int)'h'},
	    {"chunk-size", required_argument, /*@null@*/ NULL, (int)'c'},
	    {/*@null@*/ NULL, 0, /*@null@*/ NULL, 0}};

	opts->chunk_size = DEFAULT_CHUNK_SIZE;

	while ((c = getopt_long(argc, argv, "hc:", long_options, /*@null@*/ NULL)) != -1) {
		switch (c) {
		case 'h':
			usage(stdout, argv[0]);
			status = EXIT_SUCCESS;
			goto done;
		case 'c': {
			char *endptr;
			long size = strtol(optarg, &endptr, 10);
			if (*endptr != '\0' || size <= 0) {
				fprintf(stderr, "Invalid chunk size: %s\n", optarg);
				goto done;
			}
			opts->chunk_size = (size_t)size;
			break;
		}
		case '?':
			fprintf(stderr, "Unknown option or missing argument\n\n");
			usage(stderr, argv[0]);
			goto done;
		default:
			abort();
		}
	}

	if (optind < argc) {
		fprintf(stderr, "Unexpected argument: %s\n\n", argv[optind]);
		usage(stderr, argv[0]);
		goto done;
	}

	status = 0;
done:
	return status;
}

static int ensure_buffer_space(char **buffer, size_t *buf_size, size_t needed_size,
			       size_t chunk_size)
{
	if (needed_size <= *buf_size)
		return 0;

	size_t new_size = needed_size + chunk_size;
	char *new_buffer = realloc(*buffer, new_size);
	if (new_buffer == NULL) {
		perror("Failed to resize buffer");
		return -1;
	}

	*buffer = new_buffer;
	*buf_size = new_size;
	return 0;
}

static int process_complete_tags(char **buffer, size_t *content_size, FILE *output)
{
	char *start = *buffer;
	char *tag_start;
	char *tag_end;
	char *current = start;

	// Process each tag found in the buffer
	while ((tag_start = strchr(current, '<')) != NULL) {
		if (tag_start > current) {
			char saved = *tag_start;
			*tag_start = '\0';
			if (fprintf(output, "%s\n", current) < 0) {
				perror("Error writing output");
				return -1;
			}
			*tag_start = saved;
		}

		tag_end = strchr(tag_start, '>');
		if (!tag_end) {
			if (tag_start > *buffer) {
				*content_size = strlen(tag_start);
				memmove(*buffer, tag_start, *content_size + 1);
			}
			return 0;
		}

		// Replace newlines with spaces in the tag
		for (char *p = tag_start; p <= tag_end; p++) {
			if (*p == '\n') {
				*p = ' ';
			}
		}

		char saved = tag_end[1];
		tag_end[1] = '\0';
		if (fprintf(output, "%s\n", tag_start) < 0) {
			perror("Error writing output");
			return -1;
		}
		tag_end[1] = saved;
		current = tag_end + 1;
	}

	if (*current != '\0') {
		*content_size = strlen(current);
		memmove(*buffer, current, *content_size + 1);
	} else {
		*content_size = 0;
		**buffer = '\0';
	}

	return 0;
}

static int process_html(FILE *input, FILE *output, size_t chunk_size)
{
	char *buffer = NULL;
	size_t buf_size = 0;
	size_t content_size = 0;
	int status = -1;
	char chunk[MAX_BUFFER];

	buffer = malloc(chunk_size);
	if (buffer == NULL) {
		perror("Failed to allocate buffer");
		goto done;
	}
	buf_size = chunk_size;
	buffer[0] = '\0';

	while (!feof(input)) {
		size_t bytes_read = fread(chunk, 1, sizeof(chunk), input);
		if (ferror(input)) {
			perror("Error reading input");
			goto cleanup;
		}

		if (ensure_buffer_space(&buffer, &buf_size, content_size + bytes_read + 1,
					chunk_size) != 0)
			goto cleanup;

		memcpy(buffer + content_size, chunk, bytes_read);
		content_size += bytes_read;
		buffer[content_size] = '\0';

		if (process_complete_tags(&buffer, &content_size, output) != 0)
			goto cleanup;
	}

	if (content_size > 0) {
		if (fprintf(output, "%s\n", buffer) < 0) {
			perror("Error writing final output");
			goto cleanup;
		}
	}

	status = 0;

cleanup:
	free(buffer);
done:
	return status;
}

#ifdef TEST
#define MAIN_FUNCTION main_testable
#else
#define MAIN_FUNCTION main
#endif

int MAIN_FUNCTION(int argc, char *argv[])
{
	int status = EXIT_FAILURE;
	struct options opts = {DEFAULT_CHUNK_SIZE};

	if (get_options(argc, argv, &opts) != 0)
		goto done;

	status = process_html(stdin, stdout, opts.chunk_size);

done:
	return status;
}
