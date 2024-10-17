import sys
import asyncio
import aiofiles  # type: ignore
from typing import Any, Callable, Coroutine, AsyncGenerator, TypeVar, TextIO, cast
from urllib.parse import urlparse
import io
import socket

import asyncio
import aiohttp

import logging

__version__ = '0.1.8'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

T = TypeVar('T')
Get = Callable[[], Coroutine[None, None, T | None]]
Put = Callable[[T | None], Coroutine[None, None, None]]
Talk = Callable[[T | None], Coroutine[None, None, T | None]]

class Absent():
    """A class representing an absent value."""
    def __repr__(self):
        return 'Absent'

absent = Absent()

chunk_size = 8192


# Utility functions

async def tasks(*coros: Coroutine) -> list[Any]:
    """Runs multiple coroutines concurrently and returns their results."""
    tasks_list: list[Any] = []
    async with asyncio.TaskGroup() as group:
        for coro in coros:
            tasks_list.append(group.create_task(coro))
    results = [task.result() for task in tasks_list]
    return results


async def collect_bytes(get: Get[bytes]) -> bytes:
    buffer = io.BytesIO()
    while (item := await get()) is not None:
        buffer.write(item)
    return buffer.getvalue()


async def collect_text(get: Get[str]) -> str:
    buffer = io.StringIO()
    while (item := await get()) is not None:
        buffer.write(item)
    return buffer.getvalue()


# Reader implementations

async def read_file(source: str) -> Get[bytes]:
    """Returns a get() function for reading from a file."""
    file = await aiofiles.open(source, 'rb')

    async def get() -> bytes | None:
        nonlocal file
        if file is None:
            return None
        chunk = await file.read(chunk_size)
        if not chunk:
            await file.close()
            file = None
            return None
        return chunk

    return get


def validate_http_method_for_reading(method: str) -> None:
    """Raises an error if the given HTTP method is not supported for reading."""
    if method not in ('GET', 'HEAD'):
        raise ValueError(f"Unsupported HTTP method for reading: {method}")


# TODO we need the option to include headers


async def read_http(source: str, method: str = 'GET') -> Get[bytes]:
    """Returns a get() function for reading from an HTTP/S URL."""
    validate_http_method_for_reading(method)
    session: aiohttp.ClientSession | None = aiohttp.ClientSession()
    response: aiohttp.ClientResponse | None = None

    async def close() -> None:
        nonlocal response, session
        if response:
            await response.release()
            response = None
        if session:
            await session.close()
            session = None

    async def get() -> bytes | None:
        nonlocal response
        if not session:
            return None
        try:
            if not response:
                response = await session.request(method, source)
            chunk = await response.content.read(chunk_size)
            if not chunk:
                await close()
                return None
            return chunk
        except Exception as e:
            await close()
            raise e

    return get


async def read_streamreader(source: asyncio.StreamReader | None) -> Get[bytes]:
    """Returns a get() function for reading from a StreamReader."""
    src: asyncio.StreamReader | None = source
    async def get() -> bytes | None:
        nonlocal src
        if not src:
            return None
        chunk = await src.read(chunk_size)
        if not chunk:
            src = None
            return None
        return chunk

    return get


async def read_socket(sock: socket.socket) -> Get[bytes]:
    """Returns a get() function for reading from a socket."""
    sock.setblocking(False)
    sck: socket.socket | None = sock
    loop = asyncio.get_running_loop()

    async def get() -> bytes | None:
        nonlocal sck
        if not sck:
            return None
        chunk = await loop.sock_recv(sck, chunk_size)
        if not chunk:
            sck.close()
            sck = None
            return None
        return chunk

    return get


async def talk_socket(sock: socket.socket) -> Talk[bytes]:
    """Returns an talk() function for reading and writing to a socket."""
    sock.setblocking(False)
    sck: socket.socket | None = sock
    loop = asyncio.get_running_loop()

    readable = True
    writable = True

    async def talk(data: bytes | None | Absent = absent) -> bytes | None:
        nonlocal sck, readable, writable

        if sck is None:
            raise ValueError("Socket is closed.")

        # Closing the socket for writing
        if data is None:
            sck.shutdown(socket.SHUT_WR)
            writable = False
            if not readable:
                sck.close()
                sck = None
            return None

        # Writing data to the socket
        if isinstance(data, bytes):
            await loop.sock_sendall(sck, data)
            return None

        # Reading data from the socket
        if data is absent:
            chunk = await loop.sock_recv(sck, chunk_size)
            if not chunk:
                readable = False
                if not writable:
                    sck.close()
                    sck = None
                return None
            return chunk

        raise ValueError("Invalid data type for socket talk.")

    return talk


async def read_istream(istream: TextIO = sys.stdin) -> Get[bytes]:
    """Returns a get() function for reading from an input stream."""
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, istream)
    return await read_streamreader(reader)


async def talk_stream(stream: TextIO) -> Talk[bytes]:
    """Returns an io() function for reading and writing to a stream."""
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, stream)
    writer_transport, writer_protocol = await loop.connect_write_pipe(lambda: asyncio.StreamReaderProtocol(asyncio.StreamReader()), stream)
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, None, loop)
    strm: TextIO | None = stream

    readable = True
    writable = True

    async def talk(data: bytes | None | Absent = absent) -> bytes | None:
        nonlocal strm, reader, writer, readable, writable
        if strm is None:
            raise ValueError("Stream is closed.")
        if data is None:
            writable = False
            if not readable:
                strm.close()
                strm = None
            return None

        if isinstance(data, bytes):
            writer.write(data)
            await writer.drain()
            return None

        if data is absent:
            chunk = await reader.read(chunk_size)
            if not chunk:
                readable = False
                if not writable:
                    strm.close()
                    strm = None
                return None
            return chunk

        raise ValueError("Invalid data type for stream talk.")

    return talk


async def read_bytesio(data: io.BytesIO) -> Get[bytes]:
    """Returns a get() function for reading from a BytesIO object."""
    data.seek(0)

    async def get() -> bytes | None:
        chunk = data.read(chunk_size)
        if not chunk:
            return None
        return chunk

    return get


async def read_bytes(data: bytes) -> Get[bytes]:
    """Returns a get() function for reading from a bytes object."""
    buffer = io.BytesIO(data)
    return await read_bytesio(buffer)


async def read_list(lst: list[bytes]) -> Get[bytes]:
    """Returns a get() function for reading from a list."""
    index: int = 0

    async def get() -> bytes | None:
        nonlocal index
        if index >= len(lst):
            return None
        chunk = lst[index]
        index += 1
        return chunk

    return get


# Writer implementations

async def write_file(destination: str, mode: str = 'wb') -> Put[bytes]:
    """Returns a put() function for writing to a file."""
    file = await aiofiles.open(destination, mode)

    async def put(data: bytes | None) -> None:
        nonlocal file
        if file is None:
            raise ValueError("File is closed.")
        if data is None:
            await file.close()
            file = None
            return
        await file.write(data)

    return put


def validate_http_method_for_writing(method: str) -> None:
    """Raises an error if the given HTTP method is not supported for writing."""
    if method not in ('PUT', 'POST', 'PATCH', 'DELETE'):
        raise ValueError(f"Unsupported HTTP method for writing: {method}")


async def execute_http_request(session, method: str, url: str, data):
    """Executes an HTTP request with the given method, URL, and data."""
    async with session.request(method, url, data=data) as response:
        response.raise_for_status()
        # TODO we need to handle the response headers
        # TODO stream the response content
        return response


async def select(*coros: Coroutine) -> list[Any]:
    """Runs multiple coroutines concurrently and returns the first result, cancelling the others."""
    tasks_list: list[Any] = []
    async with asyncio.TaskGroup() as group:
        for coro in coros:
            tasks_list.append(group.create_task(coro))
        done, pending = await asyncio.wait(tasks_list, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()

    # Return a list with None for non-completed tasks, and the result for the completed task.
    results = [task.result() if task in done else None for task in tasks_list]

    return results


async def talk_http_stream(url: str, method: str = 'PUT') -> Talk[bytes]:
    """Returns a talk() function for streaming to an HTTP/S URL."""
    method = method.upper()
    validate_http_method_for_writing(method)
    queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    que: asyncio.Queue[bytes | None] | None = queue
    response_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    exception_queue: asyncio.Queue[Exception] = asyncio.Queue()

    async def talk(data: bytes | None | Absent = absent) -> bytes | None:
        nonlocal que

        # Check for any exceptions from the background task
        try:
            exception = exception_queue.get_nowait()
            if exception:
                exception_queue.task_done()
                raise exception
        except asyncio.QueueEmpty:
            pass

        # closing the request
        if data is None:
            if que is None:
                raise ValueError("Stream is closed.")
            if que is not None:
                await que.put(None)
                que = None
            return None

        # writing the request
        if isinstance(data, bytes):
            if que is None:
                raise ValueError("Stream is closed.")
            await que.put(data)
            return None

        # reading the response
        if data is absent:
            chunk, exception = await select(response_queue.get(), exception_queue.get())
            if exception:
                exception_queue.task_done()
                raise exception
            response_queue.task_done()
            if chunk:
                return chunk
            await response.release()
            response = None
            return None

        raise ValueError("Invalid data type for HTTP talk.")

    async def data_generator() -> AsyncGenerator[bytes, None]:
        nonlocal que
        try:
            while True:
                if que is None:
                    break
                chunk = await que.get()
                que.task_done()
                if chunk is None:
                    break
                yield chunk
        except Exception as e:
            que.task_done()
            que.close()
            que = None
            await exception_queue.put(e)
            raise

    async def http_request():
        nonlocal que
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, data=data_generator()) as resp:
                    resp.raise_for_status()
                    chunk = await response.content.read(chunk_size)
                    await response_queue.put(chunk)
        except Exception as e:
            que = None
            await exception_queue.put(e)
        finally:
            # Ensure the queue is closed even if an exception occurs
            if que is not None:
                await que.put(None)

    asyncio.create_task(http_request())

    return talk


async def talk_http_whole(url: str, method: str = 'PUT') -> Talk[bytes]:
    """Returns a put() function for writing the whole data to an HTTP/S URL."""
    validate_http_method_for_writing(method)
    buffer: io.BytesIO | None = io.BytesIO()

    async def talk(data: bytes | None | Absent = None) -> bytes | None:
        nonlocal buffer
        if buffer is None:
            raise ValueError("Stream is closed.")

        # collect the data into the buffer
        if isinstance(data, bytes):
            buffer.write(data)
            return None

        # send and close the request, and return the response content
        if data is None:
            data = buffer.getvalue()
            buffer.close()
            buffer = None
            async with aiohttp.ClientSession() as session:
                response = await execute_http_request(session, method, url, data)
                content = await response.read()
                return content

        raise ValueError("Invalid data type for HTTP talk.")

    # TODO could stream request / response but not stream the other

    return talk


def http_method_from_mode(mode: str, method: str | None) -> str:
    """Returns the HTTP method based on the mode and the given method."""
    if method:
        return method
    if mode[0] == 'r':
        return 'GET'
    if mode[0] == 'w':
        return 'PUT'
    if mode[0] == 'a':
        return 'POST'
    else:
        raise ValueError(f"Unsupported mode for HTTP/S URL: {mode}")


async def talk_http(url: str, mode: str = 'wb', method: str | None = None, stream: bool = True) -> Talk[bytes]:
    """Returns an talk() function for reading and writing to an HTTP/S URL."""
    method = http_method_from_mode(mode, method)
    if stream:
        return await talk_http_stream(url, method)
    else:
        return await talk_http_whole(url, method)


async def write_http(destination: str, mode: str = 'wb', method: str | None = None, stream: bool = True) -> Put[bytes]:
    """Returns a put() function for writing to an HTTP/S URL."""
    talk = await talk_http(destination, mode, method, stream)

    async def put(data: bytes | None) -> None:
        await talk(data)
        if data is None:
            while (chunk := await talk()) is not None:
                pass

    return put


async def write_streamwriter(destination: asyncio.StreamWriter) -> Put[bytes]:
    """Returns a put() function for writing to a StreamWriter."""
    dest: asyncio.StreamWriter | None = destination
    async def put(data: bytes | None) -> None:
        nonlocal dest
        if dest is None:
            raise ValueError("Stream is closed.")
        if data is not None:
            dest.write(data)
            await dest.drain()
            return
        dest.close()
        await dest.wait_closed()
        dest = None
    return put


async def write_socket(sock: socket.socket) -> Put[bytes]:
    """Returns a put() function for writing to a socket."""
    sock.setblocking(False)
    sck: socket.socket | None = sock
    async def put(data: bytes | None) -> None:
        nonlocal sck
        if sck is None:
            raise ValueError("Socket is closed.")
        if data is None:
            sck.close()
            sck = None
            return
        while data:
            try:
                sent = await asyncio.to_thread(sck.send, data)
                data = data[sent:]
            except BlockingIOError:
                await asyncio.sleep(0.1)
    return put


async def write_ostream(ostream: TextIO = sys.stdout) -> Put[bytes]:
    """Returns a put() function for writing to an output stream."""
    loop = asyncio.get_event_loop()
    writer_transport, writer_protocol = await loop.connect_write_pipe(lambda: asyncio.StreamReaderProtocol(asyncio.StreamReader()), ostream)
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, None, loop)
    return await write_streamwriter(writer)


async def write_bytesio(data: io.BytesIO, mode: str = 'wb') -> Put[bytes]:
    """Returns a put() function for writing to a BytesIO object."""
    if mode[0] == 'w':
        data.truncate(0)
    async def put(chunk: bytes | None) -> None:
        if chunk is not None:
            data.write(chunk)
    return put


async def write_list(lst: list[bytes], mode: str = 'wb') -> Put[bytes]:
    """Returns a put() function for writing to a list."""
    if mode[0] == 'w':
        lst.clear()
    async def put(chunk: bytes | None) -> None:
        if chunk is not None:
            lst.append(chunk)
    return put


# Main wrapper functions

async def read(source: str | asyncio.StreamReader | socket.socket) -> Get[bytes]:
    """Returns a get() function for reading from various sources."""
    # TODO bytes -> read_bytes, string -> read_string, Path -> read_file, URL -> read_url
    # TODO mode, including binary vs text
    # TODO stream vs whole
    # TODO chunks vs lines
    # TODO rstrip or not
    # TODO filename '-' means stdin/stdout, they can still access a file called '-' using './-' or the file:// scheme
    # TODO do we want sync versions of these functions, or wrappers for them?  generic sync and async wrappers?
    if isinstance(source, str):
        parsed_url = urlparse(source)
        if parsed_url.scheme in ('http', 'https'):
            return await read_http(source)
        if parsed_url.scheme == 'file' or not parsed_url.scheme:
            filename = parsed_url.path if parsed_url.scheme == 'file' else source
            return await read_file(filename)
        raise ValueError(f"Unsupported URL scheme: {parsed_url.scheme}")
    elif isinstance(source, asyncio.StreamReader):
        return await read_streamreader(source)
    elif isinstance(source, socket.socket):
        return await read_socket(source)
    raise ValueError(f"Unsupported source type: {type(source)}")


async def write(destination: str | asyncio.StreamWriter | socket.socket, mode: str = 'wb', method: str = 'PUT') -> Put[bytes]:
    """Returns a put() function for writing to various destinations."""
    if isinstance(destination, str):
        parsed_url = urlparse(destination)
        if parsed_url.scheme in ('http', 'https'):
            return await write_http(destination, method=method)
        elif parsed_url.scheme == 'file' or not parsed_url.scheme:
            filename = parsed_url.path if parsed_url.scheme == 'file' else destination
            return await write_file(filename, mode)
    elif isinstance(destination, asyncio.StreamWriter):
        return await write_streamwriter(destination)
    elif isinstance(destination, socket.socket):
        return await write_socket(destination)
    raise ValueError(f"Unsupported destination type: {type(destination)}")
