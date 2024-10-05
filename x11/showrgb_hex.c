// 2>/dev/null; set -e; X=${0%.c} ; [ "$X" -nt "$0" ] || cc -o "$X" -I$HOME/kisskit "$0" && hide "$X"; exec "$X" "$@"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_LINE_LENGTH 256

// This program reads RGB color values from stdin and outputs the corresponding
// hexadecimal color code along with the color name.

int main(int argc, char *argv[])
{
	char line[MAX_LINE_LENGTH];
	int r, g, b;
	char name[MAX_LINE_LENGTH];

	while (fgets(line, sizeof(line), stdin) != NULL) {
		if (sscanf(line, "%d %d %d\t%[^\n]", &r, &g, &b, name) == 4) {
			printf("%02x%02x%02x\t%s\n", r, g, b, name);
		}
	}

	return 0;
}
