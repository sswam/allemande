/* sshc, ssh command
written by Sam Watkins, 2007 - 2025
this program is public domain
*/

#include <limits.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <getopt.h>

#ifdef __MINGW32_MAJOR_VERSION
#define WIFEXITED(x) 1
#define WEXITSTATUS(x) x
#else
#include <sys/wait.h>
#endif

/* sshc - ssh command */

/* special exit codes: 123 - system call failed. 124 - remote cd failed */

static void arcs_error(char *error)
{
	fprintf(stderr, "Error: %s\n", error);
	exit(EXIT_FAILURE);
}

#ifndef __MINGW32_MAJOR_VERSION
/* Quoting arguments for the shell */
/* The "to" buffer must have enough space, allow 2 * strlen(from)+1. */
/* It adds a null and returns the address of the null. */
static char *sh_quote(const char *from, char *to)
{
	char c;
	while (1) {
		c = *from;
		if (c == '\0')
			break;
		if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || strchr("-_./", c) != NULL) {
			// doesn't need escaping
			*to = c;
			++to;
		} else {
			to[0] = '\\';
			to[1] = c;
			to += 2;
		}
		++from;
	}
	*to = '\0';
	return to;
}
#else
static char *sh_quote(const char *from, char *to)
{
	int quote = strchr(from, ' ') ? 1 : 0;
	if (quote)
		*to++ = '"';
	strcpy(to, from);
	to += strlen(from);
	if (quote)
		*to++ = '"';
	return to;
}
#endif

static char *sh_quote_malloc(const char *from)
{
	char *to = malloc(strlen(from) * 2 + 3);
	if (!to)
		arcs_error("memory allocation failed");
	sh_quote(from, to);
	return to;
}

char *current_dir_home_relative(void)
{
	char *dir = NULL;
	char buf[PATH_MAX];
	char *home = getenv("HOME");
	int l;
	if (!getcwd(buf, sizeof(buf)))
		arcs_error("directory path too long");
	if (home && (l = strlen(home)) && strncmp(home, buf, l) == 0) {
		if (buf[l] == '\0')
			dir = ".";
		else if (buf[l] == '/')
			dir = buf + l + 1;
	}
	if (!dir)
		dir = buf;
	return strdup(dir);
}

static void usage(void)
{
	fprintf(stderr, "usage: sshc [-p port] [--] user@host:dir command arg1...\n");
	exit(EXIT_FAILURE);
}

/* -------------------------------------------------------- */

int main(int argc, char **argv)
{
	char *user_host_dir;
	char *user_host;
	char *dir;
	char *delim;
	char command[4096];
	char ssh_command[8192];
	char *out;
	int count;
	char *ssh_prog;
	int tty;
	char *sshc_shell_init = "";
	char *port = NULL;
	int c;

	tty = isatty(fileno(stdout));

	ssh_prog = getenv("ARCS_SSH");
	if (!ssh_prog) {
		ssh_prog = getenv("SSH");
	}
	if (ssh_prog == NULL && tty) {
		ssh_prog = "ssh -q -t";
#ifdef __MINGW32_MAJOR_VERSION
		sshc_shell_init = "\". /etc/profile ; . ~/.bash_profile ; \"";
#else
		sshc_shell_init = "\"if [ -n \\\"\\$BASH\\\" ]; then . /etc/profile ; . ~/.bash_profile ; fi ; \"";
#endif
	} else if (ssh_prog == NULL) {
		ssh_prog = "ssh -q";
	}

	while ((c = getopt(argc, argv, "p:")) != -1) {
		switch (c) {
		case 'p':
			port = optarg;
			break;
		default:
			usage();
		}
	}

	if (optind >= argc) {
		usage();
	}

	user_host_dir = argv[optind++];

	user_host = user_host_dir;
	delim = strchr(user_host_dir, ':');
	if (delim && delim[1] != '\0') {
		*delim = '\0';
		dir = delim + 1;
	} else if ((delim = strchr(user_host_dir, '=')) && delim[1] == '\0') {
		*delim = '\0';
		dir = current_dir_home_relative();
	} else {
		dir = ".";
	}

	if (optind >= argc) {
		usage();
	}

	out = command;
	*out = '\0';

	while (optind < argc) {
		if (out - command + strlen(argv[optind]) * 2 + 4 > sizeof(command)) {
			arcs_error("arguments too long");
		}
		out = sh_quote(argv[optind], out);
		*out = ' ';
		++out;
		++optind;
	}
	if (out > command)
		--out;

	*out = '\0';

	char *dir_q = sh_quote_malloc(dir);
	char *dir_qq = sh_quote_malloc(dir_q);
	char *command_q = sh_quote_malloc(command);

	// TODO could do this with a temp file shell script

	char *shared_s = getenv("SSHC_SHARED");
	int shared = shared_s && *shared_s == '1';
	char *umask = shared ? "0002" : "0022";

	char port_option[16] = "";
	if (port) {
		snprintf(port_option, sizeof(port_option), "-p %s ", port);
	}

#ifdef __MINGW32_MAJOR_VERSION
	count = snprintf(ssh_command, sizeof(ssh_command),
		"%s %s-- %s %s\"umask %s ; mkdir -p %s ; cd %s || exit 124 ; %s\"",
		ssh_prog, port_option, user_host, sshc_shell_init, umask, dir, dir, command);
#else
	count = snprintf(ssh_command, sizeof(ssh_command),
		"%s %s-- %s %sumask\\ %s\\ \\;\\ mkdir -p\\ %s\\ \\;\\ \\cd\\ %s\\ \\|\\| "
		"exit 124 \\;\\ %s",
		ssh_prog, port_option, user_host, sshc_shell_init, umask, dir_qq, dir_qq, command_q);
#endif
	if (count >= (int)sizeof(ssh_command)) {
		arcs_error("arguments too long");
	}

	//	fprintf(stderr, "%s\n", ssh_command);

	int status = system(ssh_command);
	if (status == -1) {
		status = 123;
	} else if (WIFEXITED(status)) {
		status = WEXITSTATUS(status);
	}

	free(dir_q);
	free(dir_qq);
	free(command_q);

	exit(status);
}
