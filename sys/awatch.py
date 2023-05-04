#!/usr/bin/env python3

""" Watch files and directories for changes """

import sys
import os
import argparse
import logging
from pathlib import Path
import re

from watchfiles import awatch, Change, DefaultFilter

import ucm


logger = logging.getLogger(__name__)


class WatcherOptions: # pylint: disable=too-few-public-methods
	""" WatcherOptions: a class that holds the options for the Watcher class """
	exts = ()
	all_files = False
	hidden = False
	dirs = False
	inital_state = False
	follow = False


class Watcher:
	""" Watcher: a class that can watch files and directories for changes """
	flush = object()

	def __init__(self, paths, opts: WatcherOptions):
		""" Initialize the Watcher object """
		self.paths = [str(Path(p).resolve()) for p in paths]
		self.opts = opts
		self.default_filter = DefaultFilter()
		self.file_sizes = {}
		self.dirs = set()

	async def run(self):
		""" Watch the files and directories """

		for path in self.paths:
			async for row in self.handle_change(Change.added, path):
				if self.opts.inital_state:
					yield row

		watcher = awatch(*self.paths, watch_filter=self.watch_filter)

		async for changes in watcher:
			for change_type, path in changes:
				async for row in self.handle_change(change_type, path):
					yield row
			yield self.flush

	def watch_filter(self, change, path):
		""" Filter out files and directories that we don't want to watch """
		if not self.default_filter(change, path):
			return False
		if not self.opts.hidden and os.path.sep + "." in path:
			return False
		p = Path(path)
		is_dir = p.is_dir()
		if is_dir or path in self.dirs:
			return True
		return self.opts.all_files or path.endswith(self.opts.exts)

	async def handle_change(self, change_type, path):
		""" Handle a change to a file or directory """
		logger.debug("change_type: %r, path: %r", change_type, path)

		if re.search(r'[\n\t]', path):
			logger.warning("path contains newline or tab: %r", path)
			return

		p = Path(path)

		if change_type == Change.deleted:
			is_dir = path in self.dirs
		else:
			is_dir = p.is_dir() and (self.opts.follow or not p.is_symlink())

		size = self.file_sizes.pop(path, None)
		size_new = None
		if p.exists() and not p.is_dir():
			size_new = p.stat().st_size

		if is_dir and change_type == Change.added:
			async for row in self.added_directory(path):
				yield row
		elif is_dir and change_type == Change.deleted:
			async for row in self.deleted_directory(path):
				yield row
		elif not is_dir and not (change_type == Change.deleted and size is None):
			row = [path, int(change_type), size, size_new]
			if size_new is not None:
				self.file_sizes[path] = size_new
			yield row

	async def added_directory(self, path):
		""" Handle entries under a directory that was added """
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
		""" Handle entries under a directory that was deleted """
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
	""" Replace None with replacement """
	if x is None:
		return replacement
	return x


async def awatch_main(paths, opts: WatcherOptions, out=sys.stdout):
	""" Main function for awatch """
	w = Watcher(paths, opts)
	async for row in w.run():
		if row == Watcher.flush:
			out.flush()
			logger.info("flushed")
		else:
			print(*[null_to(x, '') for x in row], sep='\t', file=out)


def get_opts():
	""" Get the command line options """
	parser = argparse.ArgumentParser(description="awatch: watch files and directories for changes", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-p', '--paths', nargs='*', default=".", help="the files and directories to watch")
	parser.add_argument('-x', '--extension', nargs='*', help="the file extensions to watch")
	parser.add_argument('-a', '--all-files', action='store_true', help="watch all files")
	parser.add_argument('-H', '--hidden', action='store_true', help="watch hidden files")
	parser.add_argument('-D', '--dirs', action='store_true', help="report changes to directories")
	parser.add_argument('-i', '--inital-state', action='store_true', help="report the initial state of the files and directories")
	parser.add_argument('-L', '--follow', action='store_true', help="follow symlinks")
	ucm.add_logging_options(parser)
	opts = parser.parse_args()
	return opts


def main():
	""" Main function """
	opts = get_opts()
	ucm.setup_logging(opts)
	exts = tuple(f".{ext}" for ext in opts.extension or ())
	opts.exts = exts
	ucm.run_async(awatch_main(opts.paths, opts=opts, out=sys.stdout))


if __name__ == '__main__':
	main()
