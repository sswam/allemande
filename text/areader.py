""" areader: Async File Reader """
import asyncio
import logging

import aiofiles


logger = logging.getLogger(__name__)


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
            await self.queue.put(None)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error reading file: %s", str(e))
            raise
