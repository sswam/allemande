#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>
#include <check.h>
#include <stdarg.h>

// Include the functions from sea.c
#include "../sea.h"

#define BUFFER_SIZE 1024

START_TEST(test_run)
{
	pid_t child_pid;
	int in = -1, out = -1, err = -1;
	char buffer[BUFFER_SIZE];

	// Test simple command
	ck_assert_int_eq(run(&child_pid, NULL, &out, NULL, "echo", "Hello, World!", NULL), 0);
	ssize_t bytes_read = read_all(out, buffer, BUFFER_SIZE);
	ck_assert_int_gt(bytes_read, 0);
	buffer[bytes_read - 1] = '\0'; // Remove newline
	ck_assert_str_eq(buffer, "Hello, World!");

	// Test command with input
	const char *input = "Test input\n";
	in = -1;
	out = -1;
	ck_assert_int_eq(run(&child_pid, &in, &out, NULL, "cat", NULL), 0);
	write_all(in, input, strlen(input));
	close(in);
	bytes_read = read_all(out, buffer, BUFFER_SIZE);
	ck_assert_int_gt(bytes_read, 0);
	buffer[bytes_read - 1] = '\0'; // Remove newline
	ck_assert_str_eq(buffer, "Test input");

	// Test command with error
	err = -1;
	ck_assert_int_eq(run(&child_pid, NULL, NULL, &err, "ls", "/nonexistent", NULL), 0);
	bytes_read = read_all(err, buffer, BUFFER_SIZE);
	ck_assert_int_gt(bytes_read, 0);
	buffer[bytes_read - 1] = '\0'; // Remove newline
	ck_assert_str_eq(buffer, "ls: cannot access '/nonexistent': No such file or directory");
}
END_TEST

START_TEST(test_read_all_malloc)
{
	int pipefd[2];
	ck_assert_int_eq(pipe(pipefd), 0);

	const char *test_data = "This is a test string for read_all_malloc.";
	write_all(pipefd[1], test_data, strlen(test_data));
	close(pipefd[1]);

	char *result = read_all_malloc(pipefd[0]);
	ck_assert_ptr_nonnull(result);
	ck_assert_str_eq(result, test_data);

	free(result);
}
END_TEST

START_TEST(test_write_all)
{
	int pipefd[2];
	ck_assert_int_eq(pipe(pipefd), 0);

	const char *test_data = "Testing write_all function.";
	ssize_t bytes_written = write_all(pipefd[1], test_data, strlen(test_data));
	if (bytes_written < 0)
		perror("write_all");
	ck_assert_int_eq(bytes_written, strlen(test_data));
	close(pipefd[1]);

	char buffer[BUFFER_SIZE];
	ssize_t bytes_read = read_all(pipefd[0], buffer, BUFFER_SIZE);
	ck_assert_int_eq(bytes_read, strlen(test_data));
	buffer[bytes_read] = '\0';
	ck_assert_str_eq(buffer, test_data);
}
END_TEST

Suite *sea_suite(void)
{
	Suite *s;
	TCase *tc_core;

	s = suite_create("Sea");
	tc_core = tcase_create("Core");

	tcase_add_test(tc_core, test_run);
	tcase_add_test(tc_core, test_read_all_malloc);
	tcase_add_test(tc_core, test_write_all);
	suite_add_tcase(s, tc_core);

	return s;
}

int main(void)
{
	int number_failed;
	Suite *s;
	SRunner *sr;

	s = sea_suite();
	sr = srunner_create(s);

	srunner_run_all(sr, CK_NORMAL);
	number_failed = srunner_ntests_failed(sr);
	srunner_free(sr);

	return (number_failed == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}
