#!/usr/bin/env python3

""" atail: a program like tail(1), that doesn't rewind to the beginning if the file size shrinks """

import sys
import argparse
import logging
from pathlib import Path
import asyncio
import io
import os

import aiofiles
import aionotify

import ucm


logger = logging.getLogger(__name__)


class AsyncTail:
	""" AsyncTail: a class that can tail a file asynchronously """

	def __init__(self, filename="/dev/stdin", wait_for_create=False, lines=0, all_lines=False, follow=False, rewind=False):
		""" Initialize the AsyncTail object """
		self.filename = filename
		self.wait_for_create = wait_for_create
		self.lines = lines
		self.all_lines = all_lines
		self.follow = follow
		self.rewind = rewind
		logger.debug("self dict: %r", self.__dict__)

	async def run(self):
		""" Tail the file """
		if self.wait_for_create and not Path(self.filename).exists():
			await self.wait_for_file_creation()

		async with aiofiles.open(self.filename, mode='r') as f:
			# FIXME this is inefficient when using the n option on regular files
			if self.all_lines or self.lines:
				lines = await f.readlines()
				if self.lines:
					lines = lines[-self.lines:]
				for line in lines:
					yield line
			else:
				await self.seek_to_end(f)

			if self.follow:
				async for line in self.follow_changes(f):
					yield line

	async def seek_to_end(self, f):
		try:
			await f.seek(0, 2)
		except io.UnsupportedOperation:
			pass

	async def follow_changes(self, f):
		""" Follow the file """
		try:
			watcher = aionotify.Watcher()
			watcher.watch(self.filename, aionotify.Flags.MODIFY)
			await watcher.setup(asyncio.get_event_loop())
			while True:
				count = 0
				while line := await f.readline():
					yield line
					count += 1
				if self.rewind and not count:
					await self.seek_to_end(f)
				await watcher.get_event()
		finally:
			self.close_watcher(watcher)

	async def wait_for_file_creation(self):
		""" Wait for the file to be created """
		folder = str(Path(self.filename).parent)
		try:
			watcher = aionotify.Watcher()
			watcher.watch(folder, aionotify.Flags.CREATE | aionotify.Flags.MOVED_TO)
			await watcher.setup(asyncio.get_event_loop())
			while not Path(self.filename).exists():
				await watcher.get_event()
		finally:
			self.close_watcher(watcher)

	def close_watcher(self, watcher):
		try:
			watcher.close()
		except Exception as e:
			logger.warning("Exception closing watcher: %r", e)



async def atail(output=sys.stdout, filename="/dev/stdin", wait_for_create=False, lines=0, all_lines=False, follow=False, rewind=False):
	""" Tail a file - for command-line tool, and an example of usage """
	tail = AsyncTail(filename=filename, wait_for_create=wait_for_create, lines=lines, all_lines=all_lines, follow=follow, rewind=rewind).run()
	async for line in tail:
		print(line, end='', file=output)
		output.flush()


def get_opts():
	""" Get the command line options """
	parser = argparse.ArgumentParser(description="atail: a program like tail(1), that doesn't rewind if the file size shrinks", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('filename', nargs='?', default="/dev/stdin", help="the file to tail")
	parser.add_argument('-w', '--wait-for-create', action='store_true', help="wait for the file to be created")
	parser.add_argument('-n', '--lines', type=int, default=0, help="output the last N lines")
	parser.add_argument('-a', '--all-lines', action='store_true', help="output all lines")
	parser.add_argument('-f', '--follow', action='store_true', help="follow the file")
	parser.add_argument('-r', '--rewind', action='store_true', help="go to the new end if the file shrinks")
	ucm.add_logging_options(parser)
	opts = parser.parse_args()
	return opts


def main():
	""" Main function """
	opts = get_opts()
	ucm.setup_logging(opts)
	ucm.run_async(atail(filename=opts.filename, wait_for_create=opts.wait_for_create, lines=opts.lines, all_lines=opts.all_lines, follow=opts.follow, rewind=opts.rewind))


if __name__ == '__main__':
	main()
