#!/usr/bin/env python3

import asyncio

async def multi_port_coroutine():
    get_queue = asyncio.Queue()
    put_queue = asyncio.Queue()

    async def process():
        while True:
            item = await get_queue.get()
            print(f"Got: {item}")
            await put_queue.put(f"Processed {item}")

    return get_queue, put_queue, process()


async def cancel(task):
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def main():
    get_queue, put_queue, process_task = await multi_port_coroutine()

    task = asyncio.create_task(process_task)

    await get_queue.put("Hello")
    result = await put_queue.get()
    print(f"Result: {result}")

    await cancel(task)


asyncio.run(main())
