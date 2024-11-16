Here's some test code that should help reliably trigger those exceptions. The key is to simulate clients connecting and disconnecting while streaming is in progress:

```python
import asyncio
import aiohttp
import signal
import sys
from concurrent.futures import ThreadPoolExecutor

async def connect_and_disconnect(url, disconnect_after=0.5):
    """Connect to stream and disconnect after specified time"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # Start reading the stream
                async for line in response.content:
                    print(f"Received: {line.decode().strip()}")
                    await asyncio.sleep(0.1)
                    if disconnect_after <= 0:
                        # Simulate abrupt disconnection
                        return
                    disconnect_after -= 0.1
    except Exception as e:
        print(f"Connection error (expected): {e}")

async def chaos_test(base_url, num_clients=5):
    """Create multiple clients that connect and disconnect at different times"""
    tasks = []
    for i in range(num_clients):
        # Vary disconnect times to create chaos
        disconnect_time = 0.2 + (i * 0.3)
        task = asyncio.create_task(
            connect_and_disconnect(f"{base_url}/stream/test.html", disconnect_time)
        )
        tasks.append(task)

    # Let some tasks complete naturally and cancel others
    await asyncio.sleep(1)
    for task in tasks[::2]:  # Cancel every other task
        if not task.done():
            task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)

def signal_handler(sig, frame):
    print("Ctrl+C detected, exiting...")
    sys.exit(0)

async def main():
    base_url = "http://localhost:8001"  # Adjust to your server's address

    while True:
        print("\nStarting chaos test...")
        await chaos_test(base_url)
        await asyncio.sleep(1)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())
```

To use this test:

1. First make sure your streaming server is running
2. Create a test.html file in your rooms directory
3. Run this script

This test code:
- Creates multiple clients that connect to your stream
- Has them disconnect at different times
- Some disconnect gracefully, others abruptly
- Repeats the process continuously

You can tweak parameters like:
- `num_clients`: Number of simultaneous connections
- `disconnect_after`: How long before disconnecting
- The sleep times between operations

You might also want to add a file writer that continuously updates test.html:

```python
async def file_updater(filename):
    """Continuously update the test file"""
    counter = 0
    while True:
        with open(filename, 'a') as f:
            f.write(f"Line {counter}\n")
            counter += 1
        await asyncio.sleep(0.1)

# Add to main():
asyncio.create_task(file_updater('test.html'))
```

This should reliably trigger the exceptions you're seeing because it:
1. Creates multiple concurrent connections
2. Has clients disconnect at different stages of streaming
3. Includes both graceful and abrupt disconnections
4. Maintains continuous file updates while streaming
