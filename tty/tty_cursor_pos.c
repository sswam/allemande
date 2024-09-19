/*
 * This program demonstrates how to get the current cursor position in a terminal.
 * It uses ANSI escape codes to query the terminal and parse the response.
 * The technique involves:
 * 1. Disabling canonical mode and echo to read raw input
 * 2. Sending the Device Status Report (DSR) escape sequence
 * 3. Reading the response, which is in the format "\033[row;colR"
 * 4. Parsing the response to extract row and column numbers
 * 5. Restoring the original terminal settings
 */

#include <stdio.h>
#include <termios.h>
#include <unistd.h>
#include <sys/select.h>

#define TIMEOUT_MS 100

int read_with_timeout(int fd, void *buf, size_t count, int timeout_ms)
{
	fd_set fds;
	struct timeval tv;

	FD_ZERO(&fds);
	FD_SET(fd, &fds);

	tv.tv_sec = timeout_ms / 1000;
	tv.tv_usec = (timeout_ms % 1000) * 1000;

	int ret = select(fd + 1, &fds, NULL, NULL, &tv);
	if (ret > 0) {
		return read(fd, buf, count);
	}
	return ret; // 0 on timeout, -1 on error
}

int get_pos(int *y, int *x)
{
	char buf[30] = {0};
	int ret, i, pow;
	char ch;

	*y = 0;
	*x = 0;

	struct termios term, restore;

	// Save current terminal settings and set up raw mode
	if (tcgetattr(0, &term) == -1 || tcgetattr(0, &restore) == -1) {
		perror("tcgetattr");
		return 1;
	}
	term.c_lflag &= ~(ICANON | ECHO);
	if (tcsetattr(0, TCSANOW, &term) == -1) {
		perror("tcsetattr");
		return 1;
	}

	// Send the cursor position request
	if (write(1, "\033[6n", 4) != 4) {
		perror("write");
		tcsetattr(0, TCSANOW, &restore);
		return 1;
	}

	// Read the response into buf
	for (i = 0, ch = 0; ch != 'R' && i < sizeof(buf) - 1; i++) {
		ret = read_with_timeout(0, &ch, 1, TIMEOUT_MS);
		if (ret != 1) {
			if (ret == -1) perror("read");
			tcsetattr(0, TCSANOW, &restore);
			return 1;
		}
		buf[i] = ch;
	}

	// Restore original terminal settings
	if (tcsetattr(0, TCSANOW, &restore) == -1) {
		perror("tcsetattr");
		return 1;
	}

	if (i < 2) {
		fprintf(stderr, "Invalid response\n");
		return 1;
	}

	// Parse the response using sscanf
	if (sscanf(buf, "\033[%d;%dR", y, x) != 2) {
		fprintf(stderr, "Failed to parse response\n");
		return 1;
	}

	return 0;
}

int main(void)
{
	int x = 0, y = 0;
	if (get_pos(&y, &x) == 0) {
		printf("row=%d col=%d\n", y, x);
	} else {
		fprintf(stderr, "Failed to get cursor position\n");
	}
	return 0;
}

// Glossary:
/*
termios: Structure for terminal I/O settings
tcgetattr: Gets the current terminal attributes
tcsetattr: Sets the terminal attributes
ICANON: Canonical input mode (line-by-line)
ECHO: Echo input characters
TCSANOW: Change attributes immediately
*/
