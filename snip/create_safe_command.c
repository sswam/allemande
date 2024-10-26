/* Create a safe command string by expanding a format string with wordexp */
char *create_safe_command(const char *format, ...)
{
	char *raw_command;
	va_list args;
	wordexp_t p;
	char *safe_command = NULL;
	size_t i;
	size_t total_len = 0;
	char *ptr = NULL;
	int result;

	if (format == NULL) {
		errno = EINVAL;
		goto done;
	}

	va_start(args, format);
	if (vasprintf(&raw_command, format, args) == -1) {
		errno = ENOMEM;
		goto va_end;
	}

	if ((result = wordexp(raw_command, &p, WRDE_NOCMD)) != 0) {
		errno = result == WRDE_NOSPACE ? ENOMEM : EINVAL;
		goto free_raw_command;
	}

	if (p.we_wordc == 0) {
		errno = EINVAL;
		goto wordfree_p;
	}

	for (i = 0; i < p.we_wordc; i++)
		total_len += strlen(p.we_wordv[i]) + 1; // +1 for space or null terminator

	if ((ptr = safe_command = malloc(total_len)) == NULL) {
		errno = ENOMEM;
		goto wordfree_p;
	}

	for (i = 0; i < p.we_wordc; i++)
		ptr += snprintf(ptr, total_len - (ptr - safe_command), "%s%s", i > 0 ? " " : "", p.we_wordv[i]);

wordfree_p:
	wordfree(&p);
free_raw_command:
	free(raw_command);
va_end:
	va_end(args);
done:
	return safe_command;
}


