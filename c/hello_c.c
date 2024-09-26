// 2>/dev/null; set -e; X=${0%.c} ; [ "$X" -nt "$0" ] || cc -o "$X" -I$HOME/kisskit "$0" && hide "$X"; exec "$X" "$@"
// hello.c:

#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
	printf("Hello, world\n");
	exit(0);
}
