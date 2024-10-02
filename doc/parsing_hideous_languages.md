is there a full and correct parser for bash or perl? other than bash and perl themselves. What language are these parsers written in? Can we dump the AST from within Perl itseld?

1. Bash:
   - ShellCheck (Haskell)
   - Bash-Parser (JavaScript)

2. Perl:
   - PPI (Perl)
   - Perl::Parser (C)

3. Perl AST dump:
   - Use B::Deparse module
   - Example: perl -MO=Deparse script.pl

No full, completely correct parser exists outside the official interpreters due to language complexities and evolving syntax.

I don't suppose bash can dump the AST for itself? I guess it can run something and dump out the functions at least.

Bash doesn't have a built-in AST dumping feature. However, you can use:

1. `declare -f` to list all defined functions
2. `set -x` for tracing execution
3. External tools like ShellCheck for static analysis
4. bashdb for debugging

These provide insights into script structure and execution, but not a full AST.

I guess we could hack bash to build an AST instead of running things.

Bash doesn't have built-in functionality to dump its own AST. It can display defined functions using `declare -f`. Modifying Bash's source code to build and output an AST instead of executing commands is possible but would require significant effort.

