#!/usr/bin/env python3-allemande

""" akeepalive: Async Keepalive Generator """

import sys
import argparse
import logging
import asyncio
import aiofiles

import ucm

logger = logging.getLogger(__name__)


class AsyncKeepAlive:
    """Async Keepalive Generator"""

    def __init__(self, input_queue, timeout, timeout_return=None):
        """Initialize the Async Keepalive Generator"""
        self.input_queue = input_queue
        self.timeout = timeout
        self.timeout_return = timeout_return
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
        """Forward items from the input_queue to the output_queue, adding keepalive items on timeout"""
        while True:
            next_item = None
            try:
                next_item = await asyncio.wait_for(self.input_queue.get(), timeout=self.timeout)
                await self.queue.put(next_item)
            except asyncio.TimeoutError:
                await self.queue.put(self.timeout_return)
            finally:
                if next_item is not None:
                    self.input_queue.task_done()


# TODO put this in a separate module

class AsyncFileReader:
    """Async File Reader"""

    def __init__(self, ifile: str):
        """Initialize the Async Reader"""
        self.ifile = ifile
        self.istream = None
        self.queue = None
        self.task = None

    async def __aenter__(self):
        self.istream = await aiofiles.open(self.ifile, mode="r")
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
        if self.istream:
            await self.istream.close()

    async def _run(self):
        """Forward items from the istream to the queue"""
        try:
            while True:
                line = await self.istream.readline()
                if not line:
                    break
                await self.queue.put(line)
            # Signal end of file
            await sef.queue.put(None)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Error reading file: %s", str(e))
            raise


async def async_keepalive_demo(timeout, timeout_return):
    """Async Timed Iterator Demo"""
    async with AsyncFileReader("/dev/stdin") as input_queue:
        async with AsyncKeepAlive(input_queue, timeout, timeout_return) as queue:
            while True:
                item = await queue.get()
                if item is None:
                    break
                print(item, end="", flush=True)
                queue.task_done()


def get_opts():
    """Get command line options"""
    parser = argparse.ArgumentParser(description="atimeout", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-t", "--timeout", type=float, default=1, help="Timeout value in seconds")
    parser.add_argument("-r", "--timeout-return", default=".", help="Value to return on timeout")
    ucm.add_logging_options(parser)
    opts = parser.parse_args()
    return opts


def main():
    """Main function"""
    opts = get_opts()
    ucm.setup_logging(opts)
    asyncio.run(async_keepalive_demo(opts.timeout, opts.timeout_return))


if __name__ == "__main__":
    main()
