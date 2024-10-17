# File: /home/sam/allemande/ally/error2.py

import asyncio
from typing import Callable, TypeVar, Coroutine

T = TypeVar('T')
Put = Callable[[T | None], Coroutine[None, None, None]]

async def writer_streamwriter(destination: asyncio.StreamWriter) -> Put:
    async def put(data: bytes | None) -> None:
        if data is None:
            destination.close()
            await destination.wait_closed()
            return
        destination.write(data)
        await destination.drain()
    return put
