
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


