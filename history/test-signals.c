// 2>/dev/null; set -e; X=${0%.c} ; [ "$X" -nt "$0" ] || cc -o "$X" -I$HOME/kisskit "$0" && hide "$X"; exec "$X" "$@"

#include <stdio.h>
#include <stdlib.h>

// catch signals HUP, INT and TERM, and write messages to STDERR

#include <signal.h>
#include <unistd.h>

void handler(int sig)
{
	switch (sig) {
	case SIGHUP:
		write(STDERR_FILENO, "caught SIGHUP\n", 14);
		break;
	case SIGINT:
		write(STDERR_FILENO, "caught SIGINT\n", 14);
		break;
	case SIGTERM:
		write(STDERR_FILENO, "caught SIGTERM\n", 15);
		break;
	default:
		write(STDERR_FILENO, "caught unknown signal\n", 22);
		break;
	}
}

int main(int argc, char *argv[])
{
	struct sigaction sa;
	sa.sa_handler = handler;
	sigemptyset(&sa.sa_mask);
	sa.sa_flags = 0;
	sigaction(SIGHUP, &sa, NULL);
	sigaction(SIGINT, &sa, NULL);
	sigaction(SIGTERM, &sa, NULL);
	while (1) {
		sleep(1);
	}
	exit(0);
}
