#!/usr/bin/env ccx
// CFLAGS: -Wall -D_FILE_OFFSET_BITS=64
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

/*
 * This struct will hold the configuration for our filesystem.
 * We'll pass a pointer to this in the private_data field of fuse_context.
 */
struct fusecache_config {
	char *source_dir;
	char *cache_dir;
};

// Helper to get the full path in the source directory.
// The caller is responsible for freeing the returned string.
static char* get_source_path(const char* path)
{
    struct fusecache_config *conf = (struct fusecache_config *) fuse_get_context()->private_data;
    char *source_path = NULL;

    // asprintf is a GNU extension, requires _GNU_SOURCE
    int res = asprintf(&source_path, "%s%s", conf->source_dir, path);
    if (res == -1) {
        return NULL;
    }
    return source_path;
}

static int fusecache_getattr(const char *path, struct stat *stbuf, struct fuse_file_info *fi)
{
    (void) fi;
    char *source_path = get_source_path(path);
    if (!source_path) {
        return -ENOMEM;
    }

    int res = lstat(source_path, stbuf);
    free(source_path);

    if (res == -1) {
        return -errno;
    }

    return 0;
}

static int fusecache_readdir(const char *path, void *buf, fuse_fill_dir_t filler, off_t offset, struct fuse_file_info *fi, enum fuse_readdir_flags flags)
{
    (void) offset;
    (void) fi;
    (void) flags;

    char *source_path = get_source_path(path);
    if (!source_path) {
        return -ENOMEM;
    }

    DIR *dp = opendir(source_path);
    if (dp == NULL) {
        int err = -errno;
        free(source_path);
        return err;
    }

    struct dirent *de;
    while ((de = readdir(dp)) != NULL) {
        filler(buf, de->d_name, NULL, 0, 0);
    }

    closedir(dp);
    free(source_path);
    return 0;
}

// Helper to get the full path in the cache directory.
// The caller is responsible for freeing the returned string.
static char* get_cache_path(const char* path)
{
    struct fusecache_config *conf = (struct fusecache_config *) fuse_get_context()->private_data;
    char *cache_path = NULL;
    int res = asprintf(&cache_path, "%s%s", conf->cache_dir, path);
    if (res == -1) {
        return NULL;
    }
    return cache_path;
}

// Creates parent directories for a given file path, like "mkdir -p".
static int ensure_dirs_exist(const char *path)
{
    char *p, *dir_path;
    dir_path = strdup(path);
    if (!dir_path) {
        return -ENOMEM;
    }

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
    if (src_fd == -1) {
        return -errno;
    }

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

    if (nread == -1) {
        ret = -errno;
    }

    close(src_fd);
    close(cache_fd);

    return ret;
}

// Handles a cache miss by copying the file from the source and opening it.
static int handle_cache_miss(const char *path, const char *cache_path)
{
    char *source_path = get_source_path(path);
    if (!source_path) {
        return -ENOMEM;
    }

    // Create parent directories in cache if they don't exist
    int res = ensure_dirs_exist(cache_path);
    if (res != 0) {
        free(source_path);
        return res;
    }

    // Copy file content from source to cache
    res = copy_file_content(source_path, cache_path);
    free(source_path); // No longer need the source path
    if (res != 0) {
        return res;
    }

    // Now that it's cached, open it.
    int fd = open(cache_path, O_RDONLY);
    if (fd == -1) {
        return -errno; // Return the specific error from the final open attempt
    }

    return fd;
}

static int fusecache_open(const char *path, struct fuse_file_info *fi)
{
    // Error case first: We only support read-only operations.
    if ((fi->flags & O_ACCMODE) != O_RDONLY) {
        return -EACCES;
    }

    char *cache_path = get_cache_path(path);
    if (!cache_path) {
        return -ENOMEM;
    }

    // Try to open the file, assuming it's already in the cache.
    int fd = open(cache_path, O_RDONLY);
    if (fd == -1 && errno == ENOENT)
        fd = handle_cache_miss(path, cache_path);
    else if (fd == -1)
        fd = -errno;

    // Centralized error check: If fd is negative at this point, something failed.
    if (fd < 0) {
        free(cache_path);
        return fd; // fd already holds the negative error code
    }

    // Success path
    free(cache_path);
    fi->fh = fd;
    return 0;
}

static int fusecache_read(const char *path, char *buf, size_t size, off_t offset, struct fuse_file_info *fi)
{
    (void) path;

    int res = pread(fi->fh, buf, size, offset);
    if (res == -1) {
        return -errno;
    }

    return res;
}

static int fusecache_release(const char *path, struct fuse_file_info *fi)
{
    (void) path;
    close(fi->fh);
    return 0;
}

static const struct fuse_operations fusecache_oper = {
	.getattr = fusecache_getattr,
	.readdir = fusecache_readdir,
	.open	= fusecache_open,
	.read	= fusecache_read,
	.release = fusecache_release,
};

int main(int argc, char *argv[])
{
	struct fuse_args args = FUSE_ARGS_INIT(argc, argv);
	struct fusecache_config conf;

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
	argv[1] = argv[3]; // mount point
	for (int i = 2; i < argc-2; i++) {
		argv[i] = argv[i+2]; // shift remaining args left by 2
	}
	argc = argc - 2;

	// The last argument to fuse_main is user_data, which we can access
	// in our callbacks via fuse_get_context()->private_data.
	int ret = fuse_main(argc, argv, &fusecache_oper, &conf);

	free(conf.source_dir);
	free(conf.cache_dir);

	return ret;
}
