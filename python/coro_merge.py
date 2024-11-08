#!/usr/bin/env python3-allemande

import sys
import argparse
from asyncio import Queue, TaskGroup, run
import aiofiles  # type: ignore
from typing import Callable, Any, Coroutine

Get = Callable[[], Coroutine[None, None, Any | None]]
Put = Callable[[Any | None], Coroutine[None, None, None]]

__version__ = '0.1.6'


async def reader(filename: str, put: Put) -> None:
    """Reads lines from a file and puts them into a queue."""
    async with aiofiles.open(filename, 'r') as f:
        async for line in f:
            await put(line)
    await put(None)


async def writer(filename: str, get: Get, mode: str = 'w') -> None:
    """Writes items from a queue to a file."""
    async with aiofiles.open(filename, mode) as f:
        while (item := await get()) is not None:
            await f.write(item)


async def tasks(*coros: Coroutine) -> list[Any]:
    """Runs multiple coroutines concurrently and returns their results."""
    tasks: list[Any] = []
    async with TaskGroup() as group:
        for coro in coros:
            tasks.append(group.create_task(coro))
    results = [task.result() for task in tasks]
    return results


async def merger_simple(get1: Get, get2: Get, put: Put) -> None:
    """Merges two sorted input streams into a single sorted output stream."""
    item1 = await get1()
    item2 = await get2()

    while item1 is not None and item2 is not None:
        if item1 <= item2:
            await put(item1)
            item1 = await get1()
        else:
            await put(item2)
            item2 = await get2()

    while item1 is not None:
        await put(item1)
        item1 = await get1()

    while item2 is not None:
        await put(item2)
        item2 = await get2()

    await put(None)


async def merger(get1: Get, get2: Get, put: Put) -> None:
    """Merges two sorted input streams into a single sorted output stream efficiently."""
    item1, item2 = await tasks(get1(), get2())

    while item1 is not None and item2 is not None:
        if item1 <= item2:
            _, item1 = await tasks(put(item1), get1())
        else:
            _, item2 = await tasks(put(item2), get2())

    if item2 is None:
        item, get = item1, get1
    else:
        item, get = item2, get2

    while item is not None:
        _, item = await tasks(put(item), get())

    await put(None)


class Que(Queue):
    def __init__(self, maxsize: int) -> None:
        super().__init__(maxsize)

    async def get(self) -> Any:
        item = await super().get()
        self.task_done()
        return item


async def merge(ifile1: str, ifile2: str, ofile: str) -> None:
    """Main function to merge two sorted input files into a single sorted output file."""
    maxsize = 10
    iq1: Que = Que(maxsize)
    iq2: Que = Que(maxsize)
    oq: Que = Que(maxsize)

    await tasks(
        reader(ifile1, iq1.put),
        reader(ifile2, iq2.put),
        merger(iq1.get, iq2.get, oq.put),
        writer(ofile, oq.get),
    )


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Merge two sorted files into a single sorted output file.")
    parser.add_argument("input_file1", help="Path to the first input file")
    parser.add_argument("input_file2", help="Path to the second input file")
    parser.add_argument("output_file", help="Path to the output file")
    args = parser.parse_args()
    await merge(args.input_file1, args.input_file2, args.output_file)


if __name__ == "__main__":
    run(main())
