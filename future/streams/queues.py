#!/usr/bin/env python

import re
import asyncio
import sys
from typing import List, Tuple

async def grep(pattern: str, input_queue: asyncio.Queue, output_queue: asyncio.Queue):
    regex = re.compile(pattern)
    while True:
        item = await input_queue.get()
        if item is None:
            await output_queue.put(None)
            input_queue.task_done()
            break
        if regex.search(item):
            await output_queue.put(item)
        input_queue.task_done()

async def map_collect(func, input_queue: asyncio.Queue, output_queue: asyncio.Queue, func_final=None):
    acc = []
    while True:
        item = await input_queue.get()
        if item is None:
            if func_final:
                output = func_final(acc)
                for out_item in output:
                    await output_queue.put(out_item)
            await output_queue.put(None)
            input_queue.task_done()
            break
        output, acc = func(acc + [item])
        for out_item in output:
            await output_queue.put(out_item)
        input_queue.task_done()

async def stream_for(data, output_queue: asyncio.Queue):
    for item in data:
        await output_queue.put(item)
    await output_queue.put(None)

def mapping_func(items: List[str]) -> Tuple[List[str], List[str]]:
    accumulated = ''.join(items)
    lines = accumulated.split('\n')

    if len(lines) > 1:
        complete_lines = lines[:-1]
        remainder = lines[-1]
        return complete_lines, [remainder]
    else:
        return [], items

async def process_stream(input_queue: asyncio.Queue):
    pattern = r'\b(AI|artificial intelligence)\b'

    lines_queue = asyncio.Queue()
    filtered_queue = asyncio.Queue()

    map_task = asyncio.create_task(map_collect(mapping_func, input_queue, lines_queue))
    grep_task = asyncio.create_task(grep(pattern, lines_queue, filtered_queue))

    while True:
        item = await filtered_queue.get()
        if item is None:
            filtered_queue.task_done()
            break
        print(f"Processed: {item}")
        filtered_queue.task_done()

    await map_task
    await grep_task

async def main():
    input_queue = asyncio.Queue()
    stream_task = asyncio.create_task(stream_for(sys.stdin, input_queue))
    process_task = asyncio.create_task(process_stream(input_queue))

    await stream_task
    await process_task

if __name__ == "__main__":
    asyncio.run(main())
