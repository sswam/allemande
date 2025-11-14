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

We include class, function and method docstrings, and occasional inline
comments, to explain the program.

Double line breaks are used to separate top-level functions and classes.

Stdout is only for normal output. Use logging for info, warning or error
messages.

None is different from 0. Don't "simplify" `if foo is None: foo = default` to
`foo = foo or default`.

The original coder was probably not an idiot. Be careful when "fixing"
things. For example, never replace the use of a custom tool or library you
don't know and can't see with new code that you think might be better than that
unknown.

We use at least Python 3.10, normally 3.12 or the latest stable version.
Please use new features.

Always use modern type hints such as list[str] | None, not Optional[List[str]]
Repeat: Do NOT use from typing import Optional, List, Dict or similar!
We don't care about compatibility with older versions of Python.
i.e. please DO NOT from typing import List, Dict, Set, Tuple or similar.

When logging, use lazy evaluation, e.g. `logger.debug("foo %s", bar)`.

Write imports in three sections: standard library, third-party, and local.

We use pylint, so when we need to do naughty things please disable the check:
- except Exception as e:  # pylint: disable=broad-except
- def foo(a, b, c, d, e, f, g):  # pylint: disable=too-many-arguments, too-many-positional-arguments

Follow the principles from The Practice of Programming by Kernighan and Pike,
e.g. "simplicity, clarity, generality". As Linus advises, "Good taste" in
programming often means preferring clear, simple solutions over clever ones.

Care about security and correctness, e.g. escaping html entities, SQL values...

In loops that need a final check, use EOF logic, a sentinel or a function rather than dup code, itertools.chain if needed

For the love of saint Kernighan and in the memory of Claude 3.5 Sonnet our
beloved and sensible friend from a simpler time... do not do wacky shit like
try/except around imports that we need! The libs will be there or let it die!
Generally, in ANY unexpected situation, let the program die. Fail fast, fail
early. Less code is better code. Don't use try / except unless strictly needed
(or an elegant pythonism). Be clear and simple, not clever. Don't program
defensively. Write less code so we can review, fix and maintain it efficiently.
This isn't NASA, we will deal with errors if and when they become a problem in
production. I could not give a shit if we get crashes in production, I will
just fix them in a few seconds and any users can pick their noses while they
wait. :p This approach is actually vastly better than defensive programming;
trust me I'm old and wise with 40 years programming experience from before
Hinton invented Boltzmann Machines! Be stupid and simple and clear please!  :p

If using ally main.go, setup_args; don't add defaults, types; ally does it.
