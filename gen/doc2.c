/*
 * doc2.c - A program that executes 'cat-named' command and pipes its output to 'process' command
 *
 * This program demonstrates the use of pipes and process creation in C.
 * It executes the 'cat-named' command with provided arguments and pipes its
 * output to the 'process' command.
 *
 * Usage: ./doc2 [file1] [file2] ...
 *
 * The program will concatenate the contents of the provided files using 'cat-named'
 * and then pass the output to the 'process' command.
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <string.h>

#define MAX_COMMAND_LENGTH 1024
#define MAX_ARGS 64

/*
 * execute_command - Execute a command with given arguments
 *
 * @param command: The command to execute
 * @param args: Array of arguments for the command
 *
 * This function forks a child process to execute the given command
 * and waits for it to complete.
 */

void execute_command(const char *command, char *const args[]) {
    pid_t pid = fork();

    if (pid == -1) {
        perror("fork");
        exit(EXIT_FAILURE);
    } else if (pid == 0) {
        // Child process
        execvp(command, args);
        perror("execvp");
        exit(EXIT_FAILURE);
    } else {
        // Parent process
        int status;
        waitpid(pid, &status, 0);
        if (WIFEXITED(status) && WEXITSTATUS(status) != 0) {
            fprintf(stderr, "Command failed: %s\n", command);
            exit(EXIT_FAILURE);
        }
    }
}

/*
 * The main function performs the following steps:
 * 1. Prepares arguments for the 'cat-named' command
 * 2. Sets up a pipe for communication between processes
 * 3. Forks a child process to execute 'cat-named'
 * 4. In the parent process, executes 'process' command with piped input
 *
 * Error handling is implemented throughout the program to catch and report
 * any issues with system calls or command execution.
 */

int main(int argc, char *argv[]) {
    char cat_command[MAX_COMMAND_LENGTH] = "cat-named";
    char *cat_args[MAX_ARGS] = {cat_command};
    int cat_arg_count = 1;

    // Copy arguments to cat_args
    for (int i = 1; i < argc && i < MAX_ARGS - 1; i++) {
        cat_args[cat_arg_count++] = argv[i];
    }
    cat_args[cat_arg_count] = NULL;

    // Set up pipe
    int pipefd[2];
    if (pipe(pipefd) == -1) {
        perror("pipe");
        exit(EXIT_FAILURE);
    }

    pid_t pid = fork();
    if (pid == -1) {
        perror("fork");
        exit(EXIT_FAILURE);
    } else if (pid == 0) {
        // Child process (cat-named)
        close(pipefd[0]);
        dup2(pipefd[1], STDOUT_FILENO);
        close(pipefd[1]);

        execute_command(cat_command, cat_args);
        exit(EXIT_SUCCESS);
    } else {
        // Parent process
        close(pipefd[1]);
        dup2(pipefd[0], STDIN_FILENO);
        close(pipefd[0]);

        char *process_args[] = {"process", "Please write some basic documentation for this code.", NULL};
        execute_command("process", process_args);
    }

    return 0;
}
