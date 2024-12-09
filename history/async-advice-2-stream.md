Looking at your code and the errors, let me break down the main issues and suggest solutions:

1. First Error: "Task was destroyed but it is pending!"
This is happening in your streaming setup, likely because the tasks created by `atail` and `akeepalive` aren't being properly cleaned up when a client disconnects.

Solution: Implement proper cleanup in your `follow` function:

```python
async def follow(file, head="", keepalive=FOLLOW_KEEPALIVE, keepalive_string="\n"):
    """Follow a file and yield new lines as they are added."""
    try:
        if head:
            yield head

        tail = atail.AsyncTail(
            filename=file, wait_for_create=True, all_lines=True, follow=True, rewind=True
        ).run()
        tail2 = akeepalive.AsyncKeepAlive(tail, keepalive, timeout_return=keepalive_string).run()

        async for line in tail2:
            yield line
    finally:
        # Ensure cleanup of generators
        if 'tail2' in locals():
            await tail2.aclose()
        if 'tail' in locals():
            await tail.aclose()
```

2. Second Error: "aclose(): asynchronous generator is already running"
This suggests that you're trying to close an async generator while it's still running. This commonly happens when multiple clients are trying to access the same generator instance.

You should modify your `AsyncTail` class to handle cleanup better:

```python
class AsyncTail:
    def __init__(self, ...):
        self.watcher = None
        self._running = False
        # ... rest of your init code ...

    async def run(self):
        if self._running:
            raise RuntimeError("AsyncTail is already running")
        self._running = True
        try:
            async with aiofiles.open(self.filename, mode='r') as f:
                # ... your existing code ...
        finally:
            self._running = False
            if self.watcher:
                self.close_watcher(self.watcher)

    def close_watcher(self, watcher):
        if watcher:
            try:
                watcher.close()
                self.watcher = None
            except Exception as e:
                logger.warning("Exception closing watcher: %r", e)
```

3. Add proper error handling in your stream endpoint:

```python
@app.route("/stream/{path:path}", methods=["GET"])
async def stream(request):
    try:
        path = request.path_params["path"]
        path = chat.sanitize_pathname(path)
        path = Path(path)
        safe_path = chat.safe_join(BASE_DIR, path)

        media_type = "text/plain"
        head = ""
        keepalive_string = "\n"

        ext = safe_path.suffix

        if ext == ".html":
            media_type = "text/html"
            user = request.headers.get("X-Forwarded-User", "guest")
            if templates:
                context = {"request": request, "user": user}
                head = templates.get_template("room-head.html").render(context)
            keepalive_string = HTML_KEEPALIVE

        logger.info("tail: %s", safe_path)
        follower = follow(str(safe_path), head=head, keepalive_string=keepalive_string)

        response = StreamingResponse(follower, media_type=media_type)
        response.background = asyncio.create_task(handle_client_disconnect(request))
        return response
    except Exception as e:
        logger.error(f"Stream error: {e}", exc_info=True)
        raise

async def handle_client_disconnect(request):
    try:
        await request.is_disconnected()
    finally:
        # Cleanup code here
        logger.info("Client disconnected")
```

4. Add a context manager to your AsyncKeepAlive class:

```python
class AsyncKeepAlive:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup code
        pass
```

The key issues here are:
1. Tasks not being properly cleaned up when clients disconnect
2. Async generators being reused or not properly closed
3. Lack of proper error handling and resource cleanup

The solutions involve:
1. Implementing proper cleanup in finally blocks
2. Adding proper state management to prevent reuse of running generators
3. Adding proper error handling
4. Implementing context managers for better resource management
5. Adding client disconnect detection and cleanup

This should resolve the errors you're seeing while making your code more robust.
