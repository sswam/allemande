# Important Notes to AI

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
