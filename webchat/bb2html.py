#!/usr/bin/env python3-allemande

"""bb2html: a program that converts bb files to html as they change"""

import os
import sys
import argparse
import logging
from pathlib import Path
import asyncio
from collections import defaultdict
import io
import stat

from watchfiles import Change

import ucm
import atail
import bb_lib
import ally_markdown


os.umask(0o027)

PARALLEL_MAX = 20

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store locks for each file
file_locks = defaultdict(asyncio.Lock)

semaphore = asyncio.Semaphore(PARALLEL_MAX)


async def file_changed(bb_file: str, html_file: str, old_size: int | None, new_size: int | None, delay: float = 0.5):
    """convert a bb file to html"""
    async with file_locks[bb_file]:
        is_writable = os.access(bb_file, os.W_OK) and os.access(html_file, os.W_OK)
        try:
            html_add_writable = os.stat(html_file).st_mode | stat.S_IWUSR
            os.chmod(html_file, html_add_writable)
        except FileNotFoundError:
            pass

        # assume the file was appended to ...
        html_file_mode = "ab"

        # ... unless the file seems to be new or has shrunk, or is not writable ...
        if old_size is None or new_size < old_size or not is_writable:
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
                else:
                    await asyncio.sleep(delay)
                # Load whole bb file into memory from here on, up to the new_size
                # This avoids issues when new messages are appended while we are reading
                # then we receive watch events for the new messages also, so they
                # get double-processed
                # TODO: This is maybe still not working 100% yet.
                chat_lines = bb.read(new_size - bb.tell()).decode("utf-8").splitlines()
                for message in bb_lib.lines_to_messages(chat_lines):
                    html_message = (await ally_markdown.message_to_html(message, bb_file)).encode("utf-8")
                    html.write(html_message)
                    await asyncio.sleep(0)  # asyncio yield

        row = [html_file]
        return row


async def handle_completed_task(task: asyncio.Task, tasks: set, out: io.TextIOBase = sys.stdout):
    """Handle completed task by printing result or logging exception"""
    try:
        result = await task
        print(*result, sep="\t", file=out)
    except Exception as exc:
        logger.exception("Error processing task: %s", exc)
    tasks.discard(task)


def make_done_callback(tasks: set, out: io.TextIOBase = sys.stdout):
    """Create a callback for when a task is done"""
    def callback(task):
        asyncio.create_task(handle_completed_task(task, tasks, out))

    return callback


async def limited_file_changed(bb_file, html_file, old_size, new_size):
    """Handle file changes with a semaphore to limit concurrency"""
    async with semaphore:
        return await file_changed(bb_file, html_file, old_size, new_size)


async def process_change(line, opts, tasks, out):
    """Process a change line from the watch log"""
    logger.debug("line from tail: %s", line)
    line = line.rstrip("\n")
    if "\t" in line:
        bb_file, change_type, old_size, new_size = line.split("\t")
        change_type = Change(int(change_type))
        old_size = int(old_size) if old_size != "" else None
        new_size = int(new_size) if new_size != "" else None
    else:
        bb_file = line
        change_type = Change.added
        old_size = None
        new_size = os.path.getsize(bb_file)

    if not bb_file.endswith(opts.exts):
        return

    if os.path.islink(bb_file):
        return

    html_file = str(Path(bb_file).with_suffix(".html"))

    if change_type == Change.deleted or new_size is None:
        logger.debug("bb2html: bb file deleted: %r", bb_file)
        Path(html_file).unlink(missing_ok=True)
        return

    # If file is new, and html file exists, do not update
    if old_size is None and Path(html_file).exists():
        return

    # Create and store new task
    task = asyncio.create_task(limited_file_changed(bb_file, html_file, old_size, new_size))
    tasks.add(task)
    task.add_done_callback(make_done_callback(tasks, out))


async def bb2html(opts, watch_log, out=sys.stdout):
    """Main function"""
    logger.debug("opts: %s", opts)

    tasks = set()
    async with atail.AsyncTail(
        filename=watch_log, follow=opts.follow, rewind=opts.follow, restart=opts.follow, all_lines=not opts.follow
    ) as queue:
        while (line := await queue.get()) is not None:
            try:
                await process_change(line, opts, tasks, out)
            except Exception as exc:
                logger.exception("Error processing line: %s", exc)
            queue.task_done()

    # TODO, this isn't reached yet. Could handle ctrl-C and kill signals then do this.
    if tasks:
        await asyncio.gather(*tasks)


def get_opts():
    """Get the command line options"""
    parser = argparse.ArgumentParser(
        description="bb2html: convert bb files to html as they change", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-w", "--watch-log", default="/dev/stdin", help="the file where changes are logged")
    parser.add_argument("-x", "--extension", nargs="*", default=("bb",), help="the file extensions to process")
    parser.add_argument("-F", "--no-follow", dest="follow", action="store_false", help="do not follow the file, good for stdin")
    ucm.add_logging_options(parser)
    opts = parser.parse_args()
    return opts


def main():
    """Main function"""
    opts = get_opts()
    ucm.setup_logging(opts)
    logger.info("bb2html started")
    exts = tuple(f".{ext}" for ext in opts.extension or ())
    opts.exts = exts
    ucm.run_async(bb2html(opts=opts, watch_log=opts.watch_log))


if __name__ == "__main__":
    main()
