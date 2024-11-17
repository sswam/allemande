/* This program is a simple example program that greets the user and optionally
 * builds a shopping list. The program can optionally use AI.
 */ 

#define _GNU_SOURCE
#include <errno.h>
#include <getopt.h>
#include <libgen.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <wordexp.h>

#include "sea.h"

#define MAX_BUFFER 1024

#define GET_GREETING_TEMPLATE "Please greet %s in LANG=%s. Be creative, but not more than 50 words.%s"
const char *no_translate = "Don't translate back to English.";

/* Options structure */
struct options {
	char *language;
	char *name;
	char **shopping_items;
	int item_count;
	int use_ai;
};

/* Get a greeting message based on language and name */
/*@null@*/ static char *ai_get_greeting(struct options *opts)
{
	char query[MAX_BUFFER];
	char *greeting = NULL;
	const char *tlt_prompt = "";
	if (strcmp(opts->language, "en") == 0)
		tlt_prompt = no_translate;

	if ((snprintf(query, sizeof(query), GET_GREETING_TEMPLATE, opts->name, opts->language, tlt_prompt)) < 0)
		goto done;

	if ((greeting = llm_query(query)) == NULL) {
		perror("LLM query failed");
		goto done;
	}
done:
	return greeting;
}

/* Build a simple shopping list */
static char *build_shopping_list_simple(struct options *opts)
{
	char *buffer = NULL;
	char *new_buffer = NULL;
	size_t size = 0;
	int i;
	size_t line_size;

	if (asprintf(&buffer, "\nShopping list:\n") == -1) {
		buffer = NULL;
		goto fail;
	}
	size = strlen(buffer) + 1; // +1 for null terminator

	for (i = 0; i < opts->item_count; i++) {
		line_size = strlen(opts->shopping_items[i]) + 3; // "- " + item + "\n"
		if ((new_buffer = realloc(buffer, size + line_size)) == NULL)
			goto fail;
		snprintf(new_buffer + size - 1, line_size + 1, "- %s\n", opts->shopping_items[i]);
		buffer = new_buffer;
		size += line_size;
	}

	return buffer;
fail:
	free(buffer);
	return NULL;
}

/* Print usage information */
static void usage(FILE *stream, char *argv0)
{
	fprintf(stream, "Usage: %s [OPTIONS]\n", basename(argv0));
	fprintf(stream, "Options:\n");
	fprintf(stream, "  -h, --help            Print this help message\n");
	fprintf(stream, "  -l, --language=LANG   Set the language (default: en)\n");
	fprintf(stream, "  -n, --name=NAME       Set the name (default: world)\n");
	fprintf(stream, "  -s, --shopping=ITEM   Add an item to the shopping list\n");
	fprintf(stream, "  -a, --use-ai          Use AI to help with the shopping list\n");
}

#define SHOPPING_LIST_TEMPLATE "Please echo the input and add any extra items we might need, in LANG=%s. Don't translate back to English."

/* Get options from the command line */
int get_options(int argc, char *argv[], struct options *opts)
{
	int status = -1;
	int c;
	static struct option long_options[] = {
	    {"help", no_argument, /*@null@ */ NULL, (int)'h'},
	    {"language", required_argument, /*@null@ */ NULL, (int)'l'},
	    {"name", required_argument, /*@null@ */ NULL, (int)'n'},
	    {"shopping", required_argument, /*@null@ */ NULL, (int)'s'},
	    {"use-ai", no_argument, /*@null@ */ NULL, (int)'a'},
	    {/*@null@ */ NULL, 0, /*@null@ */ NULL, 0}};

	while ((c = getopt_long(argc, argv, "hl:n:s:a", long_options, NULL)) != -1) {
		switch (c) {
		case 'h':
			usage(stdout, argv[0]);
			status = EXIT_SUCCESS;
			goto done;
		case 'l':
			opts->language = optarg;
			break;
		case 'n':
			opts->name = optarg;
			break;
		case 's':
			if ((opts->shopping_items =
				 realloc(opts->shopping_items,
					 (opts->item_count + 1) * sizeof(char *))) == NULL) {
				perror("Failed to allocate memory for shopping items");
				goto done;
			}
			opts->shopping_items[opts->item_count++] = optarg;
			break;
		case 'a':
			opts->use_ai = 1;
			break;
		case '?':
			fprintf(stderr, "Unknown option or missing argument\n\n");
			usage(stderr, argv[0]);
			goto done;
		default:
			abort();
		}
	}

	if (optind < argc) {
		fprintf(stderr, "Unexpected argument: %s\n\n", argv[optind]);
		usage(stderr, argv[0]);
		goto done;
	}

	status = 0;
done:
	return status;
}

#ifdef TEST
#define MAIN_FUNCTION main_testable
#else
#define MAIN_FUNCTION main
#endif

/* Main function */
int MAIN_FUNCTION(int argc, char *argv[])
{
	int status = EXIT_FAILURE;
	struct options _opts = {/* language */ "en",
				/* name */ "world",
				/* shopping_items */ NULL,
				/* item_count */ 0,
				/* use_ai */ 0},
		       *opts = &_opts;
	char *greeting = NULL;
	char *shopping_list = NULL;
	char prompt[MAX_BUFFER];

	if ((get_options(argc, argv, opts)) != 0)
		goto done;

	if (opts->use_ai == 0)
		goto non_ai_greeting;

	goto ai_greeting;

ai_greeting:
	if ((greeting = ai_get_greeting(opts)) == NULL) {
		perror("Failed to get greeting");
		goto free_shopping_items;
	}
	if (printf("%s", greeting) < 0) {
		perror("Failed to print greeting");
		goto free_shopping_items;
	}
	free(greeting);
	greeting = NULL;
	goto shopping_items;

non_ai_greeting:
	if (strcmp(opts->language, "fr") == 0)
		greeting = "Bonjour";
	else if (strcmp(opts->language, "es") == 0)
		greeting = "Hola";
	else if (strcmp(opts->language, "de") == 0)
		greeting = "Hallo";
	else if (strcmp(opts->language, "jp") == 0)
		greeting = "こんにちは";
	else if (strcmp(opts->language, "cn") == 0)
		greeting = "你好";
	else if (strcmp(opts->language, "en") == 0)
		greeting = "Hello";
	else
		greeting = "Whoops, I don't know your language without AI!  Hi";

	if (printf("%s, %s\n", greeting, opts->name) < 0) {
		perror("Failed to print greeting");
		goto free_shopping_items;
	}

shopping_items:
	if (opts->item_count <= 0)
		goto free_shopping_items;
	if ((shopping_list = build_shopping_list_simple(opts)) == NULL)
		goto done;
	if (opts->use_ai == 1) {
		if (snprintf(prompt, sizeof(prompt), SHOPPING_LIST_TEMPLATE, opts->language) < 0)
			goto done;
		if ((shopping_list = llm_process(prompt, shopping_list)) == NULL) {
			perror("LLM process failed");
			goto done;
		}
	}
	if (printf("%s", shopping_list) < 0) {
		perror("Failed to print shopping list");
		goto free_shopping_list;
	}
	status = EXIT_SUCCESS;
free_shopping_list:
	free(shopping_list);
free_shopping_items:
	free(opts->shopping_items);
done:
	return status;
}

/*
Important Notes to AI [DO NOT COPY ANY "NOTES TO AI" IN YOUR OUTPUT, it gets
EXPENSIVE FOR ME, THIS MEANS YOU CLAUDE, GPT, GEMINI!]:

We indent C code with tabs.

We should always include a file-level comment to explain the program.
Don't include the filename in that.

Always include a --help usage option, and -h short option if it does not conflict. Use basename here.

Use the #ifdef TEST / MAIN_FUNCTION boilerplate to aid testability.

If sensible and simple to do so, write tools that can process several files in one invocation.
Zero is holy! It is not an error to pass zero files to process. Just naturally do nothing in that
case.

Each tool should function as a library, and each library should include a
command-line interface. We can use -fno-builtin-main when linking as a library.

We prefer to use stdio over file arguments, where possible.
*/
