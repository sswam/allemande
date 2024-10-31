#!/usr/bin/env python3

""" Watch files and directories for changes """

import sys
import os
import argparse
import logging
from pathlib import Path
import re
from types import SimpleNamespace
from pydantic import BaseModel

from watchfiles import awatch, Change, DefaultFilter
from hidden import contains_hidden_component

from ally import main, logs


logger = logs.get_logger()


class WatcherOptions(BaseModel):
    """WatcherOptions: a class that holds the options for the Watcher class"""
    exts: list[str] = []
    extension: list[str] = []
    all_files: bool = False
    hidden: bool = False
    dirs: bool = False
    initial_state: bool = False
    follow: bool = False
    recursive: bool = False
    absolute: bool = False


class Watcher:
    """Watcher: a class that can watch files and directories for changes"""
    flush = object()

    def __init__(self, paths, opts: WatcherOptions):
        """Initialize the Watcher object"""
        self.opts = opts
        self.paths = [self.resolve_path(p) for p in paths]
        self.default_filter = DefaultFilter()
        self.file_sizes: dict[str, int] = {}
        self.dirs: set[str] = set()
        self.cwd = os.getcwd() + os.path.sep

        logger.debug("opts: %r", opts)

    def resolve_path(self, path):
        """A path given with a trailing / means to follow any symlink"""
        if self.opts.follow or path.endswith("/"):
            return str(Path(path).resolve())
        if self.opts.absolute:
            return str(Path(path).absolute())
        return path

    async def run(self):
        """Watch the files and directories"""

        if self.opts.initial_state:
            for path in self.paths:
                async for row in self.handle_change(Change.added, path, initial=True):
                    yield row
            yield self.flush

        watcher = awatch(*self.paths, watch_filter=self.watch_filter, recursive=self.opts.recursive)

        async for changes in watcher:
            for change_type, path in changes:
                if not self.opts.absolute and path.startswith(self.cwd):
                    path = path[len(self.cwd) :]
                if not self.opts.absolute and path.startswith("." + os.path.sep):
                    path = path[len("." + os.path.sep) :]
                async for row in self.handle_change(change_type, path):
                    yield row
            yield self.flush

    def watch_filter(self, change_type, path):
        """Filter out files and directories that we don't want to watch"""
        if not self.default_filter(change_type, path):
            return False
        if not self.opts.hidden and contains_hidden_component(path):
            return False
        p = Path(path)
        is_dir = p.is_dir()
        if is_dir or path in self.dirs:
            return True
        return self.opts.all_files or path.endswith(self.opts.exts)

    async def handle_change(self, change_type, path, initial=False):
        """Handle a change to a file or directory"""
        logger.debug("change_type: %r, path: %r", change_type, path)

        if re.search(r"[\n\t]", path):
            logger.warning("path contains newline or tab, skipping: %r", path)
            return

        if not self.watch_filter(change_type, path):
            return

        p = Path(path)

        # Is it a directory?

        if change_type == Change.deleted:
            is_dir = path in self.dirs
        else:
            is_dir = p.is_dir() and (self.opts.follow or not p.is_symlink())

        # Get size for files or symlinks (if not following), but not dirs.

        size = self.file_sizes.pop(path, None)
        size_new = None

        is_file = p.exists() and not is_dir
        if is_file and self.opts.follow:
            size_new = p.stat().st_size
        elif is_file:
            size_new = p.lstat().st_size

        if is_dir and change_type == Change.added and (self.opts.recursive or initial):
            async for row in self.added_directory(path):
                yield row
        elif is_dir and change_type == Change.deleted and self.opts.recursive:
            async for row in self.deleted_directory(path):
                yield row
        elif not is_dir and not (change_type == Change.deleted and size is None):
            row = [path, int(change_type), size, size_new]
            if size_new is not None:
                self.file_sizes[path] = size_new
            yield row

    async def added_directory(self, path):
        """Handle entries under a directory that was added"""
        self.dirs.add(path)
        if self.opts.dirs:
            row = [path + os.path.sep, int(Change.added), None, None]
            yield row
        p = Path(path)
        for e in p.iterdir():
            logger.debug("e: %r", e)
            async for row in self.handle_change(Change.added, str(e)):
                yield row

    async def deleted_directory(self, path):
        """Handle entries under a directory that was deleted"""
        logger.debug("deleted_directory path: %r", path)
        path_slash = path + os.path.sep
        for e in list(self.file_sizes):
            if e.startswith(path_slash):
                async for row in self.handle_change(Change.deleted, e):
                    yield row
        for e in list(self.dirs):
            if e.startswith(path_slash):
                async for row in self.handle_change(Change.deleted, e):
                    yield row
        self.dirs.remove(path)
        if self.opts.dirs:
            row = [path + os.path.sep, int(Change.deleted), None, None]
            yield row


def null_to(x, replacement):
    """Replace None with replacement"""
    if x is None:
        return replacement
    return x


async def awatch_main(paths, opts: WatcherOptions, out=sys.stdout):
    """Main function for awatch"""
    opts.exts = tuple(f".{ext}" for ext in opts.extension or ())
    w = Watcher(paths, opts)
    async for row in w.run():
        if row == Watcher.flush:
            out.flush()
            logger.info("flushed")
        else:
            print(*[null_to(x, "") for x in row], sep="\t", file=out)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-p", "--paths", nargs="*", default=".", help="files and directories to watch")
    arg("-r", "--recursive", help="watch recursively under the folders", action="store_true")
    arg("-x", "--extension", nargs="*", help="file extensions to watch")
    arg("-a", "--all-files", help="watch all files", action="store_true")
    arg("-H", "--hidden", help="watch hidden files", action="store_true")
    arg("-D", "--dirs", help="report changes to directories", action="store_true")
    arg("-i", "--initial-state", help="report initial state", action="store_true")
    arg("-L", "--follow", help="follow symlinks", action="store_true")
    arg("-A", "--absolute", help="return absolute paths", action="store_true")


if __name__ == "__main__":
    main.go(awatch_main, setup_args)
