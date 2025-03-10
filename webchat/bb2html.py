#!/usr/bin/env python3-allemande

""" bb2html: a program that converts bb files to html as they change """

import os
import sys
import argparse
import logging
from pathlib import Path
import asyncio
from collections import defaultdict

from watchfiles import Change

import ucm
import atail
import chat


os.umask(0o007)


logger = logging.getLogger(__name__)

# Dictionary to store locks for each file
file_locks = defaultdict(asyncio.Lock)


async def file_changed(bb_file, html_file, old_size, new_size):
    """convert a bb file to html"""
    async with file_locks[bb_file]:
        # assume the file was appended to ...
        html_file_mode = "ab"

        # ... unless the file seems to be new or has shrunk ...
        if old_size is None or new_size < old_size:
            logger.warning("bb file will be re-rendered: %s size changed from %s to %s", bb_file, old_size, new_size)
            html_file_mode = "wb"
        else:
            logger.warning("bb file was appended, we assume: %s size changed from %s to %s", bb_file, old_size, new_size)

        with open(bb_file, "rb") as bb:
            with open(html_file, html_file_mode) as html:
                # copy perms from bb_file to html_file
                bb_stat = os.fstat(bb.fileno())
                os.fchmod(html.fileno(), bb_stat.st_mode)
                html_file_size = html.tell()
                if old_size and html_file_size:
                    bb.seek(old_size)
                # Load whole bb file into memory from here on, up to the new_size
                # This avoids issues when new messages are appended while we are reading
                # then we receive watch events for the new messages also, so they
                # get double-processed
                # TODO: This is maybe still not working 100% yet.
                chat_lines = bb.read(new_size - bb.tell()).decode("utf-8").splitlines()
                for message in chat.lines_to_messages(chat_lines):
                    html_message = chat.message_to_html(message).encode("utf-8")
                    html.write(html_message)
                    await asyncio.sleep(0)  # asyncio yield

        row = [html_file]
        return row


async def handle_completed_tasks(tasks: set, out=sys.stdout):
    """Handle completed tasks"""
    for task in list(tasks):
        if not task.done():
            continue
        try:
            row = await task
            print(*row, sep="\t", file=out)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("error processing file: %s", exc)
        tasks.discard(task)


async def bb2html(opts, watch_log, out=sys.stdout):
    """Main function"""
    logger.debug("opts: %s", opts)

    tasks = set()
    async with atail.AsyncTail(filename=watch_log, follow=True, rewind=True, restart=True) as queue:
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
                if change_type == Change.deleted:
                    Path(html_file).unlink(missing_ok=True)
                    continue

                # If file is new, and html file exists, do not update
                if old_size is None and Path(html_file).exists():
                    continue

                # Create and store new task
                task = asyncio.create_task(file_changed(bb_file, html_file, old_size, new_size))
                tasks.add(task)
                task.add_done_callback(tasks.discard)

                await handle_completed_tasks(tasks, out)

            finally:
                queue.task_done()

        # Wait for any remaining tasks
        # TODO, this isn't reached yet. Could handle ctrl-C and kill signals then do this.
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


def get_opts():
    """Get the command line options"""
    parser = argparse.ArgumentParser(
        description="bb2html: convert bb files to html as they change", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-w", "--watch-log", default="/dev/stdin", help="the file where changes are logged")
    parser.add_argument("-x", "--extension", nargs="*", default=("bb",), help="the file extensions to process")
    ucm.add_logging_options(parser)
    opts = parser.parse_args()
    return opts


def main():
    """Main function"""
    opts = get_opts()
    ucm.setup_logging(opts)
    exts = tuple(f".{ext}" for ext in opts.extension or ())
    opts.exts = exts
    ucm.run_async(bb2html(opts=opts, watch_log=opts.watch_log))


if __name__ == "__main__":
    main()
