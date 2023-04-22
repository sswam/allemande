#!/usr/bin/env python3
""" atail: a program like tail(1), that doesn't rewind if the file size shrinks """

import sys
import argparse
import logging
from pathlib import Path
import asyncio

import aiofiles
import aionotify

import ucm

logger = logging.getLogger(__name__)

class AsyncTail:
	""" AsyncTail: a class that can tail a file asynchronously """

	def __init__(self, file_path="/dev/stdin", wait_for_create=False, n=0, all_lines=False, follow=False):
		""" Initialize the AsyncTail object """
		self.file_path = file_path
		self.wait_for_create = wait_for_create
		self.n = n
		self.all_lines = all_lines
		self.follow = follow

		logger.debug("self dict: %r", self.__dict__)

	async def tail(self):
		""" Tail the file """
		if self.wait_for_create and not Path(self.file_path).exists():
			await self.wait_for_file_creation()

		async with aiofiles.open(self.file_path, mode='r') as f:
			# TODO this is inefficient when using the n option on regular files
			if self.all_lines or self.n:
				lines = await f.readlines()
				if self.n:
					lines = lines[-self.n:]
				for line in lines:
					yield line
			else:
				# seek to the end of the file
				await f.seek(0, 2)

			if self.follow:
				async for line in self.follow_changes(f):
					yield line

	async def follow_changes(self, f):
		""" Follow the file """
		watcher = aionotify.Watcher()
		watcher.watch(self.file_path, aionotify.Flags.MODIFY)
		await watcher.setup(asyncio.get_event_loop())
		while True:
			while line := await f.readline():
				yield line
			await watcher.get_event()
		watcher.close()

	async def wait_for_file_creation(self):
		""" Wait for the file to be created """
		folder = str(Path(self.file_path).parent)
		watcher = aionotify.Watcher()
		watcher.watch(folder, aionotify.Flags.CREATE | aionotify.Flags.MOVED_TO)
		await watcher.setup(asyncio.get_event_loop())
		while not Path(self.file_path).exists():
			await watcher.get_event()
		watcher.close()

async def atail(filename="/dev/stdin", wait_for_create=False, n=0, all_lines=False, follow=False, output=sys.stdout):
	""" Tail a file - for command-line tool, and an example of usage """
	tailer = AsyncTail(filename, wait_for_create=wait_for_create, n=n, all_lines=all_lines, follow=follow)
	async for line in tailer.tail():
		print(line, end='', file=output)

def get_opts():
	""" Get the command line options """
	parser = argparse.ArgumentParser(description="atail: a program like tail(1), that doesn't rewind if the file size shrinks", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('filename', nargs='?', default="/dev/stdin", help="the file to tail")
	parser.add_argument('-w', '--wait-for-create', action='store_true', help="wait for the file to be created")
	parser.add_argument('-n', '--lines', type=int, default=0, help="output the last N lines")
	parser.add_argument('-a', '--all-lines', action='store_true', help="output all lines")
	parser.add_argument('-f', '--follow', action='store_true', help="follow the file")
	ucm.add_logging_options(parser)
	opts = parser.parse_args()
	return opts

def main():
	""" Main function """
	opts = get_opts()
	ucm.setup_logging(opts)
	asyncio.run(atail(opts.filename, wait_for_create=opts.wait_for_create, n=opts.lines, all_lines=opts.all_lines, follow=opts.follow))

if __name__ == '__main__':
	main()
