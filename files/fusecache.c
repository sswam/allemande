#!/usr/bin/env ccx
// CFLAGS: -Wall -D_FILE_OFFSET_BITS=64 -D_GNU_SOURCE
// PKGS: fuse3

#define FUSE_USE_VERSION 31

#include <fuse.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <stddef.h>
#include <assert.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <dirent.h>
#include <libgen.h>
#include <time.h>

/*
 * This struct will hold the configuration for our filesystem.
 * We'll pass a pointer to this in the private_data field of fuse_context.
 */
struct fusecache_config {
	char *source_dir;
	char *cache_dir;
};

// Security helper: validates that a constructed path is within a base directory.
// It returns a newly allocated, resolved path on success, or NULL on failure.
// On failure, errno is set to EACCES for traversal, or other errors from realpath.
static char *resolve_and_verify_path(const char *base_dir, const char *path)
{
	char *full_path;
	if (asprintf(&full_path, "%s%s", base_dir, path) == -1)
		return NULL;	// ENOMEM

	char *resolved = realpath(full_path, NULL);
	if (resolved) {
		// Path exists, verify it's a subpath of base_dir
		size_t base_len = strlen(base_dir);

		if (strncmp(resolved, base_dir, base_len) == 0 && (resolved[base_len] == '\0' || resolved[base_len] == '/')) {
			free(full_path);
			return resolved;  // OK
		}
		free(resolved);
		free(full_path);
		errno = EACCES;	// Traversal detected
		return NULL;
	}

	if (errno != ENOENT) {
		// Some other error like ELOOP, EACCES on a parent dir, etc.
		free(full_path);
		return NULL;
	}
	// Path doesn't exist. Check its parent.
	char *full_path_copy = strdup(full_path);
	if (!full_path_copy) {
		free(full_path);
		errno = ENOMEM;
		return NULL;
	}
	char *parent = dirname(full_path_copy);
	char *resolved_parent = realpath(parent, NULL);
	free(full_path_copy);

	if (!resolved_parent) {
		// Parent doesn't exist or other error.
		free(full_path);
		return NULL;
	}
	// Verify parent is a subpath of base_dir
	size_t base_len = strlen(base_dir);

	if (strncmp(resolved_parent, base_dir, base_len) == 0 && (resolved_parent[base_len] == '\0' || resolved_parent[base_len] == '/')) {
		free(resolved_parent);
		// Parent is OK, so return the original, non-resolved path
		return full_path;
	}

	free(resolved_parent);
	free(full_path);
	errno = EACCES;		// Parent is outside base dir, traversal detected
	return NULL;
}

// Helper to get the full path in the source directory.
// The caller is responsible for freeing the returned string.
static char *get_source_path(const char *path)
{
	struct fusecache_config *conf = (struct fusecache_config *) fuse_get_context()->private_data;
	return resolve_and_verify_path(conf->source_dir, path);
}

// Helper to get the full path in the cache directory.
// The caller is responsible for freeing the returned string.
static char *get_cache_path(const char *path)
{
	struct fusecache_config *conf = (struct fusecache_config *) fuse_get_context()->private_data;
	return resolve_and_verify_path(conf->cache_dir, path);
}

// Filesystem operations

// Get file attributes, similar to stat().
static int fusecache_getattr(const char *path, struct stat *stbuf, struct fuse_file_info *fi)
{
	(void) fi;
	char *source_path = get_source_path(path);
	if (!source_path)
		return -ENOMEM;

	int res = lstat(source_path, stbuf);
	free(source_path);

	if (res == -1)
		return -errno;

	return 0;
}

// Read directory entries.
static int fusecache_readdir(const char *path, void *buf, fuse_fill_dir_t filler, off_t offset, struct fuse_file_info *fi, enum fuse_readdir_flags flags)
{
	(void) offset;
	(void) fi;
	(void) flags;

	char *source_path = get_source_path(path);
	if (!source_path)
		return -ENOMEM;

	DIR *dp = opendir(source_path);
	if (dp == NULL) {
		int err = -errno;
		free(source_path);
		return err;
	}

	struct dirent *de;
	while ((de = readdir(dp)) != NULL)
		filler(buf, de->d_name, NULL, 0, 0);

	closedir(dp);
	free(source_path);
	return 0;
}

// Creates parent directories for a given file path, like "mkdir -p".
static int ensure_dirs_exist(const char *path)
{
	char *p, *dir_path;
	dir_path = strdup(path);
	if (!dir_path)
		return -ENOMEM;

	for (p = strchr(dir_path + 1, '/'); p; p = strchr(p + 1, '/')) {
		*p = '\0';
		if (mkdir(dir_path, 0755) == -1 && errno != EEXIST) {
			int err = errno;
			free(dir_path);
			return -err;
		}
		*p = '/';
	}

	free(dir_path);
	return 0;
}

// Copies a file from source_path to cache_path.
static int copy_file_content(const char *source_path, const char *cache_path)
{
	int src_fd, cache_fd;
	char buf[4096];
	ssize_t nread;
	int ret = 0;

	src_fd = open(source_path, O_RDONLY);
	if (src_fd == -1)
		return -errno;

	cache_fd = open(cache_path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
	if (cache_fd == -1) {
		ret = -errno;
		close(src_fd);
		return ret;
	}

	while ((nread = read(src_fd, buf, sizeof(buf))) > 0) {
		if (write(cache_fd, buf, nread) != nread) {
			ret = -EIO;
			break;
		}
	}

	if (nread == -1)
		ret = -errno;

	close(src_fd);
	close(cache_fd);

	return ret;
}

// Handles a cache miss by atomically copying the file from the source.
// Returns 0 on success, or a negative error code.
static int handle_cache_miss(const char *path, const char *cache_path)
{
	char *source_path = get_source_path(path);
	if (!source_path)
		return -errno;

	// Create parent directories in cache if they don't exist
	int res = ensure_dirs_exist(cache_path);
	if (res != 0) {
		free(source_path);
		return res;
	}
	// Create a unique temporary file path for the copy
	// This will be a file in the cache directory, e.g. ".tmp.<pid>.<rand>"
	char *tmp_path;
	if (asprintf(&tmp_path, "%s.tmp.%d.%d", cache_path, getpid(), rand()) == -1) {
		free(source_path);
		return -ENOMEM;
	}
	// Copy file content from source to the temporary file
	res = copy_file_content(source_path, tmp_path);
	free(source_path);	// No longer need the source path
	if (res != 0) {
		unlink(tmp_path);
		free(tmp_path);
		return res;
	}
	// Atomically move the file to its final destination.
	// This will overwrite if it exists, which is fine if another thread just beat us to it.
	if (rename(tmp_path, cache_path) == -1) {
		int err = -errno;
		unlink(tmp_path);
		free(tmp_path);
		return err;
	}

	free(tmp_path);
	return 0;
}

static int fusecache_open(const char *path, struct fuse_file_info *fi)
{
	// We only support read-only operations.
	if ((fi->flags & O_ACCMODE) != O_RDONLY)
		return -EACCES;

	char *cache_path = get_cache_path(path);
	if (!cache_path)
		return -ENOMEM;

	// Try to open the file, assuming it's already in the cache.
	int fd = open(cache_path, O_RDONLY);
	if (fd == -1 && errno == ENOENT) {
		int res = handle_cache_miss(path, cache_path);
		if (res < 0) {
			free(cache_path);
			return res;
		}
		// Try again now that the file should be in the cache.
		fd = open(cache_path, O_RDONLY);
	}
	// If fd is negative at this point, something failed.
	if (fd < 0) {
		int err = -errno;
		free(cache_path);
		return err;
	}
	// Success
	free(cache_path);
	fi->fh = fd;
	return 0;
}

// Read data from an open file.
static int fusecache_read(const char *path, char *buf, size_t size, off_t offset, struct fuse_file_info *fi)
{
	(void) path;

	int res = pread(fi->fh, buf, size, offset);
	if (res == -1)
		return -errno;

	return res;
}

// Release (close) an open file.
static int fusecache_release(const char *path, struct fuse_file_info *fi)
{
	(void) path;
	close(fi->fh);
	return 0;
}

// Define the operations structure
static const struct fuse_operations fusecache_oper = {
	.getattr = fusecache_getattr,
	.readdir = fusecache_readdir,
	.open = fusecache_open,
	.read = fusecache_read,
	.release = fusecache_release,
};

// Main function: parse arguments and start the FUSE event loop.
int main(int argc, char *argv[])
{
	// struct fuse_args args = FUSE_ARGS_INIT(argc, argv);
	struct fusecache_config conf;

	srand(time(NULL));

	// We expect 3 arguments from our user:
	// fusecache <source_dir> <cache_dir> <mount_point> [fuse_options]
	// The mount point and fuse options are handled by libfuse,
	// so we just need to parse our custom ones.

	if (argc < 4) {
		fprintf(stderr, "Usage: %s <source_dir> <cache_dir> <mount_point>\n", argv[0]);
		return 1;
	}
	// Realpath is used to resolve relative paths and ".."
	conf.source_dir = realpath(argv[1], NULL);
	conf.cache_dir = realpath(argv[2], NULL);

	if (!conf.source_dir || !conf.cache_dir) {
		perror("realpath");
		free(conf.source_dir);
		free(conf.cache_dir);
		return 1;
	}
	// Adjust argc and argv for fuse_main
	argv[1] = argv[3];	// mount point
	for (int i = 2; i < argc - 2; i++) {
		argv[i] = argv[i + 2];	// shift remaining args left by 2
	}
	argc = argc - 2;

	// The last argument to fuse_main is user_data, which we can access
	// in our callbacks via fuse_get_context()->private_data.
	int ret = fuse_main(argc, argv, &fusecache_oper, &conf);

	free(conf.source_dir);
	free(conf.cache_dir);

	return ret;
}
