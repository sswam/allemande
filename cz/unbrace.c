#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <stdlib.h>

#define MAX_LINE 4096

/* Remove trailing whitespace and return pointer to last non-whitespace char */
static char *trim_end(char *line) {
	char *end = line + strlen(line) - 1;

	while (end >= line && (*end == ' ' || *end == '\n' || *end == '\t'))
		*end-- = '\0';
	return end;
}

/* Skip leading whitespace and return pointer to first non-whitespace char */
static char *find_start(char *line) {
	while (*line == ' ' || *line == '\t')
		line++;
	return line;
}

/* Returns true if line starts with a preprocessor directive */
static bool is_preprocessor(char *line) {
	return *line == '#';
}

/* Process a single line, removing braces/semicolons */
static void process_line(FILE *out, char *line) {
	bool colon = false;
	char *start, *start2;
	char *end = trim_end(line);

	if (end < line) {
		/* Empty line */
		putc('\n', out);
		return;
	}

	start = find_start(line);

	if (is_preprocessor(start)) {
		/* Preprocessor directives are not altered */
		fprintf(out, "%s\n", line);
		return;
	}
	if (*end == '{') {
		colon = true;
		*end = '\0';
	} else if (*end == ';') {
		*end = '\0';
	}
	if (*start == '}') {
		start2 = find_start(start + 1);
		memmove(start, start2, strlen(start2) + 1);
	}
	end = trim_end(line);

	if (colon)
		fprintf(out, "%s:\n", line);
	else
		fprintf(out, "%s\n", line);
}

/* Convert braced code to non-braced form with proper indentation
    * Returns 0 on success, 1 if input contains lines exceeding MAX_LINE
    */
int unbrace(FILE *in, FILE *out) {
	char line[MAX_LINE];

	while (fgets(line, sizeof(line), in)) {
		if (strlen(line) == MAX_LINE - 1 && line[MAX_LINE-2] != '\n') {
			fprintf(stderr, "Error: line too long (max %d chars)\n", MAX_LINE-1);
			return 1;
		}
		process_line(out, line);
	}

	return 0;
}

int main() {
	return unbrace(stdin, stdout);
}
