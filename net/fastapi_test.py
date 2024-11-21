#!/usr/bin/env python3-allemande

from contextlib import asynccontextmanager
import time
import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, BackgroundTasks
from anyio import to_thread


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources."""
    to_thread.current_default_thread_limiter().total_tokens = 200
    pool = ThreadPoolExecutor(max_workers=100)
    yield {"pool": pool}
    pool.shutdown()


app = FastAPI(lifespan=lifespan)


def sync_func() -> None:
    """Synchronous function that sleeps for 3 seconds."""
    time.sleep(3)
    print("sync func")


async def sync_async_with_fastapi_thread() -> None:
    """Asynchronous function using FastAPI's thread pool."""
    await to_thread.run_sync(time.sleep, 3)
    print("sync async with fastapi thread")


async def sync_async_func() -> None:
    """Asynchronous function using default thread pool."""
    await to_thread.run_sync(time.sleep, 3)
    print("sync async")


async def async_func() -> None:
    """Pure asynchronous function using asyncio.sleep."""
    await asyncio.sleep(3)
    print("async func")


@app.get("/sync")
def test_sync() -> None:
    """Test endpoint for synchronous operation."""
    sync_func()
    print("sync")


@app.get("/async")
async def test_async() -> None:
    """Test endpoint for asynchronous operation."""
    await async_func()
    print("async")


@app.get("/sync_async")
async def test_sync_async() -> None:
    """Test endpoint for synchronous operation in async context."""
    await sync_async_func()
    print("sync async")


@app.get("/sync_async_fastapi")
async def test_sync_async_with_fastapi_thread() -> None:
    """Test endpoint for FastAPI thread pool operation."""
    await sync_async_with_fastapi_thread()
    print("sync async with fastapi thread")


@app.get("/get_available_threads")
async def get_available_threads() -> int:
    """Return the number of available thread tokens."""
    return to_thread.current_default_thread_limiter().available_tokens
