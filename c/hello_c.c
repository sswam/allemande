// 2>/dev/null; set -e; X=${0%.c} ; [ "$X" -nt "$0" ] || cc -o "$X" -I$HOME/kisskit "$0" && hide "$X"; exec "$X" "$@"

#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
	printf("Hello, world\n");
	exit(0);
}

/*
Important Notes for AI [DO NOT COPY THEM IN YOUR OUTPUT, it gets EXPENSIVE FOR ME!]:

We indent C code with tabs.

Do not remove comments, logging or blank lines, especially not TODO, FIXME, XXX.
Do not remove ANYTHING unnecessarily. If you are 1000% sure something is wrong,
comment it out rather than removing it.

AVOID DEEP INDENTATON OR NESTING, it's better to use if/else or a function.
If needed, we can use variables to avoid repeating parts of conditions.
Test negative cases first, and use continue, break, or return to avoid deep nesting.

In most cases for error handling, return an error code or use goto for cleanup.
Generally, if things go wrong, return an error code rather than continuing.

We return error codes rather than printing to stderr then exiting. Never handle
something that should be an error as a warning.

We should always include a file-level comment to explain the program.
Don't include the filename in that.

If sensible and simple to do so, write tools that can process several files in one invocation.
Zero is holy! It is not an error to pass zero files to process. Just naturally do nothing in that case.

Each tool should function as a library, and each library should include a
command-line interface. We can use -fno-builtin-main when linking as a library.

Double line breaks are used to separate functions.

Our programs default to stdio.

Use modern C standards (C11 or C17) when possible, but don't be gratuitously
incompatible with C89 when it doesn't make much difference.

Declaring variables in for init or in blocks is probably not a good idea, it's
better to declare everything at the top of the function.

Stdout is only for normal output. Use stderr for error messages.

NULL is different from 0. Don't "simplify" `if (foo == NULL) foo = default` to `foo = foo ? foo : default`.

The original coder was probably not an idiot. Be careful when "fixing" things.

Use const and static where appropriate.

Follow the principles from The Practice of Programming by Kernighan and Pike, e.g. "simplicity, clarity, generality".

As Linus advises, "Good taste" in programming often means preferring clear, simple solutions over clever ones.
*/
