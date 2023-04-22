#!/usr/bin/env python3

""" bb2html: a program that converts bb files to html as they change """

import sys
import argparse
import logging
from pathlib import Path

from watchfiles import Change

import ucm
import atail
import chat

logger = logging.getLogger(__name__)


class BB2HTMLOptions: # pylint: disable=too-few-public-methods
	""" the options for the BB2HTML class """
	exts = ()


class BB2HTML:
	""" convert bb files to html as they change """

	def __init__(self, opts, watch_log):
		""" Initialize the BB2HTML object """
		self.opts = opts
		self.watch_log = watch_log
		self.tail = atail.AsyncTail(filename=self.watch_log, follow=True, rewind=True).run()

	async def run(self):
		""" convert bb files to html as they change """
		logger.debug("opts: %s", self.opts)
		async for line in self.tail:
			logger.debug("line from tail: %s", line)
			bb_file, change_type, old_size, new_size = line.rstrip("\n").split("\t")
			change_type = Change(int(change_type))
			old_size = int(old_size) if old_size != "" else None
			new_size = int(new_size) if new_size != "" else None
			if not bb_file.endswith(self.opts.exts):
				continue
			html_file = str(Path(bb_file).with_suffix(".html"))
			if change_type == Change.deleted:
				Path(html_file).unlink(missing_ok=True)
				continue
			async for row in self.file_changed(bb_file, html_file, old_size, new_size):
				yield row

	async def file_changed(self, bb_file, html_file, old_size, new_size):
		""" convert a bb file to html """
		if new_size <= (old_size or 0):
			logger.warning("bb file was truncated: %s from %s to %s", bb_file, old_size, new_size)
			return

		# assume the file was appended to

		with Path(bb_file).open("r") as bb:
			if old_size:
				bb.seek(old_size)
			with Path(html_file).open("a") as html:
				for message in chat.lines_to_messages(bb):
					print(chat.message_to_html(message), file=html)
				row = [html_file]
				yield row


async def bb2html_main(opts, watch_log, out=sys.stdout):
	""" Main function """
	bb2html = BB2HTML(opts=opts, watch_log=watch_log)
	async for row in bb2html.run():
		print(*row, sep="\t", file=out)


def get_opts():
	""" Get the command line options """
	parser = argparse.ArgumentParser(description="bb2html: convert bb files to html as they change", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-w', '--watch-log', default="/dev/stdin", help="the file where changes are logged")
	parser.add_argument('-x', '--extension', nargs="*", default=("bb",), help="the file extensions to process")
	ucm.add_logging_options(parser)
	opts = parser.parse_args()
	return opts


def main():
	""" Main function """
	opts = get_opts()
	ucm.setup_logging(opts)
	exts = tuple(f".{ext}" for ext in opts.extension or ())
	opts.exts = exts
	ucm.run_async(bb2html_main(opts=opts, watch_log=opts.watch_log))


if __name__ == '__main__':
	main()
