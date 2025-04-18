#!/usr/bin/env python3-allemande

""" atail: a program like tail(1), using async inotify or polling to follow changes """

# issues - does not work for reading stdin or presumably a pipe, as it does blocking reads currently

import sys
import argparse
import logging
from pathlib import Path
import asyncio
import io
from typing import Any, TextIO

import aiofiles
import aiofiles.base
import aionotify  # type: ignore[import-untyped]
from aiofiles.threadpool.text import AsyncTextIOWrapper

import ucm  # type: ignore[import-untyped]

__version__ = "0.2.5"


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AsyncTail:  # pylint: disable=too-many-instance-attributes
    """
    AsyncTail: a class that can tail a file asynchronously.

    Handles reading initial lines, following changes using inotify or polling,
    waiting for file creation, restarting on removal, and rewinding on truncation.

    Attributes:
        filename: Path to the file to tail.
        wait_for_create: Whether to wait if file doesn't exist initially.
        lines: Number of lines to show from the end (0 means read from seek pos).
        all_lines: Output all lines from the start (overrides lines).
        follow: Keep watching the file for changes.
        rewind: Restart reading from the beginning if the file shrinks.
        rewind_string: Optional string to output when a rewind occurs.
        restart: Re-open the file if it gets removed/renamed and then reappears.
        poll_interval: Use polling instead of inotify, with this interval (seconds).
        running: Flag indicating if the main loop is active.
        watcher: The aionotify watcher instance (if used).
        queue: The asyncio queue for outputting lines.
        task: The main asyncio task running the tail operation.
    """

    DEFAULT_FILENAME: str = "/dev/stdin"
    EOF_MARKER: Any = None
    REMOVED_FLAGS: int = aionotify.Flags.DELETE_SELF | aionotify.Flags.MOVE_SELF | aionotify.Flags.ATTRIB
    # IDK why ATTRIB is often the only signal for removal, but it is

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        filename: str = DEFAULT_FILENAME,
        wait_for_create: bool = False,
        lines: int = 0,
        all_lines: bool = False,
        follow: bool = False,
        rewind: bool = False,
        rewind_string: str | None = None,
        restart: bool = False,
        poll_interval: float | None = None,
    ) -> None:
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
        self.watcher: aionotify.Watcher | None = None
        self.queue: asyncio.Queue[str | None] | None = None
        self.task: asyncio.Task[None] | None = None

    async def __aenter__(self) -> asyncio.Queue[str | None]:
        """Enter async context, start the tailing task and return the queue."""
        if self.queue is not None or self.task is not None:
            raise RuntimeError("AsyncTail context already entered")
        self.queue = asyncio.Queue()
        self.task = asyncio.create_task(self.tail_loop())
        return self.queue

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context, cancel the task and clean up."""
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.task = None
        self.close_watcher()

    async def tail_loop(self) -> None:
        """
        Main loop: Opens the file, tails it until removed/shrunk,
        and potentially restarts based on configuration.
        """
        if self.running:
            raise RuntimeError("AsyncTail is already running")
        self.running = True
        try:
            if not self.wait_for_create and not Path(self.filename).exists():
                raise FileNotFoundError(f"File not found and wait_for_create=False: {self.filename}")

            while True:
                okay = await self.tail_once()
                if not okay:
                    break
        finally:
            self.running = False
            self.close_watcher()
            assert self.queue is not None
            await self.queue.put(self.EOF_MARKER)

    async def tail_once(self) -> bool:
        """
        Tails the file once: waits for creation if needed,
        opens the file, reads lines, and follows changes.
        Handles file removal/move/shrink events.
        Returns True if the session should continue (restart), False if it should end.
        """
        try:
            await self.tail_while_growing()
            logger.debug("File session ended (moved, removed, or shrunk): %s", self.filename)
        except FileNotFoundError:
            # This should now primarily catch errors *during* tailing or if wait_for_create fails
            logger.warning("File not found during tailing session: %s", self.filename)
        except PermissionError:
            logger.error("Permission denied while tailing: %s", self.filename)
            return False
        except Exception as e:  # pylint: disable=broad-exception-caught
            # try to restart on error after a short sleep, if enabled
            logger.error("Unexpected error in AsyncTail: %s", e, exc_info=True)
            if self.restart:
                await asyncio.sleep(0.5)

        # If we got here due to an error or a planned stop (shrink/remove), check if we should restart
        if not self.restart:
            logger.debug("Restart not configured, exiting main loop.")
            return False

        # Prepare for restart
        self.wait_for_create = True  # Wait for it to appear again
        if self.rewind and self.rewind_string is not None:
            assert self.queue is not None
            await self.queue.put(self.rewind_string)

        logger.debug("Restarting tail session for: %s", self.filename)
        return True

    async def tail_while_growing(self) -> None:
        """
        Handles one "session" of tailing a file. Waits for creation if needed,
        opens the file, reads initial lines, and follows changes until the file
        is detected as removed, moved, or shrunk (if rewind is on).
        This function returns when the current file session should end.
        Raises FileNotFoundError if wait_for_create fails.
        """
        created = False
        # For non-existent files, fail fast if not waiting
        if not self.wait_for_create and not Path(self.filename).exists():
            raise FileNotFoundError(f"File not found: {self.filename}")

        if self.wait_for_create and not Path(self.filename).exists():
            logger.debug("Waiting for file to be created: %s", self.filename)
            await self.wait_for_file_creation()
            created = True

        # Read all lines if explicitly requested, or if rewind and follow are on and the file was just created
        read_all_initial = self.all_lines or (created and self.follow and self.rewind)

        async with aiofiles.open(self.filename, mode="r") as f:
            # Regular tail functionality
            # FIXME this is inefficient when using the -n option on regular files
            # TODO use the tac code, maybe add an option not to reverse the lines and call it tail
            if read_all_initial or self.lines > 0:
                logger.debug("Reading initial lines from file: %s", self.filename)
                lines_read = await f.readlines()
                if not read_all_initial:
                    lines_read = lines_read[-self.lines:]
                assert self.queue is not None
                for line in lines_read:
                    await self.queue.put(line)
                logger.debug("Put %d initial lines in queue", len(lines_read))
            else:
                # No initial lines needed, seek to end (if possible)
                logger.debug("Seeking to end of file: %s", self.filename)
                await self.seek_to_end(f)

            # 2. Follow changes if configured
            if self.follow and self.poll_interval is not None:
                    await self.follow_changes_poll(f)
            elif self.follow:
                        await self.follow_changes_notify(f)

    async def seek_to_end(self, f: AsyncTextIOWrapper) -> None:
        """Seeks to the end of the file stream, ignoring errors for unseekable streams."""
        try:
            await f.seek(0, io.SEEK_END)
        except io.UnsupportedOperation:
            logger.debug("File %s is not seekable, cannot seek to end.", self.filename)

    async def seek_to_position(self, f: AsyncTextIOWrapper, pos: int) -> None:
        """Seeks to the specified position in the file stream, ignoring errors for unseekable streams."""
        try:
            await f.seek(pos, io.SEEK_SET)
        except io.UnsupportedOperation:
            logger.debug("File %s is not seekable, cannot seek to position %d.", self.filename, pos)

    async def get_file_position(self, f: AsyncTextIOWrapper) -> int | None:
        """Gets the current file position, returns None if not supported."""
        try:
            return await f.tell()
        except io.UnsupportedOperation:
            logger.debug("File %s does not support tell(), cannot track position.", self.filename)
            return None

    async def setup_file_watcher(self) -> None:
        """Sets up the inotify watcher for the file."""
        self.close_watcher()  # Ensure any previous watcher is closed
        self.watcher = aionotify.Watcher()
        watch_flags = aionotify.Flags.MODIFY | self.REMOVED_FLAGS
        self.watcher.watch(path=self.filename, flags=watch_flags)
        await self.watcher.setup(asyncio.get_event_loop())
        logger.debug("aionotify watcher set up for %s", self.filename)

    async def follow_changes_notify(self, f: AsyncTextIOWrapper) -> None:
        """Follow the file using inotify, until it is removed or shrunk (if rewind)."""
        logger.debug("Following changes (inotify) to file: %s", self.filename)
        pos_previous = await self.get_file_position(f)

        try:
            await self.setup_file_watcher()
            while pos_previous is not None:
                pos_previous = await self.follow_changes_notify_step(f, pos_previous)
        finally:
            self.close_watcher()

    async def follow_changes_notify_step(self, f: AsyncTextIOWrapper, pos_previous: int | None) -> int | None:
        """
        One step of following changes using inotify.
        Reads available lines, checks for shrink/removal, waits for event.
        Returns the updated file position (int) to continue, or None to stop following.
        """
        assert self.queue is not None
        assert self.watcher is not None

        # 1. Read available lines since last check
        lines_read_count = 0
        while line := await f.readline():
            await self.queue.put(line)
            lines_read_count += 1
        # logger.debug("Read %d lines from %s", lines_read_count, self.filename) # Can be noisy

        # 2.Check for file shrinkage if we can rewind, the previous size is known, and no lines were read.
        if self.rewind and pos_previous is not None and not lines_read_count:
            pos_before_seek = await self.get_file_position(f)
            await self.seek_to_end(f)
            current_size = await self.get_file_position(f)
            assert pos_before_seek is not None
            assert current_size is not None
            larger_earlier_size = max(pos_previous, pos_before_seek)
            smaller_later_size = min(current_size, pos_before_seek)
            if smaller_later_size < larger_earlier_size:
                logger.debug("File has shrunk from %d to %d, rewinding", larger_earlier_size, smaller_later_size)
                return None
            if current_size > pos_before_seek:
                logger.debug("File has grown in race condition, rewinding to previous position")
                await self.seek_to_position(f, pos_before_seek)
                current_size = pos_before_seek
                self.rewind = False
            pos_previous = current_size

        # 3. Wait for the next filesystem event
        logger.debug("Waiting for file event: %s", self.filename)
        event = await self.watcher.get_event()
        assert event is not None

        logger.debug("Received event: flags=%s, name=%s", event.flags, event.name)

        # 4. Handle file removal/move events detected by inotify
        if event.flags & self.REMOVED_FLAGS:
            # Add a small delay before checking existence, FS events can be slightly ahead
            exists = Path(self.filename).exists()
            await asyncio.sleep(0.001)
            exists = exists and Path(self.filename).exists()
            if not Path(self.filename).exists():
                logger.info("File removed or moved (detected by inotify): %s", self.filename)
                return None

        # 5. Handle modification event (MODIFY flag)
        # No explicit action needed here, the loop reads any new lines at the start.
        return pos_previous

    async def follow_changes_poll(self, f: AsyncTextIOWrapper) -> None:
        """
        Follow the file using polling instead of inotify.
        Runs until the file is removed or shrunk (if rewind enabled).
        """
        logger.debug("Following changes (polling) to file: %s", self.filename)
        assert self.queue is not None
        assert self.poll_interval is not None

        pos_previous = await self.get_file_position(f) if self.rewind else None

        while True:
            # Check for existence at the start of each poll cycle
            if not Path(self.filename).exists():
                logger.info("File %s not found during poll, stopping follow.", self.filename)
                break

            # 1. Read available lines
            lines_read_count = 0
            while line := await f.readline():
                await self.queue.put(line)
                lines_read_count += 1

            # 2. Check for shrinkage (if rewind enabled and file seekable)
            if self.rewind and pos_previous is not None and not lines_read_count:
                    # Get current size (seek to end)
                pos_before_seek = await self.get_file_position(f)  # Position after reading
                await self.seek_to_end(f)
                current_size = await self.get_file_position(f)
                logger.debug("Poll shrink check: prev_pos=%s, current_size=%s", pos_previous, current_size)
                assert pos_before_seek is not None
                assert current_size is not None

                if current_size < pos_previous:
                    logger.info("File %s shrunk (polling) from %d to %d bytes, r rewind.", self.filename, pos_previous, current_size)
                    return

                pos_previous = current_size

                # Restore position to where we finished reading, as seek_to_end() moved it
                if pos_before_seek < current_size:
                    await self.seek_to_position(f, pos_before_seek)

            # 3. Wait for the poll interval
            await asyncio.sleep(self.poll_interval)

    async def wait_for_file_creation(self) -> None:
        """Wait for the file to be created using inotify or polling."""
        logger.debug("Waiting for file creation: %s", self.filename)
        if self.poll_interval is not None:
            await self.wait_for_file_creation_poll()
            return

        folder = Path(self.filename).parent

        # Ensure folder exists before watching
        if not folder.is_dir():
            logger.error("Cannot wait for file creation: Parent directory %s does not exist.", folder)
            raise FileNotFoundError(f"Parent directory does not exist: {folder}")

        try:
            self.close_watcher()
            self.watcher = aionotify.Watcher()

            # Watch for file creation or being moved into the directory
            self.watcher.watch(str(folder), aionotify.Flags.CREATE | aionotify.Flags.MOVED_TO)
            await self.watcher.setup(asyncio.get_event_loop())

            while not Path(self.filename).exists():
                event = await self.watcher.get_event()  # pylint: disable=unused-variable
        finally:
            self.close_watcher()

    async def wait_for_file_creation_poll(self) -> None:
        """Wait for the file to be created using polling."""
        logger.debug("Waiting for file creation (polling): %s", self.filename)
        assert self.poll_interval is not None
        while not Path(self.filename).exists():
            await asyncio.sleep(self.poll_interval)

    def close_watcher(self) -> None:
        """Safely close the aionotify watcher if it exists."""
        if not self.watcher:
            return
        try:
            self.watcher.close()
            logger.debug("aionotify watcher closed.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Exception closing watcher: %r", e)
        self.watcher = None


async def atail(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    output: TextIO,
    filename: str = AsyncTail.DEFAULT_FILENAME,
    wait_for_create: bool = False,
    lines: int = 0,
    all_lines: bool = False,
    follow: bool = False,
    rewind: bool = False,
    rewind_string: str | None = None,
    restart: bool = False,
    poll_interval: float | None = None,
) -> None:
    """
    High-level async function to tail a file and print output.

    This serves as the main entry point for the command-line tool and
    provides an example of how to use the AsyncTail class.

    Args:
        output: The stream to write output lines to (default: sys.stdout).
        filename: Path to the file to tail.
        wait_for_create: Wait for file creation if it doesn't exist.
        lines: Number of initial lines from the end to show (0 = from current pos).
        all_lines: Show all lines from the start initially.
        follow: Keep watching for new lines.
        rewind: Restart reading if the file shrinks.
        rewind_string: String to print when rewind occurs.
        restart: Re-open file if removed and reappears.
        poll_interval: Use polling with this interval (seconds) instead of inotify.
    """
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
        while (line := await queue.get()) is not AsyncTail.EOF_MARKER:
                assert line is not None
                output.write(line)
                output.flush()
                queue.task_done()
        logger.debug("Received EOF marker, stopping output loop.")
        queue.task_done()


def get_opts() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "filename", nargs="?", default=AsyncTail.DEFAULT_FILENAME, help="the file to tail ('-' or omitted for stdin)"
    )
    parser.add_argument("-w", "--wait-for-create", action="store_true", help="wait for the file to be created if it doesn't exist")
    parser.add_argument("-n", "--lines", type=int, default=0, help="output the last N lines (0 means start from end)")
    parser.add_argument("-a", "--all-lines", action="store_true", help="output all lines from the start (overrides -n)")
    parser.add_argument("-f", "--follow", action="store_true", help="output appended data as the file grows")
    parser.add_argument("-r", "--rewind", action="store_true", help="rewind to start if file shrinks (implies -f)")
    parser.add_argument("-R", "--rewind-string", help="string to output when a rewind occurs (requires -r)")
    parser.add_argument(
        "-s", "--restart", action="store_true", help="keep trying to open the file after it is removed/moved (implies -f)"
    )
    parser.add_argument(
        "-p", "--poll", type=float, help="use polling with specified interval in seconds (disables inotify, implies -f)"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ucm.add_logging_options(parser)
    opts = parser.parse_args()

    if opts.filename == "-":
        opts.filename = AsyncTail.DEFAULT_FILENAME  # Explicitly use stdin

    # Imply -f if options requiring it are used
    if opts.rewind or opts.restart or opts.poll is not None:
        if not opts.follow:
            logger.debug("Implicitly enabling --follow (-f) because --rewind, --restart, or --poll was specified.")
            opts.follow = True

    # Validation or adjustments
    if opts.all_lines and opts.lines > 0:
        logger.warning("Both --all-lines (-a) and --lines (-n > 0) specified; --all-lines takes precedence.")
        opts.lines = 0

    if opts.rewind_string and not opts.rewind:
        parser.error("--rewind-string (-R) requires --rewind (-r)")

    return opts


def main() -> None:
    """Main command-line entry point."""
    opts = get_opts()
    ucm.setup_logging(opts)

    # Log effective settings
    logger.info("Starting atail for: %s", opts.filename)
    logger.debug("Effective settings: %s", opts)

    ucm.run_async(
        atail(
            output=sys.stdout,
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
