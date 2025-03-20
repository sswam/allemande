#!/usr/bin/env python3-allemande

""" atail: a program like tail(1), using async inotify or polling to follow changes """

import sys
import argparse
import logging
from pathlib import Path
import asyncio
import io
import time

import aiofiles
import aionotify

import ucm


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AsyncTail:
    """AsyncTail: a class that can tail a file asynchronously"""

    def __init__(
        self, filename="/dev/stdin", wait_for_create=False, lines=0, all_lines=False, follow=False,
        rewind=False, rewind_string=None, restart=False, poll_interval=None
    ):
        """Initialize the AsyncTail object"""
        self.filename = filename
        self.wait_for_create = wait_for_create
        self.lines = lines
        self.all_lines = all_lines
        self.follow = follow
        self.rewind = rewind
        self.rewind_string = rewind_string
        self.restart = restart
        self.poll_interval = poll_interval
        self.running = False
        self.watcher = None
        self.queue = None
        self.task = None

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
                logger.debug("File moved, removed or shrunk: %s", self.filename)
                if not self.restart:
                    break
                self.wait_for_create = True
                if self.rewind and self.rewind_string:
                    await self.queue.put(self.rewind_string)
        finally:
            self.running = False
            self.close_watcher()
            await self.queue.put(None)

    async def run_until_removed(self):
        created = False
        if self.wait_for_create and not Path(self.filename).exists():
            logger.debug("Waiting for file to be created: %s", self.filename)
            await self.wait_for_file_creation()
            created = True

        all_lines = self.all_lines or (created and self.follow and self.rewind)

        async with aiofiles.open(self.filename, mode="r") as f:
            # Regular tail functionality
            # FIXME this is inefficient when using the n option on regular files
            # TODO use the tac code, maybe add an option not to reverse the lines and call it tail
            if all_lines or self.lines:
                logger.debug("Reading lines from file: %s", self.filename)
                lines = await f.readlines()
                if not all_lines:
                    lines = lines[-self.lines :]
                for line in lines:
                    await self.queue.put(line)
                logger.debug("Put %d lines in queue", len(lines))
            else:
                logger.debug("Seeking to end of file: %s", self.filename)
                await self.seek_to_end(f)

            if self.follow:
                await self.follow_changes(f)

    async def seek_to_end(self, f):
        try:
            await f.seek(0, 2)
        except io.UnsupportedOperation:
            pass

    async def follow_changes(self, f):
        """Follow the file, until it is removed"""
        logger.debug("Following changes to file: %s", self.filename)
        if self.poll_interval is not None:
            await self.follow_changes_poll(f)
            return

        removed_flags = aionotify.Flags.DELETE_SELF | aionotify.Flags.MOVE_SELF | aionotify.Flags.ATTRIB

        pos_previous = await f.tell()

        try:
            self.watcher = aionotify.Watcher()
            self.watcher.watch(self.filename, aionotify.Flags.MODIFY | removed_flags)
            await self.watcher.setup(asyncio.get_event_loop())
            while True:
                count = 0
                while line := await f.readline():
                    await self.queue.put(line)
                    count += 1
                logger.debug("At end of file: %s", self.filename)
                if self.rewind and not count:
                    pos_before_seek = await f.tell()
                    logger.debug("before seek_to_end")
                    await self.seek_to_end(f)
                    logger.debug("after seek_to_end")
                    pos_at_end = await f.tell()
                    logger.debug("Pos before seek: %d, pos at end: %d", pos_before_seek, pos_at_end)
                    # Check if the file has shrunk at any point
                    if min(pos_at_end, pos_before_seek) < max(pos_previous, pos_before_seek):
                        # file has shrunk, so we will start again.
                        logger.debug("File has shrunk, rewinding")
                        return
                    elif pos_at_end > pos_before_seek:
                        # Went forward due to race condition, undo that
                        logger.debug("File has grown in race condition, rewinding to previous position")
                        try:
                            await f.seek(pos_before_seek, 0)
                            pos_at_end = pos_before_seek
                        except io.UnsupportedOperation:
                            pass
                    pos_previous = pos_at_end
                event = await self.watcher.get_event()
                # XXX Why is ATTRIB a trigger that the file was removed?
                if event.flags & removed_flags and not Path(self.filename).exists():
                    logger.debug("File removed: %s", self.filename)
                    return
        finally:
            self.close_watcher()

    async def follow_changes_poll(self, f):
        """Follow the file using polling instead of inotify"""
        pos = await f.tell()
        while True:
            if not Path(self.filename).exists():
                break

            count = 0
            while line := await f.readline():
                await self.queue.put(line)
                count += 1

            if self.rewind and not count:
                await self.seek_to_end(f)
                pos2 = await f.tell()
                if pos2 < pos:
                    return
                pos = pos2
            else:
                pos = await f.tell()

            await asyncio.sleep(self.poll_interval)

    async def wait_for_file_creation(self):
        """Wait for the file to be created"""
        logger.debug("Waiting for file to be created: %s", self.filename)
        if self.poll_interval is not None:
            await self.wait_for_file_creation_poll()
            return

        folder = str(Path(self.filename).parent)
        try:
            self.watcher = aionotify.Watcher()
            self.watcher.watch(folder, aionotify.Flags.CREATE | aionotify.Flags.MOVED_TO)
            await self.watcher.setup(asyncio.get_event_loop())
            while not Path(self.filename).exists():
                await self.watcher.get_event()
        finally:
            self.close_watcher()

    async def wait_for_file_creation_poll(self):
        """Wait for the file to be created"""
        while not Path(self.filename).exists():
            await asyncio.sleep(self.poll_interval)

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
    output=sys.stdout,
    filename="/dev/stdin",
    wait_for_create=False,
    lines=0,
    all_lines=False,
    follow=False,
    rewind=False,
    rewind_string=None,
    restart=False,
    poll_interval=None,
):
    """Tail a file - for command-line tool, and an example of usage"""
    async with AsyncTail(
        filename=filename,
        wait_for_create=wait_for_create,
        lines=lines,
        all_lines=all_lines,
        follow=follow,
        rewind=rewind,
        rewind_string=rewind_string,
        restart=restart,
        poll_interval=poll_interval,
    ) as queue:
        while (line := await queue.get()) is not None:
            queue.task_done()
            print(line, end="", file=output)
            output.flush()


def get_opts():
    """Get the command line options"""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("filename", nargs="?", default="/dev/stdin", help="the file to tail")
    parser.add_argument("-w", "--wait-for-create", action="store_true", help="wait for the file to be created")
    parser.add_argument("-n", "--lines", type=int, default=0, help="output the last N lines")
    parser.add_argument("-a", "--all-lines", action="store_true", help="output all lines")
    parser.add_argument("-f", "--follow", action="store_true", help="follow the file")
    parser.add_argument("-r", "--rewind", action="store_true", help="rewind to start if file shrinks")
    parser.add_argument("-R", "--rewind-string", help="string to output on rewind")
    parser.add_argument("-s", "--restart", action="store_true", help="restart if file is removed")
    parser.add_argument("-p", "--poll", type=float, help="poll interval in seconds (instead of using inotify)")
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
            restart=opts.restart,
            poll_interval=opts.poll,
        )
    )


if __name__ == "__main__":
    main()
