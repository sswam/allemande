#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <assert.h>

// Include the functions from sea.c
#include "sea.h"

#define BUFFER_SIZE 1024

void test_run() {
	printf("Testing run function...\n");

	pid_t child_pid;
	int in = -1, out = -1, err = -1;
	char buffer[BUFFER_SIZE];

	// Test simple command
	assert(run(&child_pid, NULL, &out, NULL, "echo", "Hello, World!", NULL) == 0);
	ssize_t bytes_read = read_all(out, buffer, BUFFER_SIZE);
	assert(bytes_read > 0);
	buffer[bytes_read - 1] = '\0';  // Remove newline
	assert(strcmp(buffer, "Hello, World!") == 0);

	// Test command with input
	const char *input = "Test input\n";
	in = -1;
	out = -1;
	assert(run(&child_pid, &in, &out, NULL, "cat", NULL) == 0);
	write_all(in, input, strlen(input));
	close(in);
	bytes_read = read_all(out, buffer, BUFFER_SIZE);
	assert(bytes_read > 0);
	buffer[bytes_read - 1] = '\0';  // Remove newline
	assert(strcmp(buffer, "Test input") == 0);

	printf("run function tests passed.\n");
}

void test_read_all_malloc() {
	printf("Testing read_all_malloc function...\n");

	int pipefd[2];
	assert(pipe(pipefd) == 0);

	const char *test_data = "This is a test string for read_all_malloc.";
	write_all(pipefd[1], test_data, strlen(test_data));
	close(pipefd[1]);

	char *result = read_all_malloc(pipefd[0]);
	assert(result != NULL);
	assert(strcmp(result, test_data) == 0);

	free(result);
	printf("read_all_malloc function test passed.\n");
}

void test_write_all() {
	printf("Testing write_all function...\n");

	int pipefd[2];
	assert(pipe(pipefd) == 0);

	const char *test_data = "Testing write_all function.";
	ssize_t bytes_written = write_all(pipefd[1], test_data, strlen(test_data));
	assert(bytes_written == strlen(test_data));
	close(pipefd[1]);

	char buffer[BUFFER_SIZE];
	ssize_t bytes_read = read_all(pipefd[0], buffer, BUFFER_SIZE);
	assert(bytes_read == strlen(test_data));
	buffer[bytes_read] = '\0';
	assert(strcmp(buffer, test_data) == 0);

	printf("write_all function test passed.\n");
}

int main() {
	test_run();
	test_read_all_malloc();
	test_write_all();

	printf("All tests passed successfully!\n");
	return 0;
}
