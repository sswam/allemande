#!/usr/bin/env python3

"""
This module benchmarks the overhead of using async/await and supporting
infrastructure in Python.
"""

import sys
import logging
import time
import asyncio
from typing import TextIO, Tuple, Any
from functools import wraps

from argh import arg

from ally import main  # type: ignore

__version__ = "0.1.3"  # Bumped patch version

logger = main.get_logger()  # type: ignore


def timeit(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


async def async_null():
    return None


def sync_null():
    return None


async def async_add(a: int, b: int) -> int:
    return a + b


def sync_add(a: int, b: int) -> int:
    return a + b


@timeit
def benchmark_sync_call(iterations: int):
    for _ in range(iterations):
        sync_null()


@timeit
async def benchmark_async_call(iterations: int):
    for _ in range(iterations):
        await async_null()


@timeit
async def benchmark_sleep_zero(iterations: int) -> Tuple[float, float]:
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await asyncio.sleep(0)
        times.append(time.perf_counter() - start)
    return min(times), sum(times) / len(times)


@timeit
def benchmark_sync_add(iterations: int):
    for _ in range(iterations):
        sync_add(1, 2)


@timeit
async def benchmark_async_add(iterations: int):
    for _ in range(iterations):
        await async_add(1, 2)


@timeit
async def benchmark_event_loop_start():
    async def null_coro():
        pass
    loop = asyncio.new_event_loop()
    await loop.run_in_executor(None, loop.run_until_complete, null_coro())
    loop.close()


@timeit
async def benchmark_sync_from_async(iterations: int):
    for _ in range(iterations):
        await asyncio.to_thread(sync_null)


@timeit
async def benchmark_create_task(iterations: int):
    for _ in range(iterations):
        await asyncio.create_task(async_null())


@arg("--iterations", "-i", help="number of iterations for each benchmark", type=int, default=100000)
def benchmark(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    iterations: int = 100000
) -> None:
    """
    Run various benchmarks to measure the overhead of async/await in Python.
    """
    get, put = main.io(istream, ostream)

    put(f"Running benchmarks with {iterations} iterations...")

    async def run_benchmarks():
        # Sync vs Async null function call
        sync_result, sync_time = benchmark_sync_call(iterations)
        async_result, async_time = await benchmark_async_call(iterations)
        put(f"Sync null function: {sync_time:.6f} seconds")
        put(f"Async null function: {async_time:.6f} seconds")
        put(f"Async overhead: {async_time - sync_time:.6f} seconds")

        # asyncio.sleep(0)
        sleep_result, sleep_time = await benchmark_sleep_zero(iterations)
        min_sleep, avg_sleep = sleep_result
        put(f"asyncio.sleep(0) - Min: {min_sleep:.9f} seconds, Avg: {avg_sleep:.9f} seconds")

        # Sync vs Async add function
        sync_add_result, sync_add_time = benchmark_sync_add(iterations)
        async_add_result, async_add_time = await benchmark_async_add(iterations)
        put(f"Sync add function: {sync_add_time:.6f} seconds")
        put(f"Async add function: {async_add_time:.6f} seconds")
        put(f"Async add overhead: {async_add_time - sync_add_time:.6f} seconds")

        # Event loop start time
        loop_result, loop_time = await benchmark_event_loop_start()
        put(f"Event loop start time: {loop_time:.6f} seconds")

        # Sync from async (thread wrapper)
        sync_from_async_result, sync_from_async_time = await benchmark_sync_from_async(iterations)
        put(f"Sync from async (thread wrapper): {sync_from_async_time:.6f} seconds")

        # Benchmark different event loop implementations
        default_loop_result, default_loop_time = await benchmark_event_loop_start()
        put(f"Default event loop start time: {default_loop_time:.6f} seconds")

#         try:
#             import uvloop
#             asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
#             uvloop_result, uvloop_time = await benchmark_event_loop_start()
#             put(f"uvloop event loop start time: {uvloop_time:.6f} seconds")
#             put(f"uvloop speedup: {default_loop_time / uvloop_time:.2f}x")
#         except ImportError:
#             put("uvloop not available. Install it to benchmark alternative event loop implementation.")
# 
#         # Benchmark create_task vs await
#         create_task_result, create_task_time = await benchmark_create_task(iterations)
#         put(f"create_task and await: {create_task_time:.6f} seconds")
#         put(f"create_task overhead: {create_task_time - async_time:.6f} seconds")

    try:
        asyncio.run(run_benchmarks())
    except Exception as e:
        logger.error(f"An error occurred during benchmarking: {e}")
        raise


if __name__ == "__main__":
    main.run(benchmark)
