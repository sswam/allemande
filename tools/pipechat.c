/* This program sets up bidirectional communication between two processes using
* anonymous pipes. Each process's stdout is connected to the other's stdin.
*/

#define _GNU_SOURCE
#include <errno.h>
#include <getopt.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

/* Print usage information */
static void usage(FILE *stream, const char *argv0)
{
    fprintf(stream, "Usage: %s [OPTIONS] cmd1 args... : cmd2 args...\n", argv0);
    fprintf(stream, "Options:\n");
    fprintf(stream, "  -h, --help     Print this help message\n");
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
    int pipe1[2] = {-1, -1}, pipe2[2] = {-1, -1};
    pid_t pid1, pid2;
    int colon_pos = -1;
    int i;

    static const struct option long_options[] = {
        {"help", no_argument, NULL, 'h'},
        {NULL, 0, NULL, 0}
    };

    int c;
    while ((c = getopt_long(argc, argv, "h", long_options, NULL)) != -1) {
        switch (c) {
        case 'h':
            usage(stdout, argv[0]);
            status = EXIT_SUCCESS;
            goto done;
        case '?':
            usage(stderr, argv[0]);
            goto done;
        }
    }

    if (optind >= argc) {
        fprintf(stderr, "Error: Missing command arguments\n");
        usage(stderr, argv[0]);
        goto done;
    }

    /* Find the colon separator */
    for (i = optind; i < argc; i++) {
        if (strcmp(argv[i], ":") == 0) {
            colon_pos = i;
            break;
        }
    }

    if (colon_pos == -1) {
        fprintf(stderr, "Error: Missing ':' separator\n");
        goto done;
    }

    if (colon_pos == optind || colon_pos == argc - 1) {
        fprintf(stderr, "Error: Command missing before or after ':'\n");
        goto done;
    }

    if (pipe(pipe1) < 0 || pipe(pipe2) < 0) {
        perror("pipe");
        goto close_pipes;
    }

    pid1 = fork();
    if (pid1 < 0) {
        perror("fork");
        goto close_pipes;
    }

    if (pid1 == 0) {
        if (close(pipe1[0]) == -1 || close(pipe2[1]) == -1) {
            perror("close");
            exit(EXIT_FAILURE);
        }
        if (dup2(pipe2[0], STDIN_FILENO) == -1 ||
            dup2(pipe1[1], STDOUT_FILENO) == -1) {
            perror("dup2");
            exit(EXIT_FAILURE);
        }
        argv[colon_pos] = NULL;  /* Terminate first command's argv */
        execvp(argv[optind], &argv[optind]);
        perror("execvp cmd1");
        exit(EXIT_FAILURE);
    }

    pid2 = fork();
    if (pid2 < 0) {
        perror("fork");
        goto kill_first;
    }

    if (pid2 == 0) {
        if (close(pipe1[1]) == -1 || close(pipe2[0]) == -1) {
            perror("close");
            exit(EXIT_FAILURE);
        }
        if (dup2(pipe1[0], STDIN_FILENO) == -1 ||
            dup2(pipe2[1], STDOUT_FILENO) == -1) {
            perror("dup2");
            exit(EXIT_FAILURE);
        }
        execvp(argv[colon_pos + 1], &argv[colon_pos + 1]);
        perror("execvp cmd2");
        exit(EXIT_FAILURE);
    }

    if (close(pipe1[0]) == -1 || close(pipe1[1]) == -1 ||
        close(pipe2[0]) == -1 || close(pipe2[1]) == -1) {
        perror("close");
        goto kill_both;
    }

    if (waitpid(pid1, NULL, 0) == -1 || waitpid(pid2, NULL, 0) == -1) {
        perror("waitpid");
        goto done;
    }

    status = EXIT_SUCCESS;
    goto done;

kill_both:
    kill(pid2, SIGTERM);
    waitpid(pid2, NULL, 0);
kill_first:
    kill(pid1, SIGTERM);
    waitpid(pid1, NULL, 0);
close_pipes:
    if (pipe1[0] != -1) close(pipe1[0]);
    if (pipe1[1] != -1) close(pipe1[1]);
    if (pipe2[0] != -1) close(pipe2[0]);
    if (pipe2[1] != -1) close(pipe2[1]);
done:
    return status;
}

// 1. In the cleanup code, the close() return values aren't being checked,
// which could mask errors during cleanup. Though in cleanup code this is often
// acceptable.
// 2. The program doesn't handle SIGPIPE signal, which could occur if one
// process terminates before the other. Though this might be the desired
// behavior.
// 3. In error cases where close() fails in the child processes, the
// error handling exits but doesn't close the other pipe file descriptors
// first. Though these will be closed on process exit anyway.
