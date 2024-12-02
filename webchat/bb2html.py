#!/usr/bin/env python3-allemande

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


async def file_changed(bb_file, html_file, old_size, new_size):
	""" convert a bb file to html """

	# assume the file was appended to ...
	html_file_mode = "ab"

	# ... unless the file has shrunk
	if old_size and new_size < old_size:
		logger.warning("bb file was truncated: %s from %s to %s", bb_file, old_size, new_size)
		html_file_mode = "wb"

	with open(bb_file, "rb") as bb:
		with open(html_file, html_file_mode) as html:
			html_file_size = html.tell()
			if old_size and html_file_size:
				bb.seek(old_size)
			for message in chat.lines_to_messages(bb):
				html.write(chat.message_to_html(message).encode("utf-8"))

	row = [html_file]
	return row


async def bb2html(opts, watch_log, out=sys.stdout):
	""" Main function """
	logger.debug("opts: %s", opts)

	async with atail.AsyncTail(filename=watch_log, follow=True, rewind=True) as queue:
		while (line := await queue.get()) is not None:
			try:
				logger.debug("line from tail: %s", line)
				bb_file, change_type, old_size, new_size = line.rstrip("\n").split("\t")
				change_type = Change(int(change_type))
				old_size = int(old_size) if old_size != "" else None
				new_size = int(new_size) if new_size != "" else None
				if not bb_file.endswith(opts.exts):
					continue

				html_file = str(Path(bb_file).with_suffix(".html"))
				try:
					if change_type == Change.deleted:
						Path(html_file).unlink(missing_ok=True)
						continue
					row = await file_changed(bb_file, html_file, old_size, new_size)
					print(*row, sep="\t", file=out)
				except PermissionError as exc:
					logger.error("PermissionError: %s", exc)
			finally:
				queue.task_done()


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
	ucm.run_async(bb2html(opts=opts, watch_log=opts.watch_log))


if __name__ == '__main__':
	main()
