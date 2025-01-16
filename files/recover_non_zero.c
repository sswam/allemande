/* This program reads stdin block by block and saves non-zero consecutive blocks
	* to separate files in the current working directory.
	*/

#define _GNU_SOURCE
#include <errno.h>
#include <getopt.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define DEFAULT_BLOCK_SIZE 512
#define MAX_FILENAME 32

/* Options structure */
struct options {
	size_t block_size;
};

/* Print usage information */
static void usage(FILE *stream, char *argv0)
{
	fprintf(stream, "Usage: %s [OPTIONS]\n", basename(argv0));
	fprintf(stream, "Read stdin block by block and save consecutive non-zero blocks to files.\n\n");
	fprintf(stream, "Options:\n");
	fprintf(stream, "  -h, --help            Print this help message\n");
	fprintf(stream, "  -b, --block-size=SIZE Set block size (default: 512)\n");
}

/* Get options from the command line */
static int get_options(int argc, char *argv[], struct options *opts)
{
	int status = -1;
	int c;
	char *endptr;
	static struct option long_options[] = {
		{"help", no_argument, NULL, (int)'h'},
		{"block-size", required_argument, NULL, (int)'b'},
		{NULL, 0, NULL, 0}
	};

	while ((c = getopt_long(argc, argv, "hb:", long_options, NULL)) != -1) {
		switch (c) {
		case 'h':
			usage(stdout, argv[0]);
			exit(0);
		case 'b':
			opts->block_size = strtoul(optarg, &endptr, 0);
			if (*endptr != '\0' || opts->block_size == 0) {
				fprintf(stderr, "Invalid block size: %s\n", optarg);
				goto done;
			}
			break;
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

/* Check if block contains only zeros */
static int is_zero_block(const unsigned char *block, size_t size)
{
	for (size_t i = 0; i < size; i++) {
		if (block[i] != 0)
			return 0;
	}
	return 1;
}

#ifdef TEST
#define MAIN_FUNCTION main_testable
#else
#define MAIN_FUNCTION main
#endif

/* Main function */
int MAIN_FUNCTION(int argc, char *argv[])
{
	int status = EXIT_FAILURE;
	struct options _opts = {DEFAULT_BLOCK_SIZE}, *opts = &_opts;
	unsigned char *block = NULL;
	size_t bytes_read;
	int file_count = 0;
	FILE *outfile = NULL;
	char filename[MAX_FILENAME];
	int in_nonzero_sequence = 0;

	if (get_options(argc, argv, opts) != 0)
		goto done;

	block = malloc(opts->block_size);
	if (block == NULL) {
		perror("Failed to allocate block buffer");
		goto done;
	}

	while ((bytes_read = fread(block, 1, opts->block_size, stdin)) > 0) {
		if (bytes_read < opts->block_size && !feof(stdin)) {
			perror("Read error");
			goto cleanup;
		}

		if (is_zero_block(block, bytes_read)) {
			if (in_nonzero_sequence) {
				if (fclose(outfile) != 0) {
					outfile = NULL;
					perror("Failed to close output file");
					goto cleanup;
				}
				outfile = NULL;
				in_nonzero_sequence = 0;
			}
			continue;
		}

		if (!in_nonzero_sequence) {
			if (snprintf(filename, sizeof(filename), "%06d.bin", file_count++) < 0) {
				fprintf(stderr, "Failed to create filename\n");
				goto cleanup;
			}

			outfile = fopen(filename, "wb");
			if (outfile == NULL) {
				perror("Failed to create output file");
				goto cleanup;
			}
			in_nonzero_sequence = 1;
		}

		if (fwrite(block, 1, bytes_read, outfile) != bytes_read) {
			perror("Failed to write block");
			goto cleanup;
		}
	}

	if (ferror(stdin)) {
		perror("Read error on stdin");
		goto cleanup;
	}

	if (outfile != NULL && fclose(outfile) != 0) {
		outfile = NULL;
		perror("Failed to close output file");
		goto cleanup;
	}

	outfile = NULL;

	status = EXIT_SUCCESS;

cleanup:
	if (outfile != NULL)
		(void)fclose(outfile);
	free(block);
done:
	return status;
}
