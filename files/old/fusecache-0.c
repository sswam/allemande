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

/*
 * This struct will hold the configuration for our filesystem.
 * We'll pass a pointer to this in the private_data field of fuse_context.
 */
struct fusecache_config {
	char *source_dir;
	char *cache_dir;
};

// We'll implement these functions soon.
static int fusecache_getattr(const char *path, struct stat *stbuf, struct fuse_file_info *fi)
{
    (void) fi; // Unused.

    memset(stbuf, 0, sizeof(struct stat));

    if (strcmp(path, "/") == 0) {
        stbuf->st_mode = S_IFDIR | 0755;
        stbuf->st_nlink = 2; // . and ..
        return 0;
    }

    return -ENOENT;
}

static int fusecache_readdir(const char *path, void *buf, fuse_fill_dir_t filler, off_t offset, struct fuse_file_info *fi, enum fuse_readdir_flags flags)
{
    (void) offset; // Unused.
    (void) fi;     // Unused.
    (void) flags;  // Unused.

    if (strcmp(path, "/") != 0) {
        return -ENOENT;
    }

    filler(buf, ".", NULL, 0, 0);
    filler(buf, "..", NULL, 0, 0);

    return 0;
}

static int fusecache_open(const char *path, struct fuse_file_info *fi)
{
    // Our empty filesystem has no files to open.
    return -ENOENT;
}

static int fusecache_read(const char *path, char *buf, size_t size, off_t offset, struct fuse_file_info *fi)
{
    // Should not be called since open() will fail.
    (void) path;
    (void) buf;
    (void) size;
    (void) offset;
    (void) fi;
    return -EIO;
}

static int fusecache_release(const char *path, struct fuse_file_info *fi)
{
    // Should not be called since open() will fail.
    (void) path;
    (void) fi;
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
