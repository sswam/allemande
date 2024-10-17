from asyncio import TaskGroup
import aiofiles  # type: ignore
from typing import TextIO, Any, Callable, Coroutine, AsyncGenerator
from urllib.parse import urlparse
import io

import asyncio
import aiohttp

__version__ = '0.1.5'

Get = Callable[[], Coroutine[None, None, Any]]
Put = Callable[[Any], Coroutine[None, None, None]]


# Reader implementations

async def reader_file(source: str, put: Put) -> None:
    async with aiofiles.open(source, 'r') as f:
        async for line in f:
            await put(line)


async def reader_url(source: str, put: Put) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get(source) as response:
            async for line in response.content.iter_lines():
                await put(line.decode())


async def reader_textio(source: io.TextIOBase, put: Put) -> None:
    # TODO: Try to get the underlying UNIX file descriptor, and use that to read the file with proper non-blocking asyncio.
    #   We can fall back to this if we can't get the file descriptor.
    for line in source:
        await put(line)


async def reader_streamreader(source: asyncio.StreamReader, put: Put) -> None:
    while True:
        line = await source.readline()
        if not line:
            break
        await put(line.decode())


async def reader_filelike(source: io.IOBase, put: Put) -> None:
    while True:
        line = await asyncio.to_thread(source.readline)
        if not line:
            break
        await put(line)


async def reader_socket(sock: socket.socket, put: Put) -> None:
    sock.setblocking(False)
    while True:
        try:
            data = await asyncio.to_thread(sock.recv, 4096)
            if not data:
                break
            await put(data.decode())
        except BlockingIOError:
            await asyncio.sleep(0.1)


# Writer implementations

async def writer_file(destination: str, get: Get, mode: str = 'w') -> None:
    async with aiofiles.open(destination, mode) as f:
        while (item := await get()) is not None:
            await f.write(item)


async def data_generator(get: Callable) -> AsyncGenerator[bytes, None]:
    while True:
        item = await get()
        if item is None:
            break
        if isinstance(item, str):
            yield item.encode('utf-8')
        elif isinstance(item, bytes):
            yield item
        else:
            raise TypeError(f"Unsupported data type: {type(item)}. Expected str or bytes.")


async def collect_bytes(get: Get) -> bytes:
    buffer = io.BytesIO()
    while (item := await get()) is not None:
        buffer.write(item)
    return buffer.getvalue()


async def collect_text(get: Get) -> str:
    buffer = io.StringIO()
    while (item := await get()) is not None:
        buffer.write(item)
    return buffer.getvalue()


def validate_http_method(method: str) -> None:
    if method not in ('PUT', 'POST', 'PATCH', 'DELETE'):
        raise ValueError(f"Unsupported HTTP method for writing: {method}")


async def execute_http_request(session: aiohttp.ClientSession, method: str, url: str, data: bytes | AsyncGenerator[bytes, None]) -> None
    http_method = getattr(session, method.lower())
    async with http_method(url, data=data) as response:
        await response.read()


async def writer_url_stream(destination: str, get: Callable, method: str = 'PUT') -> None:
    validate_http_method(method)
    async with aiohttp.ClientSession() as session:
        await execute_http_request(session, method, destination, data_generator(get))


async def writer_url(destination: str, get: Callable, method: str = 'PUT') -> None:
    validate_http_method(method)
    data = await collect_bytes(get)
    async with aiohttp.ClientSession() as session:
        await execute_http_request(session, method, destination, data)


async def writer_url(destination: str, get: Callable, method: str = 'PUT', stream: bool = True) -> None:
    if stream:
        await writer_url_stream(destination, get, method)
    else:
        await writer_url(destination, get, method)


async def writer_textio(destination: io.TextIOBase, get: Get) -> None:
    # TODO: Try to get the underlying UNIX file descriptor, and use that to write to the file with proper non-blocking asyncio.
    #   We can fall back to this if we can't get the file descriptor.
    while (item := await get()) is not None:
        destination.write(item)
    await asyncio.to_thread(destination.flush)


async def writer_streamwriter(destination: asyncio.StreamWriter, get: Get) -> None:
    while (item := await get()) is not None:
        destination.write(item.encode())
        await destination.drain()
    await destination.close()


async def writer_filelike(destination: io.IOBase, get: Get) -> None:
    while (item := await get()) is not None:
        await asyncio.to_thread(destination.write, item)
    await asyncio.to_thread(destination.flush)


async def writer_socket(sock: socket.socket, get: Get) -> None:
    sock.setblocking(False)
    while True:
        item = await get()
        if item is None:
            break
        try:
            await asyncio.to_thread(sock.sendall, item.encode())
        except BlockingIOError:
            # TODO We should use select, poll, or epoll to wait for the socket to be ready for writing.
            # TODO is there aio socket support in a library?  if so we should use that...
            # Supposedly the asyncio library has support for sockets.
            await asyncio.sleep(0.1)


# Main wrapper functions

# TODO reader() should return a get() function instead of taking a put() function.
# TODO writer() should return a put() function instead of taking a get() function.

async def reader(source: str | TextIO | asyncio.StreamReader | io.IOBase, put: Put) -> None:
    """Reads lines and puts them into a queue."""
    if isinstance(source, str):
        parsed_url = urlparse(source)
        if parsed_url.scheme in ('http', 'https'):
            await reader_url(source, put)
        elif parsed_url.scheme == 'file' or not parsed_url.scheme:
            filename = parsed_url.path if parsed_url.scheme == 'file' else source
            await reader_file(filename, put)
    elif isinstance(source, io.TextIOBase):
        await reader_textio(source, put)
    # TODO binary stream support, with io.IOBase
    elif isinstance(source, asyncio.StreamReader):
        await reader_streamreader(source, put)
    elif isinstance(source, socket.socket):
        await reader_socket(source, put)
    elif hasattr(source, 'readline'):
        await reader_filelike(source, put)
    else:
        raise ValueError(f"Unsupported source type: {type(source)}")
    await put(None)


async def writer(destination: str | TextIO | asyncio.StreamWriter | io.IOBase, get: Get, mode: str = 'w', method: str = 'PUT') -> None:
    """Writes items from a queue to various destinations."""
    if isinstance(destination, str):
        parsed_url = urlparse(destination)
        if parsed_url.scheme in ('http', 'https'):
            await writer_url(destination, put, method=method)
        elif parsed_url.scheme == 'file' or not parsed_url.scheme:
            filename = parsed_url.path if parsed_url.scheme == 'file' else destination
            await writer_file(filename, get, mode)
    elif isinstance(destination, io.TextIOBase):
        await writer_textio(destination, get)
    # TODO binary stream support, with io.IOBase
    elif isinstance(destination, asyncio.StreamWriter):
        await writer_streamwriter(destination, get)
    elif isinstance(destination, socket.socket):
        await writer_socket(destination, get)
    elif hasattr(destination, 'write'):
        await writer_filelike(destination, get)
    else:
        raise ValueError(f"Unsupported destination type: {type(destination)}")


async def tasks(*coros: Coroutine) -> list[Any]:
    """Runs multiple coroutines concurrently and returns their results."""
    tasks: list[Any] = []
    async with TaskGroup() as group:
        for coro in coros:
            tasks.append(group.create_task(coro))
    results = [task.result() for task in tasks]
    return results
