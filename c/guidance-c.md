# Important Notes to AI

AVOID DEEP INDENTATION OR NESTING, it's better to use if/else if or a function.
This is the number one rule! If needed, we can use variables to avoid repeating
parts of conditions. Test negative or short cases first, and use continue,
break, or return to avoid deep nesting.

Follow Linus's kernel code style guide.

Do not remove comments, logging or blank lines, especially not TODO, FIXME,
XXX. Do not remove ANYTHING unnecessarily. If you are 1000% sure something is
wrong, comment it out rather than removing it.

In most cases for error handling, return an error code or use goto for cleanup.
Generally, if things go wrong, return an error code rather than continuing.

We return error codes rather than printing to stderr then exiting. Never handle
something that should be an error as a warning.

Stdout is only for normal output. Use stderr for info, warning or error
messages.

Use modern C standards (C11 or C17) when possible, but don't be gratuitously
incompatible with C89 when it doesn't make much difference.

We prefer to declare all local variables at the top of the function, not in
blocks or for init.

NULL is different from 0. Don't "simplify" `if (foo == NULL) foo = default` to
`foo = foo ? foo : default`.

The original coder was probably not an idiot. Be careful when "fixing"
things. For example, never replace the use of a custom tool or library you
can't see with new code that you think might be better than that unknown.

Use const and static where appropriate.

Follow the principles from The Practice of Programming by Kernighan and Pike,
e.g. "simplicity, clarity, generality". As Linus advises, "Good taste" in
programming often means preferring clear, simple solutions over clever ones.

Care about security and correctness, e.g. escaping html entities, SQL values...
