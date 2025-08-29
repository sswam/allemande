#!/usr/bin/env python3-allemande

"""Async message gatherer with debouncing"""

import argparse
import logging
import asyncio
from typing import Any

import ucm

from areader import AsyncFileReader

logger = logging.getLogger(__name__)


class AsyncGather:
    """Collects messages and forwards them after a timeout"""

    def __init__(self, input_queue: asyncio.Queue, wait: float):
        """Initialize the gatherer with input queue and wait time"""
        self.input_queue = input_queue
        self.wait = wait
        self.output_queue = None
        self.task = None
        self.buffer: list[Any] = []
        self.timer_handle = None
        self.flush_lock = asyncio.Lock()

    async def __aenter__(self):
        self.output_queue = asyncio.Queue()
        self.task = asyncio.create_task(self._run())
        return self.output_queue

    async def __aexit__(self, *args):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        # Cancel any pending timer
        if self.timer_handle and not self.timer_handle.cancelled():
            self.timer_handle.cancel()

        # Flush remaining messages with lock to avoid race
        async with self.flush_lock:
            if self.buffer:  # Send any remaining messages
                await self.output_queue.put("".join(self.buffer))
                self.buffer.clear()

        self.task = None
        self.output_queue = None

    def _reset_timer(self):
        """Reset the debounce timer"""
        if self.timer_handle and not self.timer_handle.cancelled():
            self.timer_handle.cancel()

        # Create the flush task directly when timer expires
        self.timer_handle = asyncio.get_event_loop().call_later(
            self.wait, lambda: asyncio.create_task(self._flush_buffer()))

    async def _flush_buffer(self):
        """Flush the current buffer to output queue"""
        async with self.flush_lock:
            if not self.buffer:
                return
            await self.output_queue.put("".join(self.buffer))
            self.buffer.clear()

    async def _run(self):
        """Gather messages and forward them after timeout"""
        try:
            while True:
                msg = await self.input_queue.get()
                if msg is None:  # EOF
                    # Cancel timer before final flush
                    if self.timer_handle and not self.timer_handle.cancelled():
                        self.timer_handle.cancel()
                    await self._flush_buffer()
                    await self.output_queue.put(None)
                    break

                async with self.flush_lock:
                    self.buffer.append(msg)
                self.input_queue.task_done()
                self._reset_timer()
        except asyncio.CancelledError:
            # Let cancellation propagate
            raise


async def agather_demo(wait: float = 0.2):
    """Demo the message gatherer"""
    async with AsyncFileReader("/dev/stdin") as input_queue:
        async with AsyncGather(input_queue, wait) as queue:
            while True:
                item = await queue.get()
                if item is None:
                    break
                print(item, end="", flush=True)
                queue.task_done()


def get_opts():
    """Get command line options"""
    parser = argparse.ArgumentParser(description="agather", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-w", "--wait", type=float, default=0.2, help="Wait before forwarding messages (seconds)")
    ucm.add_logging_options(parser)
    opts = parser.parse_args()
    return opts


def main():
    """Main function"""
    opts = get_opts()
    ucm.setup_logging(opts)
    asyncio.run(agather_demo(opts.wait))


if __name__ == "__main__":
    main()
