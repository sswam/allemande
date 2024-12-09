#!/usr/bin/env python3-allemande

""" atail: a program like tail(1), using inotify to follow file changes """

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
logger.setLevel(logging.DEBUG)


class AsyncTail:
    """AsyncTail: a class that can tail a file asynchronously"""

    def __init__(self, filename="/dev/stdin", wait_for_create=False, lines=0, all_lines=False, follow=False, rewind=False, rewind_string=None):
        """Initialize the AsyncTail object"""
        self.filename = filename
        self.wait_for_create = wait_for_create
        self.lines = lines
        self.all_lines = all_lines
        self.follow = follow
        self.rewind = rewind
        self.rewind_string = rewind_string
        self.running = False
        self.watcher = None
        self.queue = None
        self.task = None
        logger.debug("self dict: %r", self.__dict__)

    async def __aenter__(self):
        self.queue = asyncio.Queue()
        self.task = asyncio.create_task(self._run())
        return self.queue

    async def __aexit__(self, *args):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.task = None
        self.queue = None

    async def _run(self):
        """Tail the file"""
        if self.running:
            raise RuntimeError("AsyncTail is already running")
        self.running = True
        try:
            while True:
                await self.run_until_removed()
                logger.debug("File moved or removed: %s", self.filename)
                if not (self.rewind and self.wait_for_create):
                    break
                if self.rewind_string:
                    await self.queue.put(self.rewind_string)
        finally:
            self.running = False
            self.close_watcher()

    async def run_until_removed(self):
        if self.wait_for_create and not Path(self.filename).exists():
            await self.wait_for_file_creation()

        async with aiofiles.open(self.filename, mode="r") as f:
            # Regular tail functionality
            # FIXME this is inefficient when using the n option on regular files
            if self.all_lines or self.lines:
                lines = await f.readlines()
                if self.lines:
                    lines = lines[-self.lines :]
                for line in lines:
                    await self.queue.put(line)
            else:
                await self.seek_to_end(f)

            if not self.follow:
                return

            # Follow the file, until it is removed
            await self.follow_changes(f)

    async def seek_to_end(self, f):
        try:
            await f.seek(0, 2)
        except io.UnsupportedOperation:
            pass

    async def follow_changes(self, f):
        """Follow the file, until it is removed"""
        removed_flags = aionotify.Flags.DELETE_SELF | aionotify.Flags.MOVE_SELF | aionotify.Flags.ATTRIB

        pos = await f.tell()

        try:
            self.watcher = aionotify.Watcher()
            self.watcher.watch(self.filename, aionotify.Flags.MODIFY | removed_flags)
            await self.watcher.setup(asyncio.get_event_loop())
            while True:
                count = 0
                while line := await f.readline():
                    await self.queue.put(line)
                    count += 1
                if self.rewind and not count:
                    await self.seek_to_end(f)
                    pos2 = await f.tell()
                    if pos2 < pos:
                        # file has shrunk, so we will start again.
                        return
                    pos = pos2
                else:
                    pos = await f.tell()
                event = await self.watcher.get_event()
                if event.flags & removed_flags and not Path(self.filename).exists():
                    break
        finally:
            self.close_watcher()

    async def wait_for_file_creation(self):
        """Wait for the file to be created"""
        folder = str(Path(self.filename).parent)
        try:
            self.watcher = aionotify.Watcher()
            self.watcher.watch(folder, aionotify.Flags.CREATE | aionotify.Flags.MOVED_TO)
            await self.watcher.setup(asyncio.get_event_loop())
            while not Path(self.filename).exists():
                await self.watcher.get_event()
        finally:
            self.close_watcher()

    def close_watcher(self):
        """Close the watcher"""
        if not self.watcher:
            return
        try:
            self.watcher.close()
            self.watcher = None
        except Exception as e:
            logger.warning("Exception closing watcher: %r", e)


async def atail(
    output=sys.stdout, filename="/dev/stdin", wait_for_create=False, lines=0, all_lines=False, follow=False, rewind=False, rewind_string=None
):
    """Tail a file - for command-line tool, and an example of usage"""
    async with AsyncTail(
        filename=filename, wait_for_create=wait_for_create, lines=lines, all_lines=all_lines, follow=follow, rewind=rewind, rewind_string=rewind_string
    ) as queue:
        while (line := await queue.get()) is not None:
            print(line, end="", file=output)
            output.flush()
            queue.task_done()


def get_opts():
    """Get the command line options"""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("filename", nargs="?", default="/dev/stdin", help="the file to tail")
    parser.add_argument("-w", "--wait-for-create", action="store_true", help="wait for the file to be created")
    parser.add_argument("-n", "--lines", type=int, default=0, help="output the last N lines")
    parser.add_argument("-a", "--all-lines", action="store_true", help="output all lines")
    parser.add_argument("-f", "--follow", action="store_true", help="follow the file")
    parser.add_argument("-r", "--rewind", action="store_true", help="rewind to start if file shrinks or is recreated")
    parser.add_argument("-R", "--rewind-string", help="string to output on rewind")
    ucm.add_logging_options(parser)
    opts = parser.parse_args()
    return opts


def main():
    """Main function"""
    opts = get_opts()
    ucm.setup_logging(opts)
    ucm.run_async(
        atail(
            filename=opts.filename,
            wait_for_create=opts.wait_for_create,
            lines=opts.lines,
            all_lines=opts.all_lines,
            follow=opts.follow,
            rewind=opts.rewind,
            rewind_string=opts.rewind_string,
        )
    )


if __name__ == "__main__":
    main()
