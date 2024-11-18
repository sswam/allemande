#!/usr/bin/env python3-allemande

"""
Bidirectional chat tool that connects stdin/stdout with /dev/tty.
"""

import sys
import asyncio
import logging
from asyncio import StreamReader, StreamWriter

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


async def read_stream(reader: StreamReader, writer: StreamWriter, name: str) -> None:
    """Read lines from a stream and write them to another stream."""
    try:
        while True:
            line = await reader.readline()
            if not line:
                break
            writer.write(line)
            await writer.drain()
            logger.debug(f"{name} -> {line.decode().rstrip()}")
    except Exception as e:
        logger.error(f"Error in {name}: {e}")


async def chat() -> None:
    """Set up bidirectional communication between stdin/stdout and /dev/tty."""
    # Open /dev/tty for reading and writing
    tty_reader, tty_writer = await asyncio.open_connection(
        open("/dev/tty", "rb", buffering=0),
        open("/dev/tty", "wb", buffering=0),
    )

    # Create tasks for both directions
    stdin_reader = asyncio.StreamReader()
    await asyncio.get_running_loop().connect_read_pipe(
        lambda: asyncio.StreamReaderProtocol(stdin_reader), sys.stdin
    )

    stdout_writer = asyncio.StreamWriter(
        sys.stdout.buffer, None, asyncio.get_running_loop()
    )

    tasks = [
        asyncio.create_task(read_stream(stdin_reader, tty_writer, "output")),
        asyncio.create_task(read_stream(tty_reader, stdout_writer, "input")),
    ]

    await asyncio.gather(*tasks)


def iochat() -> None:
    """Start the bidirectional chat."""
    try:
        asyncio.run(chat())
    except KeyboardInterrupt:
        logger.info("Chat terminated by user")


def setup_args(arg):
    """Set up the command-line arguments."""
    # No arguments needed for this tool
    pass


if __name__ == "__main__":
    main.go(iochat, setup_args)
