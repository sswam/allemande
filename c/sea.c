#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/wait.h>
#include <string.h>
#include <stdarg.h>

#define MAX_ARGS 64
#define BLOCK 4096

/* Execute a command with a va_list of arguments, with flexible piping options */
int runv(const char *command, va_list args, pid_t *childpid, /*@null@*/ int /*@null@*/ *in, /*@null@*/ int /*@null@*/ *out, /*@null@*/ int /*@null@*/ *err)
{
	int status = -1;
	int pipefd_in[2] = {-1, -1};
	int pipefd_out[2] = {-1, -1};
	int pipefd_err[2] = {-1, -1};
	/*@null@*/ char *argv[MAX_ARGS];
	int argc = 0;
	char *arg = NULL;

	*childpid = 0;

	// Prepare the argument array
	argv[argc++] = (char *)command;
	while ((arg = va_arg(args, char *)) != NULL && argc < MAX_ARGS - 1)
		argv[argc++] = arg;
	argv[argc] = NULL;

	// Create pipes if needed
	if (in == NULL)
		pipefd_in[0] = STDIN_FILENO;
	else if (*in != -1)
		pipefd_in[0] = *in;
	else if (pipe(pipefd_in) == -1)
		goto done;
	else {
		*in = pipefd_in[1];
		if (fcntl(pipefd_in[1], F_SETFD, FD_CLOEXEC) == -1)
			goto close_in;
	}

	if (out == NULL)
		pipefd_out[1] = STDOUT_FILENO;
	else if (*out != -1)
		pipefd_out[1] = *out;
	else if (pipe(pipefd_out) == -1)
		goto close_in;
	else {
		*out = pipefd_out[0];
		if (fcntl(pipefd_out[0], F_SETFD, FD_CLOEXEC) == -1)
			goto close_out;
	}

	if (err == NULL)
		pipefd_err[1] = STDERR_FILENO;
	else if (err == out)
		pipefd_err[1] = pipefd_out[1];
	else if (*err != -1)
		pipefd_err[1] = *err;
	else if (pipe(pipefd_err) == -1)
		goto close_out;
	else {
		*err = pipefd_err[0];
		if (fcntl(pipefd_err[0], F_SETFD, FD_CLOEXEC) == -1)
			goto close_pipes;
	}

	if ((*childpid = fork()) == -1)
		goto close_pipes;
	if (*childpid != 0)
		goto parent;
	goto child;

child:
	if (in != NULL && pipefd_in[0] != -1) {
		(void)close(pipefd_in[1]);
		if (pipefd_in[0] != STDIN_FILENO && dup2(pipefd_in[0], STDIN_FILENO) == -1)
			goto dup2_failed;
	}
	if (out != NULL && pipefd_out[1] != -1) {
		(void)close(pipefd_out[0]);
		if (pipefd_out[1] != STDOUT_FILENO && dup2(pipefd_out[1], STDOUT_FILENO) == -1)
			goto dup2_failed;
	}
	if (err != NULL && err != out && pipefd_err[1] != -1) {
		(void)close(pipefd_err[0]);
		if (pipefd_err[1] != STDERR_FILENO && dup2(pipefd_err[1], STDERR_FILENO) == -1)
			goto dup2_failed;
	}

	(void)execvp(command, argv);
	perror("execvp failed");
	fprintf(stderr, "\tcommand not found?  %s\n", command);
	_exit(127); // exec failed

dup2_failed:
	perror("dup2 failed");
	_exit(126); // dup2 failed

parent:
	if (in != NULL && pipefd_in[0] != -1) {
		(void)close(pipefd_in[0]);
	}
	if (out != NULL && pipefd_out[1] != -1) {
		(void)close(pipefd_out[1]);
	}
	if (err != NULL && err != out && pipefd_err[1] != -1) {
		(void)close(pipefd_err[1]);
	}
	status = 0;
	goto done;

close_pipes:
	if (err != NULL && err != out && pipefd_err[0] != -1) {
		(void)close(pipefd_err[0]);
		(void)close(pipefd_err[1]);
	}
close_out:
	if (out != NULL && pipefd_out[0] != -1) {
		(void)close(pipefd_out[0]);
		(void)close(pipefd_out[1]);
	}
close_in:
	if (in != NULL && pipefd_in[0] != -1) {
		(void)close(pipefd_in[0]);
		(void)close(pipefd_in[1]);
	}
done:
	return status;
}

/* Execute a command with a variable number of arguments, with flexible piping options */
int run(pid_t *childpid, /*@null@*/ int *in, /*@null@*/ int *out, /*@null@*/ int *err, const char *command, ...)
{
	va_list args;
	int status = -1;

	va_start(args, command);
	status = runv(command, args, childpid, in, out, err);
	va_end(args);

	return status;
}

/* Read all data from a file descriptor into a buffer */
ssize_t read_all(int fd, char *buffer, ssize_t buffer_size)
{
	ssize_t n;
	ssize_t total = 0;

	while ((n = read(fd, buffer + total, (size_t)(buffer_size - total))) > 0) {
		total += n;
		if (total == buffer_size) {
			n = -1;
			break;
		}
	}
	(void)close(fd);
	return n < 0 ? n : total;
}

/* Read all data from a file descriptor into a malloc'd buffer */
/*@null@*/ char *read_all_malloc(int fd)
{
	char *buffer = NULL;
	char *buffer_new = NULL;
	size_t buffer_size = 0;
	ssize_t n;

	for (;;) {
		if ((buffer_new = realloc(buffer, buffer_size + BLOCK)) == NULL)
			goto free_buffer;
		buffer = buffer_new;
		if ((n = read(fd, buffer + buffer_size, BLOCK)) < 0)
			goto free_buffer;
		if (n == 0 && (buffer_new = realloc(buffer, buffer_size + 1)) == NULL)
			goto free_buffer;
		if (n == 0) {
			buffer = buffer_new;
			buffer[buffer_size] = '\0';
			(void)close(fd);
			goto done;
		}
		buffer_size += n;
	}

free_buffer:
	fprintf(stderr, "read_all_malloc: failed to read all data\n");
	free(buffer);
	buffer = NULL;
done:
	return buffer;
}

/* Write all data from a buffer to a file descriptor */
ssize_t write_all(int fd, const char *buffer, ssize_t buffer_size)
{
	ssize_t n;
	ssize_t total = 0;

	while (total < buffer_size && (n = write(fd, buffer + total, (size_t)(buffer_size - total))) > 0) {
		total += n;
	}
	return n < 0 ? n : total;
}

/* Run a command and capture its output */
char *run_capture(const char *command, ...)
{
	va_list args;
	char *result = NULL;
	int status = -1;
	int fd_from = -1;
	pid_t childpid = 0;

	va_start(args, command);
	status = runv(command, args, &childpid, NULL, &fd_from, NULL);
	va_end(args);

	if (status == -1)
		goto fail;

	if ((result = read_all_malloc(fd_from)) == NULL)
		goto waitpid;

waitpid:
	if ((waitpid((__pid_t)childpid, &status, 0)) == -1 || status != 0) {
		perror("Command failed");
		free(result);
		result = NULL;
	}
fail:
	return result;
}

/* Run a command with input, and capture its output */
char *run_capture_with_input(const char *input, const char *command, ...)
{
	va_list args;
	char *result = NULL;
	int status = -1;
	int fd_to = -1;
	int fd_from = -1;
	pid_t childpid = 0;
	pid_t feeder_pid = 0;

	va_start(args, command);
	status = runv(command, args, &childpid, &fd_to, &fd_from, NULL);
	va_end(args);

	if (status == -1)
		goto done;

	/* we need to use threads or fork, or temp files, to avoid deadlocks */
	
	if ((feeder_pid = fork()) == -1) {
		perror("Failed to fork feeder process");
		goto close_fds;
	}
	if (feeder_pid == 0) {
		(void)close(fd_from);
		if (write_all(fd_to, input, strlen(input)) == -1)
			_exit(1);
		_exit(0);
	}
	(void)close(fd_to);

	if ((result = read_all_malloc(fd_from)) == NULL)
		goto wait_feeder;

wait_feeder:
	if (waitpid((__pid_t)feeder_pid, &status, 0) == -1 || status != 0) {
		perror("Feeder process failed");
		free(result);
		result = NULL;
	}
close_fds:
	(void)close(fd_to);
	(void)close(fd_from);
	if (waitpid((__pid_t)childpid, NULL, 0) == -1 || status != 0) {
		perror("Command failed");
		free(result);
		result = NULL;
	}
done:
	return result;
}

/* LLM query */
char *llm_query(const char *query)
{
	return run_capture("llm", "query", query, NULL);
}

/* LLM process */
char *llm_process(const char *query, const char *input)
{
	return run_capture_with_input(input, "llm", "process", query, NULL);
}
