#!/usr/bin/env python

import re
import asyncio
from typing import List, Tuple


async def grep(pattern: str, stream):
    regex = re.compile(pattern)
    async for item in stream:
        if regex.search(item):
            yield item


async def map_collect(func, stream, initial_acc: List = None, func_final=None):
    acc = initial_acc or []
    async for item in stream:
        output, acc = func(acc + [item])
        for out_item in output:
            yield out_item
    if func_final:
        output = final_func(acc)
        for out_item in output:
            yield out_item


async def stream_for(data):
    for item in data:
        yield item


def mapping_func(items: List[str]) -> Tuple[List[str], List[str]]:
    accumulated = ''.join(items)
    lines = accumulated.split('\n')

    if len(lines) > 1:
        complete_lines = lines[:-1]
        remainder = lines[-1]
        return complete_lines, [remainder]
    else:
        return [], items


async def process_stream(stream):
    pattern = r'\b(AI|artificial intelligence)\b'
    lines = map_collect(mapping_func, stream)
    filtered = grep(pattern, lines)

    async for item in filtered:
        print(f"Processed: {item}")


async def main():
    example_data = [
        "This is a line about AI\n",
        "and artificial intelligence\n",
        "spanning multiple ",
        "lines.\n",
        "Another line mentioning AI",
        " but not complete\n",
        "Final lines\nabout\nartificial intelligence.\nGood-bye!"
    ]

    stream = stream_for(example_data)
    await process_stream(stream)


if __name__ == "__main__":
    asyncio.run(main())
