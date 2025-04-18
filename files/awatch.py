#!/usr/bin/env python3-allemande

""" Watch files and directories for changes """

import sys
import os
from pathlib import Path
import re
import subprocess
import asyncio
from typing import Callable

from pydantic import BaseModel
from watchfiles import awatch, Change, DefaultFilter
from hidden import contains_hidden_component

from ally import main, logs

__VERSION__ = "0.1.3"


logger = logs.get_logger()


class WatcherOptions(BaseModel):
    """WatcherOptions: a class that holds the options for the Watcher class"""

    exts: list[str] = []
    extension: list[str] = []
    all_files: bool = False
    hidden: bool = False
    dirs: bool = False
    initial_state: bool = False
    initial_scan: bool = False
    follow: bool = False
    recursive: bool = False
    absolute: bool = False
    run: bool = False
    job: bool = False
    service: bool = False
    command: list[str] = []
    debounce: float = 0.01
    exclude_paths: list[str] = []
    metadata: bool = False


class Debounce:  # pylint: disable=too-few-public-methods
    """Generic debouncing class"""

    # func is async
    def __init__(self, func: Callable, *args, delay: float = 0.01, **kwargs):
        self.delay = delay
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.pending_task: asyncio.Task | None = None

    async def trigger(self):
        """Schedule the function to be called after the delay"""
        # Cancel any pending operation
        if self.pending_task:
            self.pending_task.cancel()

        # Schedule new operation after delay
        self.pending_task = asyncio.create_task(self._delayed_execute())

    async def _delayed_execute(self):
        """Execute the operation after waiting for the delay"""
        try:
            await asyncio.sleep(self.delay)
            logger.info("Executing debounced function")
            await self.func(*self.args, **self.kwargs)
        finally:
            self.pending_task = None


class ServiceManager:
    """Manages service processes with throttled restarts"""

    def __init__(self, service_command: list[str]):
        self.service_command = service_command
        self.current_process: subprocess.Popen | None = None

    def term_or_kill(self):
        """Wait for the current process to finish"""
        if not self.current_process:
            return
        try:
            self.current_process.terminate()
            self.current_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.current_process.kill()
            self.current_process.wait()

    async def stop(self) -> None:
        """Clean up the current process if it exists"""
        if not self.current_process:
            return
        await asyncio.to_thread(self.term_or_kill)

    async def start(self) -> None:
        """Start or restart the service"""
        await self.stop()
        self.current_process = subprocess.Popen(self.service_command)  # pylint: disable=consider-using-with


class Watcher:  # pylint: disable=too-many-instance-attributes
    """Watcher: a class that can watch files and directories for changes"""

    flush = object()

    def __init__(self, paths, opts: WatcherOptions):
        """Initialize the Watcher object"""
        self.opts = opts
        self.paths = [self.resolve_path(p) for p in paths]
        self.exclude_paths = [self.resolve_path(p) for p in opts.exclude_paths]
        self.default_filter = DefaultFilter()
        self.file_sizes: dict[str, int] = {}
        self.dirs: set[str] = set()
        self.cwd = os.getcwd() + os.path.sep
        self.service_manager = ServiceManager(opts.command)
        self.restart_service_debounce = Debounce(self.service_manager.start, delay=opts.debounce)

    def resolve_path(self, path):
        """A path given with a trailing / means to follow any symlink"""
        if self.opts.follow or path.endswith("/"):
            return str(Path(path).resolve())
        if self.opts.absolute:
            return str(Path(path).absolute())
        return path

    async def run_command(self, *args):
        """Handle running commands asynchronously"""
        try:
            process = await asyncio.create_subprocess_exec(
                *self.opts.command, *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error("Command failed with exit code %d", process.returncode)
            logger.error(stderr.decode())
            print(stdout.decode())
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Failed to run command: %s", str(e))

    async def changed_run_process(self, changed_path):
        """Run the command or service when a file changes"""
        if self.opts.run:
            await self.run_command(changed_path)
        elif self.opts.job:
            await self.run_command()
        elif self.opts.service:
            await self.restart_service_debounce.trigger()

    async def run(self):
        """Watch the files and directories"""

        if self.opts.initial_state or self.opts.initial_scan:
            for path in self.paths:
                async for row in self.handle_change(Change.added, path, initial=True):
                    if self.opts.initial_state:
                        yield row
                        await self.changed_run_process(path)
            if self.opts.initial_state:
                yield self.flush

        watcher = awatch(*self.paths, watch_filter=self.watch_filter, recursive=self.opts.recursive)

        try:
            async for changes in watcher:
                for change_type, path in changes:
                    if not self.opts.absolute and path.startswith(self.cwd):
                        path = path[len(self.cwd) :]
                    if not self.opts.absolute and path.startswith("." + os.path.sep):
                        path = path[len("." + os.path.sep) :]
                    async for row in self.handle_change(change_type, path):
                        yield row
                        await self.changed_run_process(path)
                yield self.flush
        finally:
            await self.service_manager.stop()

    def is_excluded(self, path):
        """Check if a path is in the exclude list"""
        for exclude_path in self.exclude_paths:
            if path == exclude_path or path.startswith(exclude_path + os.path.sep):
                return True
        return False

    def watch_filter(self, change_type, path):
        """Filter out files and directories that we don't want to watch"""
        try:
            return self.watch_filter_2(change_type, path)
        except (OSError, PermissionError, FileNotFoundError) as e:
            logger.warning("Error filtering: %s", str(e))
            return False

    def watch_filter_2(self, change_type, path):
        """Filter out files and directories that we don't want to watch"""
        if not self.default_filter(change_type, path):
            return False
        if not self.opts.hidden and contains_hidden_component(path):
            return False
        if self.is_excluded(path):
            return False
        p = Path(path)
        is_dir = p.is_dir()
        if is_dir or path in self.dirs:
            return True

        if not self.opts.metadata and change_type == Change.modified:
            # don't trigger on metadata changes
            stat = os.stat(path)
            if stat.st_mtime != stat.st_ctime:
                return False

        return self.opts.all_files or path.endswith(tuple(self.opts.exts))

    async def handle_change(self, change_type, path, initial=False):
        """Handle a change to a file or directory"""
        try:
            async for row in self.handle_change_2(change_type, path, initial):
                yield row
        except (OSError, PermissionError, FileNotFoundError) as e:
            logger.error("Error handling change: %s", str(e))

    async def handle_change_2(self, change_type, path, initial=False):
        """Handle a change to a file or directory"""
        logger.debug("change_type: %r, path: %r", change_type, path)

        if re.search(r"[\n\t]", path):
            logger.warning("path contains newline or tab, skipping: %r", path)
            return

        if not self.watch_filter(change_type, path):
            return

        p = Path(path)

        # Is it a directory?

        if change_type == Change.deleted:
            is_dir = path in self.dirs
        else:
            is_dir = p.is_dir() and (self.opts.follow or not p.is_symlink())

        # Get size for files or symlinks (if not following), but not dirs.

        size = self.file_sizes.pop(path, None)
        size_new = None

        if change_type != Change.deleted:
            is_file = p.exists() and not is_dir
            if is_file and self.opts.follow:
                size_new = p.stat().st_size
            elif is_file:
                size_new = p.lstat().st_size

        if is_dir and change_type == Change.added and (self.opts.recursive or initial):
            async for row in self.added_directory(path):
                yield row
        elif is_dir and change_type == Change.deleted and self.opts.recursive:
            async for row in self.deleted_directory(path):
                yield row
        elif not is_dir and not (change_type == Change.deleted and size is None):
            row = [path, int(change_type), size, size_new]
            if size_new is not None:
                self.file_sizes[path] = size_new
            yield row

    async def added_directory(self, path):
        """Handle entries under a directory that was added"""
        self.dirs.add(path)
        if self.opts.dirs:
            row = [path + os.path.sep, int(Change.added), None, None]
            yield row
        p = Path(path)
        for e in sorted(p.iterdir(), key=lambda x: x.stat().st_ctime):
            logger.debug("e: %r", e)
            async for row in self.handle_change(Change.added, str(e)):
                yield row

    async def deleted_directory(self, path):
        """Handle entries under a directory that was deleted"""
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
    """Replace None with replacement"""
    if x is None:
        return replacement
    return x


async def awatch_main(paths, opts: WatcherOptions, out=sys.stdout):
    """Main function for awatch"""
    opts.exts = [f".{ext}" for ext in opts.extension]
    if (opts.run or opts.job or opts.service) and not opts.command:
        raise ValueError("command is required when using --run, --job or --service")
    w = Watcher(paths, opts)
    async for row in w.run():
        if row == Watcher.flush:
            out.flush()
            logger.info("flushed")
        else:
            print(*[null_to(x, "") for x in row], sep="\t", file=out)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-p", "--paths", nargs="*", default=".", help="files and directories to watch")
    arg("-r", "--recursive", help="watch recursively under the folders", action="store_true")
    arg("-x", "--extension", nargs="*", default=[], help="file extensions to watch")
    arg("-a", "--all-files", help="watch all files", action="store_true")
    arg("-H", "--hidden", help="watch hidden files", action="store_true")
    arg("-D", "--dirs", help="report changes to directories", action="store_true")
    arg("-i", "--initial-state", help="report initial state", action="store_true")
    arg("-I", "--initial-scan", help="scan initial state but do not report", action="store_true")
    arg("-L", "--follow", help="follow symlinks", action="store_true")
    arg("-A", "--absolute", help="return absolute paths", action="store_true")
    arg("-R", "--run", help="run command when files change, with pathname as argument", action="store_true")
    arg("-J", "--job", help="run command when files change, with no arguments", action="store_true")
    arg("-s", "--service", help="run and restart a service when files change", action="store_true")
    arg("-d", "--debounce", type=float, default=0.01, help="debounce time in seconds for service commands")
    arg("-e", "--exclude", dest="exclude_paths", nargs="*", default=[], help="paths to exclude from watching")
    arg("-m", "--metadata", help="watch metadata changes", action="store_true")
    arg("command", nargs="*", help="command or service to run when files change")


if __name__ == "__main__":
    main.go(awatch_main, setup_args)
