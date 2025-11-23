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
#include <time.h>
#include <sys/xattr.h>
#include <sys/file.h>
#include <poll.h>

/*
* This struct will hold the configuration for our filesystem.
* We'll pass a pointer to this in the private_data field of fuse_context.
*/
struct fusenull_config {
   char *root_dir;
};

// Helper to get the full path in the root directory.
// The caller is responsible for freeing the returned string.
static char *get_root_path(const char *path)
{
   struct fusenull_config *conf = (struct fusenull_config *) fuse_get_context()->private_data;
   char *full_path;

   if (asprintf(&full_path, "%s%s", conf->root_dir, path) == -1) {
      return NULL;
   }

   return full_path;
}

// Filesystem operations

// Update signatures to match FUSE3 fuse_operations struct
static int fuse_getattr(const char *path, struct stat *stbuf, struct fuse_file_info *fi)
{
   (void) fi;
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int res = lstat(root_path, stbuf);
   free(root_path);

   if (res == -1)
      return -errno;

   return 0;
}

static int fuse_readlink(const char *path, char *buf, size_t size)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int res = readlink(root_path, buf, size - 1);
   free(root_path);

   if (res == -1)
      return -errno;

   buf[res] = '\0';
   return 0;
}

static int fuse_mknod(const char *path, mode_t mode, dev_t rdev)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int res;
   if (S_ISFIFO(mode))
      res = mkfifo(root_path, mode);
   else
      res = mknod(root_path, mode, rdev);
   free(root_path);

   if (res == -1)
      return -errno;

   return 0;
}

static int fuse_mkdir(const char *path, mode_t mode)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int res = mkdir(root_path, mode);
   free(root_path);

   if (res == -1)
      return -errno;

   return 0;
}

static int fuse_unlink(const char *path)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int res = unlink(root_path);
   free(root_path);

   if (res == -1)
      return -errno;

   return 0;
}

static int fuse_rmdir(const char *path)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int res = rmdir(root_path);
   free(root_path);

   if (res == -1)
      return -errno;

   return 0;
}

static int fuse_symlink(const char *from, const char *to)
{
   char *root_from = get_root_path(from);
   char *root_to = get_root_path(to);
   if (!root_from || !root_to) {
      free(root_from);
      free(root_to);
      return -ENOMEM;
   }

   int res = symlink(root_to, root_from);
   free(root_from);
   free(root_to);

   if (res == -1)
      return -errno;

   return 0;
}

// Update signatures to match FUSE3 fuse_operations struct
static int fuse_rename(const char *from, const char *to, unsigned int flags)
{
   (void) flags;
   char *root_from = get_root_path(from);
   char *root_to = get_root_path(to);
   if (!root_from || !root_to) {
      free(root_from);
      free(root_to);
      return -ENOMEM;
   }

   int res = rename(root_from, root_to);
   free(root_from);
   free(root_to);

   if (res == -1)
      return -errno;

   return 0;
}

static int fuse_link(const char *from, const char *to)
{
   char *root_from = get_root_path(from);
   char *root_to = get_root_path(to);
   if (!root_from || !root_to) {
      free(root_from);
      free(root_to);
      return -ENOMEM;
   }

   int res = link(root_from, root_to);
   free(root_from);
   free(root_to);

   if (res == -1)
      return -errno;

   return 0;
}

// Update signatures to match FUSE3 fuse_operations struct
static int fuse_chmod(const char *path, mode_t mode, struct fuse_file_info *fi)
{
   (void) fi;
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int res = chmod(root_path, mode);
   free(root_path);

   if (res == -1)
      return -errno;

   return 0;
}

// Update signatures to match FUSE3 fuse_operations struct
static int fuse_chown(const char *path, uid_t uid, gid_t gid, struct fuse_file_info *fi)
{
   (void) fi;
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int res = chown(root_path, uid, gid);
   free(root_path);

   if (res == -1)
      return -errno;

   return 0;
}

// Update signatures to match FUSE3 fuse_operations struct
static int fuse_truncate(const char *path, off_t size, struct fuse_file_info *fi)
{
   (void) fi;
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int res = truncate(root_path, size);
   free(root_path);

   if (res == -1)
      return -errno;

   return 0;
}

static int fuse_access(const char *path, int mask)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int res = access(root_path, mask);
   free(root_path);

   if (res == -1)
      return -errno;

   return 0;
}

// Update signatures to match FUSE3 fuse_operations struct
static int fuse_readdir(const char *path, void *buf, fuse_fill_dir_t filler, off_t offset, struct fuse_file_info *fi, enum fuse_readdir_flags flags)
{
   (void) offset;
   (void) fi;
   (void) flags;

   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   DIR *dp = opendir(root_path);
   if (dp == NULL) {
      int err = -errno;
      free(root_path);
      return err;
   }

   struct dirent *de;
   while ((de = readdir(dp)) != NULL) {
      struct stat st;
      memset(&st, 0, sizeof(st));
      st.st_ino = de->d_ino;
      st.st_mode = de->d_type << 12;
      if (filler(buf, de->d_name, &st, 0, 0))
         break;
   }

   closedir(dp);
   free(root_path);
   return 0;
}

static int fuse_create(const char *path, mode_t mode, struct fuse_file_info *fi)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int fd = open(root_path, fi->flags | O_CREAT | O_TRUNC, mode);
   free(root_path);

   if (fd == -1)
      return -errno;

   fi->fh = fd;
   return 0;
}

static int fuse_open(const char *path, struct fuse_file_info *fi)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int fd = open(root_path, fi->flags);
   free(root_path);

   if (fd == -1)
      return -errno;

   fi->fh = fd;
   return 0;
}

static int fuse_read(const char *path, char *buf, size_t size, off_t offset, struct fuse_file_info *fi)
{
   (void) path;

   int res = pread(fi->fh, buf, size, offset);
   if (res == -1)
      res = -errno;

   return res;
}

static int fuse_write(const char *path, const char *buf, size_t size, off_t offset, struct fuse_file_info *fi)
{
   (void) path;

   int res = pwrite(fi->fh, buf, size, offset);
   if (res == -1)
      res = -errno;

   return res;
}

static int fuse_release(const char *path, struct fuse_file_info *fi)
{
   (void) path;
   close(fi->fh);
   return 0;
}

static int fuse_fsync(const char *path, int isdatasync, struct fuse_file_info *fi)
{
   (void) path;
   int res = isdatasync ? fdatasync(fi->fh) : fsync(fi->fh);
   if (res == -1)
      return -errno;

   return 0;
}

static int fuse_opendir(const char *path, struct fuse_file_info *fi)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   DIR *dp = opendir(root_path);
   free(root_path);

   if (dp == NULL)
      return -errno;

   fi->fh = (uintptr_t) dp;
   return 0;
}

static int fuse_releasedir(const char *path, struct fuse_file_info *fi)
{
   (void) path;
   closedir((DIR *) fi->fh);
   return 0;
}

static int fuse_fsyncdir(const char *path, int isdatasync, struct fuse_file_info *fi)
{
   (void) path;
   (void) isdatasync;
   (void) fi;
   // FUSE doesn't have direct fsync for dirs; assume success
   return 0;
}

static int fuse_statfs(const char *path, struct statvfs *stbuf)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int res = statvfs(root_path, stbuf);
   free(root_path);

   if (res == -1)
      return -errno;

   return 0;
}

static int fuse_setxattr(const char *path, const char *name, const char *value, size_t size, int flags)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int res = setxattr(root_path, name, value, size, flags);
   free(root_path);

   if (res == -1)
      return -errno;

   return 0;
}

static int fuse_getxattr(const char *path, const char *name, char *value, size_t size)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   ssize_t res = getxattr(root_path, name, value, size);
   free(root_path);

   if (res == -1)
      return -errno;

   return res;
}

static int fuse_listxattr(const char *path, char *list, size_t size)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   ssize_t res = listxattr(root_path, list, size);
   free(root_path);

   if (res == -1)
      return -errno;

   return res;
}

static int fuse_removexattr(const char *path, const char *name)
{
   char *root_path = get_root_path(path);
   if (!root_path)
      return -ENOMEM;

   int res = removexattr(root_path, name);
   free(root_path);

   if (res == -1)
      return -errno;

   return 0;
}

// Remove fuse_getlk and fuse_setlk, replace with fuse_lock for FUSE3 .lock
static int fuse_lock(const char *path, struct fuse_file_info *fi, int cmd, struct flock *lock)
{
   (void) path;
   int res;
   if (cmd == F_GETLK) {
      res = fcntl(fi->fh, F_GETLK, lock);
   } else if (cmd == F_SETLK || cmd == F_SETLKW) {
      res = fcntl(fi->fh, cmd, lock);
   } else {
      return -EINVAL;
   }
   if (res == -1)
      return -errno;
   return 0;
}

static int fuse_flock(const char *path, struct fuse_file_info *fi, int op)
{
   (void) path;

   int res = flock(fi->fh, op);
   if (res == -1)
      return -errno;

   return 0;
}

static int fuse_fallocate(const char *path, int mode, off_t offset, off_t length, struct fuse_file_info *fi)
{
   (void) path;

   int res = fallocate(fi->fh, mode, offset, length);
   if (res == -1)
      return -errno;

   return 0;
}

static ssize_t fuse_copy_file_range(const char *path_in, struct fuse_file_info *fi_in, off_t offset_in, const char *path_out, struct fuse_file_info *fi_out, off_t offset_out, size_t len, int flags)
{
   (void) path_in;
   (void) path_out;

   ssize_t res = copy_file_range(fi_in->fh, &offset_in, fi_out->fh, &offset_out, len, flags);
   if (res == -1)
      return -errno;

   return res;
}

static off_t fuse_lseek(const char *path, off_t off, int whence, struct fuse_file_info *fi)
{
   (void) path;

   off_t res = lseek(fi->fh, off, whence);
   if (res == -1)
      return -errno;

   return res;
}

// Placeholder for unsupported operations
static int fuse_bmap(const char *path, size_t blocksize, uint64_t *idx)
{
   (void) path;
   (void) blocksize;
   (void) idx;
   return -ENOSYS;
}

static int fuse_ioctl(const char *path, int cmd, void *arg, struct fuse_file_info *fi, unsigned int flags, void *data)
{
   (void) path;
   (void) cmd;
   (void) arg;
   (void) fi;
   (void) flags;
   (void) data;
   return -ENOSYS;
}

static int fuse_poll(const char *path, struct fuse_file_info *fi, struct fuse_pollhandle *ph, unsigned *reventsp)
{
   (void) path;
   (void) fi;
   (void) ph;
   (void) reventsp;
   return -ENOSYS;
}

static int fuse_write_buf(const char *path, struct fuse_bufvec *buf, off_t off, struct fuse_file_info *fi)
{
   (void) path;
   (void) buf;
   (void) off;
   (void) fi;
   return -ENOSYS;
}

// Update fuse_oper struct to match FUSE3: add fi to relevant ops, add flags to rename and readdir, use .lock instead of .getlk/.setlk, remove .setattr, copy_file_range returns ssize_t
static const struct fuse_operations fuse_oper = {
   .getattr = fuse_getattr,
   .readlink = fuse_readlink,
   .mknod = fuse_mknod,
   .mkdir = fuse_mkdir,
   .unlink = fuse_unlink,
   .rmdir = fuse_rmdir,
   .symlink = fuse_symlink,
   .rename = fuse_rename,
   .link = fuse_link,
   .chmod = fuse_chmod,
   .chown = fuse_chown,
   .truncate = fuse_truncate,
   .access = fuse_access,
   .readdir = fuse_readdir,
   .create = fuse_create,
   .open = fuse_open,
   .read = fuse_read,
   .write = fuse_write,
   .release = fuse_release,
   .fsync = fuse_fsync,
   .opendir = fuse_opendir,
   .releasedir = fuse_releasedir,
   .fsyncdir = fuse_fsyncdir,
   .statfs = fuse_statfs,
   .setxattr = fuse_setxattr,
   .getxattr = fuse_getxattr,
   .listxattr = fuse_listxattr,
   .removexattr = fuse_removexattr,
   .lock = fuse_lock,
   .flock = fuse_flock,
   .fallocate = fuse_fallocate,
   .copy_file_range = fuse_copy_file_range,
   .lseek = fuse_lseek,
   .bmap = fuse_bmap,
   .ioctl = fuse_ioctl,
   .poll = fuse_poll,
   .write_buf = fuse_write_buf,
};

// Main function: parse arguments and start the FUSE event loop.
int main(int argc, char *argv[])
{
   struct fusenull_config conf;

   srand(time(NULL));

   if (argc < 3) {
      fprintf(stderr, "Usage: %s <root_dir> <mount_point> [fuse_options...]\n", argv[0]);
      return 1;
   }

   conf.root_dir = realpath(argv[1], NULL);
   if (!conf.root_dir) {
      perror("realpath failed for root_dir");
      return 1;
   }

   int fuse_argc = argc - 1;
   char **fuse_argv = malloc(fuse_argc * sizeof(char *));
   if (fuse_argv == NULL) {
      perror("malloc for fuse_argv failed");
      free(conf.root_dir);
      return 1;
   }

   fuse_argv[0] = argv[0];
   fuse_argv[1] = argv[2];
   for (int i = 3; i < argc; i++) {
      fuse_argv[i - 1] = argv[i];
   }

   int ret = fuse_main(fuse_argc, fuse_argv, &fuse_oper, &conf);

   free(fuse_argv);
   free(conf.root_dir);

   return ret;
}
