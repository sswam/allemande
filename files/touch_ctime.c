#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <getopt.h>
#include <libgen.h>
#include <linux/stat.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

/* Print usage information */
static void usage(FILE *stream, const char *argv0)
{
	char *prog;

	prog = strdup(argv0);
	fprintf(stream, "Usage: %s [OPTIONS] [FILE ...]\n", basename(prog));
	free(prog);
	fprintf(stream, "Update the ctime of each FILE.\n\n");
	fprintf(stream, "Options:\n");
	fprintf(stream, "  -h, --help     Display this help and exit\n");
}

/* Update the ctime of a file */
int touch_ctime(const char *filename)
{
	struct statx statxbuf;
	struct timespec times[2];

	if (statx(AT_FDCWD, filename, 0, STATX_ATIME | STATX_MTIME, &statxbuf) == -1) {
		fprintf(stderr, "Error reading file times for %s: %s\n", filename, strerror(errno));
		return -1;
	}

	times[0].tv_sec = statxbuf.stx_atime.tv_sec;
	times[0].tv_nsec = statxbuf.stx_atime.tv_nsec;
	times[1].tv_sec = statxbuf.stx_mtime.tv_sec;
	times[1].tv_nsec = statxbuf.stx_mtime.tv_nsec;

	if (utimensat(AT_FDCWD, filename, times, 0) == -1) {
		fprintf(stderr, "Error touching %s: %s\n", filename, strerror(errno));
		return -1;
	}
	return 0;
}

#ifdef TEST
#define MAIN_FUNCTION main_testable
#else
#define MAIN_FUNCTION main
#endif

/* Main function */
int MAIN_FUNCTION(int argc, char *argv[])
{
	int opt;
	int exit_status = EXIT_SUCCESS;
	static struct option long_options[] = {
		{"help", no_argument, NULL, 'h'},
		{NULL, 0, NULL, 0}
	};

	while ((opt = getopt_long(argc, argv, "h", long_options, NULL)) != -1) {
		switch (opt) {
		case 'h':
			usage(stdout, argv[0]);
			return EXIT_SUCCESS;
		default:
			usage(stderr, argv[0]);
			return EXIT_FAILURE;
		}
	}

	for (int i = optind; i < argc; i++) {
		if (touch_ctime(argv[i]) != 0)
			exit_status = EXIT_FAILURE;
	}

	return exit_status;
}
