// #!/usr/bin/env ccx

// TODO issue, relative paths in INPUTS won't work if executed from another directory

#define _POSIX_C_SOURCE 200809L
#define _DEFAULT_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <getopt.h>
#include <limits.h>

#define MAX_CMD 4096
#define MAX_LINE 1024
#define VERSION "1.0.8"

struct build_vars {
	char cc[MAX_LINE];
	char cppflags[MAX_LINE];
	char cflags[MAX_LINE];
	char inputs[MAX_LINE];
	char ldflags[MAX_LINE];
	char ldlibs[MAX_LINE];
	char pkgs[MAX_LINE];
	char has_shebang;
};

// Check if file exists and return its modification time
time_t get_mod_time(const char *path)
{
	struct stat st;
	if (stat(path, &st) == 0) {
		return st.st_mtime;
	}
	return 0;
}

// Parse a single build variable from a comment line
static void parse_build_var(const char *line, const char *prefix, char *dest, size_t dest_size)
{
	const char *start;
	size_t prefix_len;
	char *nl;

	prefix_len = strlen(prefix);
	if (strncmp(line, prefix, prefix_len) != 0) {
		return;
	}

	start = line + prefix_len;
	while (*start == ' ' || *start == '\t') {
		start++;
	}

	strncpy(dest, start, dest_size - 1);
	dest[dest_size - 1] = '\0';

	nl = strchr(dest, '\n');
	if (nl) {
		*nl = '\0';
	}
}

// Extract build variables from source file (CC, CFLAGS, LDLIBS, OBJECTS)
// Only looks at top of file, before first blank line
void get_build_vars(const char *src, struct build_vars *vars)
{
	FILE *f;
	char line[MAX_LINE];
	char shebang_checked = 0;

	// Set defaults
	strcpy(vars->cc, "gcc");
	strcpy(vars->cppflags, "-D_GNU_SOURCE -D_FILE_OFFSET_BITS=64");
	strcpy(vars->cflags, "-std=gnu99 -Wall -Wextra -Wstrict-prototypes -g -ggdb");
	strcpy(vars->inputs, "");
	strcpy(vars->ldlibs, "");
	strcpy(vars->ldflags, "");
	strcpy(vars->pkgs, "");
	vars->has_shebang = 0;

	f = fopen(src, "r");
	if (!f) {
		return;
	}

	while (fgets(line, sizeof(line), f)) {
		// Stop at first blank line or non-comment/non-shebang line
		if (line[0] == '\n' || line[0] == '\0') {
			break;
		}

		if (!shebang_checked) {
			vars->has_shebang = (strncmp(line, "#!", 2) == 0);
			shebang_checked = 1;
		}

		// Skip shebang
		if (strncmp(line, "#!", 2) == 0) {
			continue;
		}

		// Stop at non-comment lines
		if (strncmp(line, "//", 2) != 0) {
			break;
		}

		// Parse build variables
		parse_build_var(line, "// CC:", vars->cc, sizeof(vars->cc));
		parse_build_var(line, "// CPPFLAGS:", vars->cppflags, sizeof(vars->cppflags));
		parse_build_var(line, "// CFLAGS:", vars->cflags, sizeof(vars->cflags));
		parse_build_var(line, "// INPUTS:", vars->inputs, sizeof(vars->inputs));
		parse_build_var(line, "// LDFLAGS:", vars->ldflags, sizeof(vars->ldflags));
		parse_build_var(line, "// LDLIBS:", vars->ldlibs, sizeof(vars->ldlibs));
		parse_build_var(line, "// PKGS:", vars->pkgs, sizeof(vars->pkgs));
	}

	fclose(f);
}

// Dump build variables (for debugging)
void dump_build_vars(struct build_vars *vars)
{
	printf("Build variables:\n");
	printf("  CC: %s\n", vars->cc);
	printf("  CPPFLAGS: %s\n", vars->cppflags);
	printf("  CFLAGS: %s\n", vars->cflags);
	printf("  INPUTS: %s\n", vars->inputs);
	printf("  LDFLAGS: %s\n", vars->ldflags);
	printf("  LDLIBS: %s\n", vars->ldlibs);
	printf("  PKGS: %s\n", vars->pkgs);
}

// Modify program name to get source name
char *prog_source_name(char *prog)
{
	char *slash = strrchr(prog, '/');
	if (slash)
		prog = slash + 1;
	if (prog[0] == '.')
		prog++;
	char *dot = strrchr(prog, '.');
	if (dot && strcmp(dot, ".elf") == 0)
		*dot = '\0';
	return prog;
}

int main(int argc, char *argv[])
{
	char *src, *basename, *last_slash;
	struct build_vars vars;
	char out[PATH_MAX];
	char real_src_path[PATH_MAX];
	char *cmd_template = "tail -n+1 %s | %s %s %s%s -o %s -x c - -x none %s %s %s%s";
	char *cmd_template_skip = "tail -n+2 %s | %s %s %s%s -o %s -x c - -x none %s %s %s%s";
	char *cmd_template_pkg_config = "tail -n+1 %s | %s %s %s `pkg-config --cflags %s` -o %s -x c - -x none %s %s %s `pkg-config --libs %s`";
	char *cmd_template_pkg_config_skip = "tail -n+2 %s | %s %s %s `pkg-config --cflags %s` -o %s -x c - -x none %s %s %s `pkg-config --libs %s`";
	char cmd[MAX_CMD];
	time_t src_time, out_time;
	int status;
	char **new_argv;
	int i, dir_len;
	char *verbose;
	int opt;
	int force_rebuild = 0;
	int compile_only = 0;

	static struct option long_options[] = {
		{"help", no_argument, 0, 'h'},
		{"compile", no_argument, 0, 'c'},
		{"force", no_argument, 0, 'f'},
		{0, 0, 0, 0}
	};

	// set verbose from env CCX_VERBOSE
	verbose = getenv("CCX_VERBOSE");
	if (verbose && strcmp(verbose, "1"))
		verbose = NULL;

	while ((opt = getopt_long(argc, argv, "+hcf", long_options, NULL)) != -1) {
		switch (opt) {
		case 'h':
			printf("Usage: %s [options] <source.c> [args...]\n", argv[0]);
			printf("Options:\n");
			printf("  -h, --help     Show this help message\n");
			printf("  -c, --compile  Build the program but do not execute it\n");
			printf("  -f, --force    Force rebuild even if executable is up-to-date\n");
			printf("Version: %s\n", VERSION);
			return 0;
		case 'c':
			compile_only = 1;
			break;
		case 'f':
			force_rebuild = 1;
			break;
		default:
			fprintf(stderr, "Usage: %s [options] <source.c> [args...]\n", argv[0]);
			fprintf(stderr, "Try '%s --help' for more information.\n", argv[0]);
			return 1;
		}
	}

	if (optind >= argc) {
		fprintf(stderr, "Usage: %s [options] <source.c> [args...]\n", argv[0]);
		fprintf(stderr, "Try '%s --help' for more information.\n", argv[0]);
		return 1;
	}

	// modify argv[0], skip leading ".", cut off final .elf
	if (argc > 0)
		argv[0] = prog_source_name(argv[0]);

	src = argv[optind];

	if (realpath(src, real_src_path) == NULL) {
		fprintf(stderr, "Error resolving path for: %s\n", src);
		perror("realpath");
		return 1;
	}
	src = real_src_path;

	// Create output filename
	last_slash = strrchr(src, '/');
	// last_slash is guaranteed to be non-NULL because realpath returns an absolute path
	basename = last_slash + 1;
	dir_len = (int)(last_slash - src) + 1;

	if ((size_t)dir_len + 1 + strlen(basename) + 4 >= sizeof(out)) {
		fprintf(stderr, "Output path too long\n");
		return 1;
	}

	strncpy(out, src, dir_len);
	out[dir_len] = '\0';
	strcat(out, ".");
	strcat(out, basename);
	strcat(out, ".elf");

	// Check if rebuild is needed
	src_time = get_mod_time(src);
	out_time = get_mod_time(out);

	if (force_rebuild || !out_time || src_time > out_time) {
		// Get build variables
		get_build_vars(src, &vars);
		if (verbose)
			dump_build_vars(&vars);

		// Build command: tail -n+2 $SOURCE | $CC $CPPFLAGS $CFLAGS `pkg-config --cflags $PKGS` -o $OUT -x c - -x none $INPUTS $LDFLAGS $LDLIBS `pkg-config --libs $PKGS`
		char *template = vars.has_shebang ? (*vars.pkgs ? cmd_template_pkg_config_skip : cmd_template_skip) : (*vars.pkgs ? cmd_template_pkg_config : cmd_template);
		status = snprintf(cmd, sizeof(cmd), template,
			src,
			vars.cc,
			vars.cppflags,
			vars.cflags,
			vars.pkgs,
			out,
			vars.inputs,
			vars.ldflags,
			vars.ldlibs,
			vars.pkgs
		);

		if (status >= (int)sizeof(cmd)) {
			fprintf(stderr, "Build command too long\n");
			return 1;
		}

		// Print command if verbose
		if (verbose)
			fprintf(stderr, "Executing: %s\n", cmd);

		// Execute compilation
		status = system(cmd);
		if (status != 0) {
			return 1;
		}
	}

	if (compile_only) {
		return 0;
	}

	// Modify argv to execute the compiled binary
	new_argv = malloc(sizeof(char*) * (argc - optind));
	if (!new_argv) {
		perror("malloc");
		return 1;
	}

	new_argv[0] = prog_source_name(strdup(out));

	for (i = optind + 1; i < argc; i++) {
		new_argv[i - optind] = argv[i];
	}
	new_argv[argc - optind] = NULL;

	execv(out, new_argv);

	// If execv returns, there was an error
	perror("execv failed");
	free(new_argv[0]);
	free(new_argv);
	return 1;
}
