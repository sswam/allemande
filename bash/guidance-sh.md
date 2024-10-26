# Important Notes to AI

AVOID DEEP INDENTATION OR NESTING, better to use if/elif or a function. This
is the number one rule! If needed, we can use variables to avoid repeating
parts of conditions. Test negative or short cases first, and use continue,
break, return, or exit to avoid deep nesting.

Do not remove comments, logging or blank lines, especially not TODO, FIXME,
XXX. Do not remove ANYTHING unnecessarily. If you are 1000% sure something is
wrong, comment it out rather than removing it.

We use the `-e` `-u` and `-o pipefail` options via ally, so be careful to avoid
accidentally exiting. Don't use [ test ] || action, it's unsafe with -e.
Use if [ test ]; then action; fi

Warnings and other commentary must be printed to stderr:
echo >&2 "Something went wrong".
No unnecessary "success" or info messages,
no "Error: " or "Warning: " prefixes; THIS IS UNIX!

Only use echo for fixed text. Echo "$foo" is unreliable due to its options;
use printf with a format string.

We don't care about compatibility with older versions of bash, or other shells.

Follow the principles from The Practice of Programming by Kernighan and Pike,
e.g. "simplicity, clarity, generality". As Linus advises, "Good taste" in
programming often means preferring clear, simple solutions over clever ones.
