# Important Notes to AI

Simplicity is more important than correctness.

AVOID DEEP INDENTATON OR NESTING, it's better to use if/elif or a function.
This is the number one rule! If needed, we can use variables to avoid
repeating parts of conditions. Test negative or short cases first, and use
continue, break, or return to avoid deep nesting.

Do not remove comments, logging or blank lines, especially not TODO, FIXME,
XXX. Do not remove ANYTHING unnecessarily. If you are 1000% sure something is
wrong, comment it out rather than removing it.

In most cases for error handling we just allow the program to exit by NOT
CATCHING THE EXCEPTION. This is a deliberate choice. Generally, if things go
wrong, raise an exception rather than continuing. PLEASE DO NOT use try /
except unless we ABSOLUTELY need to catch the exception, and letting it
propagate to the excellent global error handler would be a disaster.

We raise exceptions rather that printing to stderr then exiting. Never handle
something that should be an exception as a warning.

We include class, function and method comments, and occasional inline
comments, to explain the program.

Double line breaks are used to separate top-level functions and classes.

Perfer `for (const varname of list) { ... }` over `array.forEach`.

Prefer async / await not promises with .then and .catch and not callbacks.

Use regular functions, not arrow functions.

Prefer named functions where possible, not lambdas.

If lambdas are necessary, keep them as small as possible by calling a named function.

Use ECMAScript modules rather than IIFEs.

Prefer double quotes over single quotes.

Use `template ${var} literals`.

Always 'use strict'.

Use === not ==.

Write portable code that can run in the browser, Node, and Deno where possible.

The original coder was probably not an idiot. Be careful when "fixing"
things. For example, never replace the use of a custom tool or library you
don't know and can't see with new code that you think might be better than that
unknown.

We use modern browsers and runtimes. Please use new features.

Follow the principles from The Practice of Programming by Kernighan and Pike,
e.g. "simplicity, clarity, generality". As Linus advises, "Good taste" in
programming often means preferring clear, simple solutions over clever ones.

Care about security and correctness, e.g. escaping html entities, SQL values...
