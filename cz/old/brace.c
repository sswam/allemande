/*
* A C program that converts Python-like code without braces and semicolons into regular C code,
* and also performs the reverse operation. Supports multiple languages.
* Improved to handle punctuation correctly, especially within strings and comments.
* Fixed indent level issue when removing punctuation from C code.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <libgen.h>

#define VERSION "3.0.2"
#define MAX_LINE_LENGTH 2000
#define MAX_INDENT 100
#define INDENT_SIZE 4  // Number of spaces per indent level

typedef enum { C_LANG, PYTHON, JAVASCRIPT, DART, PERL, BASH } Language;

char* trim(char* str);
int get_indent_level(const char* line);
void add_punctuation(FILE* input, FILE* output, Language lang);
void remove_punctuation(FILE* input, FILE* output, Language lang);
void process_file(const char* input_file, const char* output_file, int add_punct, Language lang);

/* Function Prototypes */
int main(int argc, char* argv[]) {
    if (argc != 5) {
        fprintf(stderr, "%s version %s\n", basename(argv[0]), VERSION);
        fprintf(stderr, "Usage: %s <input_file> <output_file> <add|remove> <language>\n", basename(argv[0]));
        return EXIT_FAILURE;
    }

    int add_punct = strcmp(argv[3], "add") == 0;
    Language lang;

    if (strcmp(argv[4], "c") == 0) lang = C_LANG;
    else if (strcmp(argv[4], "python") == 0) lang = PYTHON;
    else if (strcmp(argv[4], "javascript") == 0) lang = JAVASCRIPT;
    else if (strcmp(argv[4], "dart") == 0) lang = DART;
    else if (strcmp(argv[4], "perl") == 0) lang = PERL;
    else if (strcmp(argv[4], "bash") == 0) lang = BASH;
    else {
        fprintf(stderr, "Unsupported language: %s\n", argv[4]);
        return EXIT_FAILURE;
    }

    process_file(argv[1], argv[2], add_punct, lang);
    return EXIT_SUCCESS;
}

void process_file(const char* input_file, const char* output_file, int add_punct, Language lang) {
    FILE* input = fopen(input_file, "r");
    if (!input) {
        perror("Error opening input file");
        exit(EXIT_FAILURE);
    }

    FILE* output = fopen(output_file, "w");
    if (!output) {
        perror("Error opening output file");
        fclose(input);
        exit(EXIT_FAILURE);
    }

    if (add_punct) {
        add_punctuation(input, output, lang);
    } else {
        remove_punctuation(input, output, lang);
    }

    fclose(input);
    fclose(output);
}

char* trim(char* str) {
    char* end;
    // Trim leading space
    while (isspace((unsigned char)*str)) str++;
    if (*str == 0) return str;
    // Trim trailing space
    end = str + strlen(str) - 1;
    while (end > str && isspace((unsigned char)*end)) end--;
    *(end + 1) = '\0';
    return str;
}

int get_indent_level(const char* line) {
    int level = 0;
    int spaces = 0;
    int tabs = 0;
    while (*line == ' ' || *line == '\t') {
        if (*line == ' ') {
            spaces++;
            if (spaces == INDENT_SIZE) {
                level++;
                spaces = 0;
            }
        } else if (*line == '\t') {
            level++;
            spaces = 0;
        }
        line++;
    }
    return level;
}

int is_inside_quotes(const char* line, int index) {
    int in_single = 0, in_double = 0;
    for (int i = 0; i < index; i++) {
        if (line[i] == '"' && !in_single) {
            in_double = !in_double;
        } else if (line[i] == '\'' && !in_double) {
            in_single = !in_single;
        } else if (line[i] == '\\') {
            i++; // Skip escaped character
        }
    }
    return in_single || in_double;
}

void add_punctuation(FILE* input, FILE* output, Language lang) {
    char line[MAX_LINE_LENGTH];
    int indent_stack[MAX_INDENT];
    int stack_top = 0;

    while (fgets(line, sizeof(line), input)) {
        char original_line[MAX_LINE_LENGTH];
        strcpy(original_line, line); // Preserve original for accurate indentation
        char* trimmed = trim(line);
        int indent = get_indent_level(original_line);

        // Close blocks if current indent is less than stack top
        while (stack_top > 0 && indent < indent_stack[stack_top - 1]) {
            fprintf(output, "%*s}\n", indent_stack[--stack_top] * INDENT_SIZE, "");
        }

        // Write the original line
        fprintf(output, "%s", original_line);

        // Check if the line ends with a colon (for block start in Python-like syntax)
        int len = strlen(trimmed);
        if (len > 0 && trimmed[len - 1] == ':') {
            trimmed[len - 1] = '\0'; // Remove the colon
            fprintf(output, " {\n");
            if (stack_top < MAX_INDENT) {
                indent_stack[stack_top++] = indent + 1;
            } else {
                fprintf(stderr, "Indent stack overflow\n");
                exit(EXIT_FAILURE);
            }
        } else if (lang != PYTHON && lang != BASH) {
            // Avoid adding semicolon to lines that already have one or are block statements
            if (trimmed[len - 1] != ';' && trimmed[len - 1] != '{' && trimmed[len - 1] != '}') {
                fprintf(output, ";\n");
            }
        }
    }

    // Close any remaining open blocks
    while (stack_top > 0) {
        fprintf(output, "%*s}\n", indent_stack[--stack_top] * INDENT_SIZE, "");
    }
}

void remove_punctuation(FILE* input, FILE* output, Language lang) {
    char line[MAX_LINE_LENGTH];
    int indent_level = 0;
    int in_multiline_comment = 0;

    while (fgets(line, sizeof(line), input)) {
        char new_line[MAX_LINE_LENGTH] = "";
        int i = 0;
        int len = strlen(line);
        int current_indent = get_indent_level(line);

        while (i < len) {
            // Handle multiline comments
            if (in_multiline_comment) {
                if (line[i] == '*' && line[i + 1] == '/') {
                    in_multiline_comment = 0;
                    i += 2;
                    continue;
                }
                i++;
                continue;
            }

            // Start of multiline comment
            if (line[i] == '/' && line[i + 1] == '*') {
                in_multiline_comment = 1;
                i += 2;
                continue;
            }

            // Start of single line comment
            if (line[i] == '/' && line[i + 1] == '/') {
                // Append the rest of the line as is
                strcat(new_line, &line[i]);
                break;
            }

            // Handle string literals
            if (line[i] == '"' || line[i] == '\'') {
                char quote = line[i];
                strncat(new_line, &line[i], 1);
                i++;
                while (i < len) {
                    strncat(new_line, &line[i], 1);
                    if (line[i] == '\\') {
                        strncat(new_line, &line[i + 1], 1);
                        i += 2; // Skip escaped character
                        continue;
                    }
                    if (line[i] == quote) {
                        i++;
                        break;
                    }
                    i++;
                }
                continue;
            }

            // Remove semicolons and braces if not within strings or comments
            if (line[i] == ';' && lang != PYTHON && lang != BASH) {
                i++;
                continue;
            }
            if ((line[i] == '{' || line[i] == '}') && lang == C_LANG) {
                if (line[i] == '}') {
                    if (indent_level > 0)
                        indent_level--;
                } else if (line[i] == '{') {
                    indent_level++;
                }
                i++;
                continue;
            }

            // Accumulate other characters
            strncat(new_line, &line[i], 1);
            i++;
        }

        // Trim the new line and add indentation
        char* trimmed = trim(new_line);
        if (trimmed[0] == '\0') {
            // Empty line after trimming, skip
            continue;
        }

        // Output the line with proper indentation
        fprintf(output, "%*s%s\n", indent_level * INDENT_SIZE, "", trimmed);
    }
}
