# A program that converts Cz code (looks like Python) to C/C++, adding braces and semicolons.
# Lines are processed one at a time, handling various syntax elements and converting them

export cstr types vec
use vio


# Main function that processes input lines and writes C/C++ output
brace(vec *lines):
	ssize_t lineno = 0
	brace_init()
	if readstmt(lines, lineno++):
		writestmt()
		while readstmt(lines, lineno++):
			writedelim()
			writestmt()
		writedelim()


def MAXTABS 256

# Block types for tracking nested structures
enum { SWITCH, WHICH, STRUCT, CLASS, INIT, VOID_MAIN, MACRO, DO, DOWHILE, ELSE, OTHER }

# Global state variables for processing
local int blocktype[MAXTABS]

# Keywords that require parentheses
local char *kwdparens[] = { "if", "else if", "while", "do", "for", "switch", "else", 0 }

# Current line processing state
local char *l                 # Current line being processed
local int len                 # Length of current line
local int tabs                # Number of tabs at start of line
local int lasttabs            # Number of tabs from previous line
local int skipsemi            # Flag to skip adding semicolon
local char *label             # Label at start of line
local char *lastlabel         # Previous label
local int lastblank           # Flag for previous line being blank
local char *caselabel         # Case label in switch statements
local char *lastcase          # Previous case label
local int casetabs            # Number of tabs before case label
local int in_macro            # Flag for macro processing
local int first_line_of_macro # Flag for first line of macro

local int is_kwdparens        # Flag for keywords requiring parentheses
local int is_static           # Flag for static declarations


# Initialize global state
local brace_init():
	lastlabel = 0
	lastcase = 0
	in_macro = 0
	first_line_of_macro = 0


# Read and process a single statement from input
local int readstmt(vec *lines, ssize_t lineno):
	if !readln(lines, lineno):
		tabs = 0
		return 0
	tabs = striptabs()
	strip_one_space_maybe()
	fussy()

	# Process labels at start of line
	label = 0
	if len > 0 && tabs == 0:
		int lbllen = wordlen()
		if l[lbllen] == '\t':
			label = l
			l += lbllen
			len -= lbllen
			tabs = striptabs()
			label[lbllen] = '\0'

	# Process case labels
	caselabel = 0
	casetabs = 0
	if len > 0 && tabs > 0 && l[0] != '#':
		int lbllen = caselen()
		if l[lbllen] == ',' && l[lbllen+1] == '\t':
			l[lbllen] = '\0'
			lbllen++
		if l[lbllen] == '\t':
			caselabel = l
			l += lbllen
			len -= lbllen
			casetabs = striptabs()
			caselabel[lbllen] = '\0'
			tabs += casetabs

	# Handle special cases
	if len == 1 && l[0] == '.':
		l[0] = '\0' ; len = 0

	if tabs >= MAXTABS:
		error("too many tabs")

	return 1


# Writes the current statement with appropriate formatting and handling of special cases
local writestmt():
	# Reset flags for current statement processing
	is_kwdparens = 0
	is_static = 0

	# Add break statement for which/switch cases
	if caselabel && lasttabs >= tabs && !(lastblank && lastcase) \
			&& blocktype[tabs-1] == WHICH:
		indent(tabs)
		print("break;\n")

	# Handle labels, adding underscore prefix for numeric labels
	if label:
		if isdigit((int)label[0]):
			print("_")
		print(label)
		print(":")

	# Apply proper indentation
	indent(tabs - casetabs)

	# Process case labels, converting "else" to "default"
	if caselabel:
		if caselabel[0] == '\0':
			error("spurious space between tabs")
		eif strcmp(caselabel, "else") == 0:
			print("default:")
		else:
			print("case ")
			print(caselabel)
			print(":")
		indent(casetabs)

	# Determine block type for current statement
	if strcmp(l, "do") == 0:
		blocktype[tabs] = DO
	eif blocktype[tabs] == DO && cstr_begins_with(l, "while "):
		blocktype[tabs] = DOWHILE
	eif cstr_begins_with(l, "switch "):
		blocktype[tabs] = SWITCH
	eif cstr_begins_with(l, "else") && (len == 4 || l[4] == ' '):
		blocktype[tabs] = ELSE
	eif cstr_begins_with(l, "which "):
		blocktype[tabs] = WHICH
	eif (cstr_begins_with(l, "enum") && (len == 4 || l[4] == ' ')) || \
			l[len-1] == '=' || \
			(tabs > 0 && blocktype[tabs-1] == INIT):
		blocktype[tabs] = INIT
	eif tabs > lasttabs && blocktype[lasttabs] == INIT:
		int i
		for i=lasttabs+1; i<=tabs; ++i:
			blocktype[i] = INIT
	else:
		# Handle special declarations: template, extern "C", struct, union, class
		char *c = l
		if cstr_begins_with(c, "template<"):
			c = strchr(c+9, '>')
			if c == NULL:
				error("template is missing >")
			++c
			if *c == '\0':
				error("template<...> must be followed by the start of a declaration on the same line")
			if *c != ' ':
				error("template<...> must be followed by a space")
			++c
		eif cstr_begins_with(c, "extern \"C\" "):
			c += 11
			if *c == '\0':
				error("extern \"C\" must be followed by the start of a declaration on the same line")

		# Set block type based on declaration type
		if cstr_begins_with(c, "struct ") && classy(c+7):
			blocktype[tabs] = STRUCT
		eif cstr_begins_with(c, "union ") && classy(c+6):
			blocktype[tabs] = STRUCT
		eif cstr_begins_with(c, "class ") && classy(c+6):
			blocktype[tabs] = CLASS
		eif *c == '^' || *c == '#':
			# Ignore directives and comments
		else:
			blocktype[tabs] = OTHER

	# Process the statement content and handle special syntax
	skipsemi = 0
	if len > 0 && l[wordlen()] == '\0' && tabs > 0 && \
			blocktype[tabs] != INIT && \
				strcmp(l, "else") != 0 && \
				strcmp(l, "return") != 0 && \
				strcmp(l, "break") != 0 && \
				strcmp(l, "continue") != 0 && \
				strcmp(l, "do") != 0 && \
				strcmp(l, "repeat") != 0:
		print("goto ")
		if isdigit((int)l[0]):
			print("_")
	eif l[0] == '#':
		print("/")
		l[0] = '/'
	eif cstr_begins_with(l, "export ") || cstr_begins_with(l, "use "):
		l = strchr(l, ' ') + 1
		print("#include ")
		print(l)
		l = "" ; len = 0
	eif cstr_begins_with(l, "def "):
		if tabs != 0:
			error("macro definitions must be at top level")
		blocktype[tabs] = MACRO
		in_macro = 1
		first_line_of_macro = 1
		print("#define ")
		l += 4 ; len -= 4
	eif cstr_begins_with(l, "local ") || cstr_begins_with(l, "static "):
		char *l2 = strchr(l, ' ')+1
		print("static ")
		is_static = 1
		len -= (l2-l) ; l = l2
		if tabs == 0:
			addvoids()
	eif cstr_begins_with(l, "^"):
		print("#")
		skipsemi = 1
		l++ ; len--
	eif l[len-1] == '{' || strcmp(l, "}") == 0:
		skipsemi = 1
	eif tabs == 0:
		addvoids()
	else:
		procstmt()

	print(l)

	# Determine if semicolon should be skipped
	skipsemi = skipsemi || len == 0 || l[0] == '"' || l[0] == '<' || \
		l[0] == '/' || last() == '/'

	if caselabel && len == 0:
		skipsemi = 0

	# Update state for next line
	lastblank = len == 0
	lastlabel = 0
	lastcase = 0
	if label || !lastblank:
		lastlabel = label
	if caselabel && !lastblank:
		lastcase = caselabel
	lasttabs = tabs

# Writes appropriate delimiters (semicolons, braces) at the end of statements
local writedelim():
	int lt = lasttabs
	if first_line_of_macro:
		skipsemi = 1
		if tabs != 0:
			lt = tabs
	if lt >= tabs && \
			(!skipsemi || \
				(lastblank && (lastlabel || lastcase))) && \
			!(lt > 0 && blocktype[lt-1] == INIT):
		if is_kwdparens && blocktype[lt] != DOWHILE:
			print(" {}")
		else:
			print(";")
	if in_macro && tabs > 0:
		print(" \\")
	print("\n")
	if !(in_macro && tabs == 0):
		while lt > tabs:
			indent(--lt)
			if blocktype[lt] == STRUCT || blocktype[lt] == CLASS:
				print("};\n")
			eif blocktype[lt] == INIT && !(lt>0 && blocktype[lt-1] == INIT):
				print("};\n")
			else:
				if lt == 0 && blocktype[0] == VOID_MAIN:
					print("\treturn 0;\n")
				print("}\n")
		while lt < tabs:
			indent(lt++)
			print("{\n")
	if in_macro && tabs == 0:
		in_macro = 0
	first_line_of_macro = 0

# Processes special statement keywords and syntax
local procstmt():
	char **k
	char *c
	if (c = cstr_begins_with(l, "which ")):
		print("switch(")
		print(c)
		l = ")" ; len = 1
	eif cstr_begins_with(l, "eif "):
		print("else if(")
		print(l+4)
		l = ")" ; len = 1
		is_kwdparens = 1
	eif strcmp(l, "repeat") == 0:
		l = "while(1)" ; len = 8
	else:
		for k=kwdparens; *k != 0; ++k:
			int c = strlen(*k)
			if cstr_begins_with(l, *k) && (l[c] == ' ' || l[c] == '\0'):
				if l[c] == ' ':
					l[c] = '('
					print(l)
					l = ")" ; len = 1
				is_kwdparens = 1
				break

# Reads a line from the input vector
local int readln(vec *lines, ssize_t lineno):
	if lineno >= veclen(lines):
		return 0
	l = *(cstr*)v(lines, lineno)
	len = strlen(l)
	return 1

# Returns the last character of the current line
local char last():
	if len == 0:
		return '\0'
	return l[len-1]

# Counts and removes leading tabs from the current line
local int striptabs():
	int tabs = 0
	while l[0] == '\t':
		++l
		++tabs
		--len
	return tabs

# Checks for invalid spacing at start/end of line
local fussy():
	if l[0] == ' ':
		error("two spaces at start of line")
	if last() == ' ':
		error("space at end of line")

# Returns length of identifier/word at start of line
local int wordlen():
	return strspn(l, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_0123456789.")

# Returns length until first tab character
local int caselen():
	return strcspn(l, "\t")

# Removes a single leading space if present
local strip_one_space_maybe():
	if l[0] == ' ':
		++l
		--len

# Prints specified number of tab characters
local indent(int tabs):
	for ; tabs>0; --tabs:
		print("\t")

# Adds void return type to functions without explicit return type
local addvoids():
	char *c1 = cstr_begins_with(l, "extern \"C\" ")
	if c1:
		print("extern \"C\" ")
		l = c1
	int addvoid = 1
	char *c = l
	for ; *c != 0; ++c:
		if *c == ' ':
			addvoid = 0
		if *c == '(':
			if addvoid:
				if cstr_begins_with(l, "main("):
					print("int ")
					blocktype[tabs] = VOID_MAIN
				else:
					print("void ")
			if c[1] == ')':
				c[1] = '\0'
				print(l)
				c[1] = ')'
				print("void")
				len -= (c - l) + 1
				l = c + 1
			break

# Checks if declaration is a class-like construct
local int classy(char *c):
	char *spc = strchr(c, ' ')
	char *colon = strchr(c, ':')
	char *paren = strchr(c, '(')
	return !paren && (!spc || colon == spc + 1 || colon < spc)
