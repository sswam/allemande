// 2>/dev/null; set -e; X=${0%.c} ; [ "$X" -nt "$0" ] || cc -o "$X" -I$HOME/kisskit "$0" && hide "$X"; exec "$X" "$@"
/* a C program that attempts to convert Python-like code without braces and semicolons into regular C code. It also includes a reverse operation and support for some other languages. Note that this is a simplified implementation and may not cover all edge cases or language-specific nuances. */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_LINE_LENGTH 1000
#define MAX_INDENT 100

typedef enum { C, PYTHON, JAVASCRIPT, DART, PERL, BASH } Language;

char* trim(char* str);
int get_indent_level(const char* line);
void add_punctuation(FILE* input, FILE* output, Language lang);
void remove_punctuation(FILE* input, FILE* output, Language lang);
void process_file(const char* input_file, const char* output_file, int add_punct, Language lang);

int main(int argc, char* argv[]) {
    if (argc != 5) {
        fprintf(stderr, "Usage: %s <input_file> <output_file> <add|remove> <language>\n", argv[0]);
        return 1;
    }

    int add_punct = strcmp(argv[3], "add") == 0;
    Language lang;
    if (strcmp(argv[4], "c") == 0) lang = C;
    else if (strcmp(argv[4], "python") == 0) lang = PYTHON;
    else if (strcmp(argv[4], "javascript") == 0) lang = JAVASCRIPT;
    else if (strcmp(argv[4], "dart") == 0) lang = DART;
    else if (strcmp(argv[4], "perl") == 0) lang = PERL;
    else if (strcmp(argv[4], "bash") == 0) lang = BASH;
    else {
        fprintf(stderr, "Unsupported language: %s\n", argv[4]);
        return 1;
    }

    process_file(argv[1], argv[2], add_punct, lang);
    return 0;
}

void process_file(const char* input_file, const char* output_file, int add_punct, Language lang) {
    FILE* input = fopen(input_file, "r");
    FILE* output = fopen(output_file, "w");

    if (!input || !output) {
        fprintf(stderr, "Error opening files\n");
        exit(1);
    }
    if (add_punct) add_punctuation(input, output, lang);
    else remove_punctuation(input, output, lang);
    fclose(input);
    fclose(output);
}

char* trim(char* str) {
    char* end;
    while (isspace(*str)) str++;
    if (*str == 0) return str;
    end = str + strlen(str) - 1;
    while (end > str && isspace(*end)) end--;
    *(end + 1) = 0;
    return str;
}

int get_indent_level(const char* line) {
    int level = 0;
    while (*line == ' ' || *line == '\t') {
        level++;
        line++;
    }
    return level;
}

void add_punctuation(FILE* input, FILE* output, Language lang) {
    char line[MAX_LINE_LENGTH];
    int indent_stack[MAX_INDENT] = {0};
    int stack_top = 0;

    while (fgets(line, sizeof(line), input)) {
        char* trimmed = trim(line);
        int indent = get_indent_level(line);

        while (stack_top > 0 && indent < indent_stack[stack_top - 1]) {
            fprintf(output, "%*s}\n", indent_stack[--stack_top], "");
        }

        fprintf(output, "%s", line);
        if (strlen(trimmed) > 0 && trimmed[strlen(trimmed) - 1] == ':') {
            trimmed[strlen(trimmed) - 1] = ' ';
            fprintf(output, "{\n");
            indent_stack[stack_top++] = indent;
        } else if (lang != PYTHON && lang != BASH && !strchr(trimmed, '{') && !strchr(trimmed, '}')) {
            fprintf(output, ";\n");
        }
    }

    while (stack_top > 0) {
        fprintf(output, "%*s}\n", indent_stack[--stack_top], "");
    }
}

void remove_punctuation(FILE* input, FILE* output, Language lang) {
    char line[MAX_LINE_LENGTH];
    int indent_level = 0;

    while (fgets(line, sizeof(line), input)) {
        char* trimmed = trim(line);
        int current_indent = get_indent_level(line);

        if (strchr(trimmed, '{')) {
            trimmed[strlen(trimmed) - 1] = ':';
            fprintf(output, "%s\n", trimmed);
            indent_level++;
        } else if (strchr(trimmed, '}')) {
            indent_level--;
        } else {
            if (lang != PYTHON && lang != BASH) {
                int len = strlen(trimmed);
                if (len > 0 && trimmed[len - 1] == ';') {
                    trimmed[len - 1] = '\0';
                }
            }
            fprintf(output, "%*s%s\n", indent_level * 4, "", trimmed);
        }
    }
}
