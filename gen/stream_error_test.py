import os
import signal
import sys
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import asyncio
import aiohttp

async def connect_and_disconnect(url, disconnect_after=0.5):
    """Connect to stream and disconnect after specified time"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # Start reading the stream
                async for line in response.content:
                    print(f"Received: {line.decode().strip()}")
                    await asyncio.sleep(random.uniform(0.1, 0.2))
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
        disconnect_time = 1.2 + random.uniform(0, 1)
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

async def file_updater(filename):
    """Continuously update the test file"""
    counter = 0
    while True:
        with open(filename, 'a') as f:
            f.write(f"Line {counter}\n")
            counter += 1
        await asyncio.sleep(random.uniform(0.1, 0.2))

async def main():
    base_url = "http://localhost:8001"  # Adjust to your server's address

    # Add to main():
    test_file = str(Path(os.environ["ALLEMANDE_ROOMS"])/'test.html')
    asyncio.create_task(file_updater(test_file))

    while True:
        print("\nStarting chaos test...")
        await chaos_test(base_url)
        await asyncio.sleep(1)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())
