#!/usr/bin/env python3

""" Move files to a rubbish directory """

import os
import shutil

from ally import main, logs, filer


def get_rubbish_dir(first_arg):
    """ Get the rubbish directory for the given file """
    # TODO to be more general, this should start at the parent directory of the file,
    # and walk up the directory tree until it finds a mount point, the home directory, or an unwriteable directory,
    # then return the first writeable directory found
    home = os.path.expanduser("~")
    m = filer.mount_point(first_arg)
    if m == filer.mount_point(home) or m == "/":
        return os.path.join(home, ".rubbish")
    else:
        return os.path.join(m, ".rubbish")


def create_rubbish_dir(rubbish_dir):
    old_umask = os.umask(0o077)
    os.makedirs(rubbish_dir, exist_ok=True)
    os.chmod(rubbish_dir, 0o700)
    os.umask(old_umask)


def rubbish(files, copy=False):
    if not files:
        return 0

    logger = logs.get_logger(1)

    if isinstance(files, str):
        files = [files]

    rubbish_dir = os.environ.get("RUBBISH") or get_rubbish_dir(files[0])
    create_rubbish_dir(rubbish_dir)

    status = 0
    for file in files:
        basename = os.path.basename(file)
        dest = filer.generate_unique_name(rubbish_dir, basename)

        try:
            if copy:
                shutil.copy2(file, dest, follow_symlinks=False)
                logger.info(f"copied '{file}' -> '{dest}'")
            else:
                shutil.move(file, dest)
                logger.info(f"moved '{file}' -> '{dest}'")
        except Exception as e:
            logger.error(f"Error {'copying' if copy else 'moving'} {file}: {e}")
            status = 1

    return status


def setup_args(parser):
    parser.description = __doc__
    parser.add_argument("files", nargs="+", help="Files to move to rubbish")
    parser.add_argument(
	"-c",
	"--copy",
	action="store_true",
	help="Copy files to rubbish instead of moving",
    )


if __name__ == "__main__":
    main.go(rubbish, setup_args)
