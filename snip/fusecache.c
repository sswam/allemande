// Helper to verify if a resolved path is a subpath of a resolved base directory.
static int is_subpath(const char *resolved_path, const char *resolved_base_dir) {
	size_t base_len = strlen(resolved_base_dir);
	if (strncmp(resolved_path, resolved_base_dir, base_len) != 0) {
		return 0; // Not a subpath
	}

	// Check if it's the directory itself or a file/dir within it.
	// This prevents matching "/base/dir-foo" with base "/base/dir".
	char separator = resolved_path[base_len];
	return separator == '\0' || separator == '/';
}

// Security helper: validates that a constructed path is within a base directory.
static char *resolve_and_verify_path(const char *base_dir, const char *path)
{
	char *resolved_base = realpath(base_dir, NULL);
	if (!resolved_base) {
		return NULL; // Base directory must exist and be accessible.
	}

	char *full_path;
	if (asprintf(&full_path, "%s/%s", resolved_base, path) == -1) {
		free(resolved_base);
		return NULL; // ENOMEM
	}

	char *resolved_path = realpath(full_path, NULL);
	if (resolved_path) {
		// Path exists, verify it's within the resolved base directory.
		if (is_subpath(resolved_path, resolved_base)) {
			free(full_path);
			free(resolved_base);
			return resolved_path; // OK
		}
		// Traversal detected
		free(resolved_path);
	} else if (errno == ENOENT) {
		// Path doesn't exist. Check its parent to allow file creation.
		char *full_path_copy = strdup(full_path);
		if (!full_path_copy) {
			free(full_path);
			free(resolved_base);
			errno = ENOMEM;
			return NULL;
		}

		char *parent_dir = dirname(full_path_copy);
		char *resolved_parent = realpath(parent_dir, NULL);
		free(full_path_copy);

		if (resolved_parent && is_subpath(resolved_parent, resolved_base)) {
			// Parent is valid, so the new path is safe to create.
			// Return the non-resolved, concatenated path for the caller to use.
			free(resolved_parent);
			free(resolved_base);
			return full_path;
		}
		if (resolved_parent) free(resolved_parent);
	}

	// Failure case: traversal, or an error other than ENOENT.
	free(full_path);
	free(resolved_base);
	errno = EACCES;
	return NULL;
}
