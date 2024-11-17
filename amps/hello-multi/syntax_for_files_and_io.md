A bare pathname refers to the file's contents:
	- This is implemented using mmap, with a struct including mmap parameters.
	- It can be used as a char \*. The data will be NUL terminated.

Pathnames must be distinguished from literals and variable names, how?
	- "foo bar" is a string literal
	- 123 is an integer literal (or long, Decimal, etc.)
	- 12.34 is a floating-point literal
	- Anything starting with /, ./ or ../ is a pathname?
	- Or just use strings as pathnames.

A < sign then pathname, redirects input from that file.
	- Used with external tools.
	- Could maybe also be used to redirect stdin within C or Python code.

A > sign then pathname, redirects output to that file.

A >> sign then pathname, appends output to that file.

A pathname then < sign, uses the file as an argument, for input only.

A pathname then > sign, uses the file as an argument, for output only.

A pathname then >> sign, uses the file as an argument, for appending output only.

A pathname then ! sign, uses the file as an argument, for update (reading and writing).
