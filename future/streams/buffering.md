To reduce IO delays caused by queue buffering, you can:

1. Use `asyncio.Queue(maxsize=1)` to limit the buffer size to 1.
2. Use `asyncio.Queue()` with no `maxsize` argument for an unbounded queue.
3. Use `queue.put_nowait()` instead of `queue.put()` to avoid blocking.
4. Use `queue.get_nowait()` with try/except for non-blocking reads.

These approaches will minimize buffering and allow for more immediate processing of queue items.

