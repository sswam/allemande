// 2>/dev/null; set -e +a; ccx() { local d="${0%/*}"; [ "$d" != "$0" ] || d='.'; o=$d/.${0##*/}.elf; [ "$o" -nt "$0" ] || cc -o "$o" -std=gnu99 -Wall "$0" "$d/sea.o"; exec "$o" "$@"; }; ccx "$@"

#include <stdio.h>

int main(int argc, char *argv[])
{
    printf("Hello, World!\n");
    return 0;
}
