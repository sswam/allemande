import asyncio
import os
from ally.aio import read, write, collect_bytes, collect_text

async def test_file_read():
    print("\nTesting file read...")
    get = await read("/etc/passwd")
    content = await collect_bytes(get)
    print(f"Read {len(content)} characters from /etc/passwd")
    print(content[:100])  # Print first 100 characters

async def test_file_write():
    print("\nTesting file write...")
    put = await write("/tmp/test_output.txt")
    test_data = b"Hello, this is a test file written by the library."
    await put(test_data)
    await put(None)  # Close the file
    print(f"Wrote {len(test_data)} bytes to /tmp/test_output.txt")

    # Verify the write
    get = await read("/tmp/test_output.txt")
    content = await collect_bytes(get)
    print(f"Verified content ({len(content)} bytes): {content.decode()}")

async def test_http_get():
    print("Testing HTTP GET...")
    url = "https://allemande.ai/epic.html"
    get = await read(url)
    content = b""
    while (chunk := await get()) is not None:
        content += chunk
        print(f"Read {len(chunk)} bytes from {url}")
    print(f"Fetched {len(content)} bytes from {url}")
    print(content[:100])  # Print first 100 bytes

async def test_http_put_post():
    print("\nTesting HTTP PUT...")
    url = "https://allemande.ai/put"
    put = await write(url, method="PUT")
    test_data = b"This is a PUT request test."
    await put(test_data)
    await put(None)  # Finalize the request
    print(f"Sent {len(test_data)} bytes via PUT to {url}")

    print("\nTesting HTTP POST...")
    post = await write(url, method="POST")
    test_data = b"This is a POST request test."
    await post(test_data)
    await post(None)  # Finalize the request
    print(f"Sent {len(test_data)} bytes via POST to {url}")

async def main():
    try:
        await test_file_read()
        await test_file_write()
        await test_http_get()
        await test_http_put_post()
    except Exception as e:
        print(f"An error occurred: {e}")
        raise e
    finally:
        # Clean up the test file
        if os.path.exists("/tmp/test_output.txt"):
            os.remove("/tmp/test_output.txt")
            print("\nCleaned up test file.")

if __name__ == "__main__":
    asyncio.run(main())
