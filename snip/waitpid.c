	waitpid((__pid_t)childpid, &status, 0);
	if (status == -1) {
		perror("waitpid failed");
		free(result);
		result = NULL;
	}
	if (status != 0) {
		perror("Command failed");
		if (WIFEXITED(status))
			fprintf(stderr, "\tstatus: %d\n", WEXITSTATUS(status));
		else if (WIFSIGNALED(status))
			fprintf(stderr, "\tsignal: %d\n", WTERMSIG(status));
		else
			fprintf(stderr, "\tunknown status %d\n", status);
		free(result);
		result = NULL;
	}
