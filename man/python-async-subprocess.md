To run a subprocess asynchronously without blocking the main event loop, you can use the `asyncio.create_subprocess_exec()` function along with `asyncio.subprocess.PIPE` for handling input/output. Here's how you can modify your code to work asynchronously:

```python
import asyncio
import subprocess

async def run_subprocess(command, query):
    # Create the subprocess
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Write to stdin
    proc.stdin.write(query.encode("utf-8"))
    await proc.stdin.drain()
    proc.stdin.close()

    # Read stdout and stderr
    stdout, stderr = await proc.communicate()

    # Get the return code
    return_code = await proc.wait()

    return stdout.decode("utf-8"), stderr.decode("utf-8"), return_code

async def main():
    command = ["your", "command", "here"]
    query = "Your input query"

    output, errors, status = await run_subprocess(command, query)

    print(f"Output: {output}")
    print(f"Errors: {errors}")
    print(f"Status: {status}")

# Run the async function
asyncio.run(main())
```

Key points:

1. We use `asyncio.create_subprocess_exec()` instead of `subprocess.Popen()`.
2. We use `asyncio.subprocess.PIPE` for stdin, stdout, and stderr.
3. Writing to stdin is done with `proc.stdin.write()` followed by `await proc.stdin.drain()` to ensure all data is written.
4. We use `await proc.communicate()` to read both stdout and stderr asynchronously.
5. The return code is obtained with `await proc.wait()`.

This approach allows you to run the subprocess without blocking the main event loop, which is crucial in asynchronous programming.

If you need to run multiple subprocesses concurrently, you can create multiple coroutines and run them with `asyncio.gather()`:

```python
async def main():
    command1 = ["command1"]
    command2 = ["command2"]
    query1 = "query1"
    query2 = "query2"

    task1 = run_subprocess(command1, query1)
    task2 = run_subprocess(command2, query2)

    results = await asyncio.gather(task1, task2)

    for i, (output, errors, status) in enumerate(results, 1):
        print(f"Process {i}:")
        print(f"Output: {output}")
        print(f"Errors: {errors}")
        print(f"Status: {status}")
        print()

asyncio.run(main())
```

This approach allows you to run multiple subprocesses concurrently and efficiently within your asyncio-based application.

