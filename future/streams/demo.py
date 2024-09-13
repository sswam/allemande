import sys
import asyncio
import aiofiles


EOF = object()  # Sentinel object to signal end of queue


async def producer(queue):
    for i in range(5):
        await queue.put(f'event {i}')
        await asyncio.sleep(1)  # Mocking I/O work


async def reader(stream_reader, queue):
    while True:
        line = await stream_reader.readline()
        if not line:  # EOF reached
            await queue.put(EOF)
            break
        await queue.put(line.decode().strip())


async def stdin_reader(queue):
    loop = asyncio.get_event_loop()
    stream_reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(stream_reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    await reader(stream_reader, queue)


async def writer(stream_writer, queue):
    while True:
        data = await queue.get()
        if data is None:  # Use None as a signal to stop
            break
        stream_writer.write(data.encode())
        await stream_writer.drain()


async def stdout_writer(queue):
    loop = asyncio.get_event_loop()
    stream_writer = asyncio.StreamWriter(sys.stdout, None, None, loop)
    await writer(stream_writer, queue)


async def socket_reader(host, port, queue):
    stream_reader, _ = await asyncio.open_connection(host, port)
    await reader(stream_reader, queue)


async def socket_writer(host, port, queue):
    reader, writer = await asyncio.open_connection(host, port)
    try:
        while True:
            data = await queue.get()
            if data is None:  # Use None as a signal to stop
                break
            writer.write(data.encode())
            await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def socket_reader_writer(host, port, read_queue, write_queue):
    reader, writer = await asyncio.open_connection(host, port)
    try:
        read_task = asyncio.create_task(reader_loop(reader, read_queue))
        write_task = asyncio.create_task(writer_loop(writer, write_queue))
        await asyncio.gather(read_task, write_task)
    finally:
        writer.close()
        await writer.wait_closed()


async def reader_loop(reader, queue):
    while True:
        data = await reader.readline()
        if not data:
            break
        await queue.put(data.decode().strip())


async def writer_loop(writer, queue):
    while True:
        data = await queue.get()
        if data is None:
            break
        writer.write(data.encode())
        await writer.drain()


Here are additional functions to read, write, or read/write on any existing file handle using its UNIX file number:

import os
import fcntl

def get_file_handle(file_descriptor):
    return os.fdopen(file_descriptor, 'rb+', buffering=0)

async def file_reader(file_descriptor, queue):
    file_handle = get_file_handle(file_descriptor)
    fcntl.fcntl(file_handle, fcntl.F_SETFL, os.O_NONBLOCK)
    loop = asyncio.get_event_loop()
    stream_reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(stream_reader)
    await loop.connect_read_pipe(lambda: protocol, file_handle)
    await reader(stream_reader, queue)

async def file_writer(file_descriptor, queue):
    file_handle = get_file_handle(file_descriptor)
    loop = asyncio.get_event_loop()
    stream_writer = asyncio.StreamWriter(file_handle, None, None, loop)
    await writer(stream_writer, queue)

async def file_reader_writer(file_descriptor, read_queue, write_queue):
    file_handle = get_file_handle(file_descriptor)
    fcntl.fcntl(file_handle, fcntl.F_SETFL, os.O_NONBLOCK)
    loop = asyncio.get_event_loop()
    stream_reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(stream_reader)
    transport, _ = await loop.connect_read_pipe(lambda: protocol, file_handle)
    stream_writer = asyncio.StreamWriter(transport, protocol, stream_reader, loop)
    read_task = asyncio.create_task(reader(stream_reader, read_queue))
    write_task = asyncio.create_task(writer(stream_writer, write_queue))
    await asyncio.gather(read_task, write_task)


# Usage
async def main():
    read_queue = asyncio.Queue()
    write_queue = asyncio.Queue()
    
    task = asyncio.create_task(socket_reader_writer('localhost', 8888, read_queue, write_queue))
    
    # Write some data
    await write_queue.put("Hello, server!")
    await write_queue.put("How are you?")
    
    # Read responses
    for _ in range(2):
        response = await read_queue.get()
        print(f"Received: {response}")
    
    # Signal to stop writing
    await write_queue.put(None)
    
    await task

asyncio.run(main())
```

4. Working with arbitrary file handles:

```python
import asyncio
import os

async def file_reader(fd, queue):
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, os.fdopen(fd, 'rb'))
    
    while True:
        line = await reader.readline()
        if not line:
            break
        await queue.put(line.decode().strip())

async def file_writer(fd, queue):
    loop = asyncio.get_event_loop()
    transport, protocol = await loop.connect_write_pipe(asyncio.Protocol, os.fdopen(fd, 'wb'))
    
    while True:
        data = await queue.get()
        if data is None:
            break
        transport.write(data.encode() + b'\n')
    
    transport.close()

# Usage
async def main():
    read_fd, write_fd = os.pipe()
    
    read_queue = asyncio.Queue()
    write_queue = asyncio.Queue()
    
    reader_task = asyncio.create_task(file_reader(read_fd, read_queue))
    writer_task = asyncio.create_task(file_writer(write_fd, write_queue))
    
    # Write some data
    await write_queue.put("Hello, pipe!")
    await write_queue.put("This is a test.")
    
    # Read the data
    for _ in range(2):
        data = await read_queue.get()
        print(f"Read: {data}")
    
    # Signal to stop writing
    await write_queue.put(None)
    
    await asyncio.gather(reader_task, writer_task)
    
    os.close(read_fd)
    os.close(write_fd)

asyncio.run(main())
```

These examples demonstrate how to perform asynchronous I/O operations with stdout, sockets, and arbitrary file handles. The socket example shows both reading and writing, and the file handle example uses a pipe to demonstrate both reading and writing to file descriptors.

Remember that when working with sockets or file handles, it's important to properly close the resources when you're done with them to avoid resource leaks.


# Usage
async def main():
    read_queue = asyncio.Queue()
    write_queue = asyncio.Queue()
    
    task = asyncio.create_task(socket_reader_writer('localhost', 8888, read_queue, write_queue))
    
    # Write some data
    await write_queue.put("Hello, server!")
    await write_queue.put("How are you?")
    
    # Read responses
    for _ in range(2):
        response = await read_queue.get()
        print(f"Received: {response}")
    
    # Signal to stop writing
    await write_queue.put(None)
    
    await task

asyncio.run(main())
```

4. Working with arbitrary file handles:

```python
import asyncio
import os

async def file_reader(fd, queue):
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, os.fdopen(fd, 'rb'))
    
    while True:
        line = await reader.readline()
        if not line:
            break
        await queue.put(line.decode().strip())

async def file_writer(fd, queue):
    loop = asyncio.get_event_loop()
    transport, protocol = await loop.connect_write_pipe(asyncio.Protocol, os.fdopen(fd, 'wb'))
    
    while True:
        data = await queue.get()
        if data is None:
            break
        transport.write(data.encode() + b'\n')
    
    transport.close()

# Usage
async def main():
    read_fd, write_fd = os.pipe()
    
    read_queue = asyncio.Queue()
    write_queue = asyncio.Queue()
    
    reader_task = asyncio.create_task(file_reader(read_fd, read_queue))
    writer_task = asyncio.create_task(file_writer(write_fd, write_queue))
    
    # Write some data
    await write_queue.put("Hello, pipe!")
    await write_queue.put("This is a test.")
    
    # Read the data
    for _ in range(2):
        data = await read_queue.get()
        print(f"Read: {data}")
    
    # Signal to stop writing
    await write_queue.put(None)
    
    await asyncio.gather(reader_task, writer_task)
    
    os.close(read_fd)
    os.close(write_fd)

asyncio.run(main())
```

These examples demonstrate how to perform asynchronous I/O operations with stdout, sockets, and arbitrary file handles. The socket example shows both reading and writing, and the file handle example uses a pipe to demonstrate both reading and writing to file descriptors.

Remember that when working with sockets or file handles, it's important to properly close the resources when you're done with them to avoid resource leaks.



async def main():
    queue = asyncio.Queue()
    
    # For stdin:
    asyncio.create_task(stdin_reader(queue))
    
    # For a socket:
    # asyncio.create_task(socket_reader('localhost', 8888, queue))
    
    while True:
        item = await queue.get()
        if item is EOF:
            break
        print(f"Received: {item}")

if __name__ == "__main__":
    asyncio.run(main())
```

This approach allows you to read asynchronously from stdin or a socket, putting each line into a queue for further processing. The `EOF` sentinel object is used to signal when the stream has ended.

Remember that for real-world applications, you might need to add error handling and possibly adjust the buffering behavior depending on your specific requirements.


async def reader(file_path, queue):
    async with aiofiles.open(file_path, mode='r') as f:
        async for line in f:
            await queue.put(line)
    await queue.put(EOF)

async def writer(file_path, queue, mode='w'):
    async with aiofiles.open(file_path, mode=mode) as f:
        while True:
            block = await queue.get()
            if block is EOF:
                # queue.task_done()
                break
            await f.write(block)
            queue.task_done()

async def processor(queue):
    while True:
        item = await queue.get()
        if item is EOF:
            queue.task_done()
            break
        print(f'Processed {item.rstrip()}')
        queue.task_done()

async def main():
    queue = asyncio.Queue()
    producer_task = asyncio.create_task(reader("./demo.py", queue))
    processor_task = asyncio.create_task(processor(queue))

    await asyncio.gather(producer_task)
    await queue.join()

    processor_task.cancel()

asyncio.run(main())

