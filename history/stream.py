
async def follow_poll(file, sleep=FOLLOW_SLEEP, keepalive=FOLLOW_KEEPALIVE, keepalive_string="\n"):
	time_since_send = 0
	async with aiofiles.open(file, mode='r') as f:
		while True:
			while line := await f.readline():
				logger.info(f"sending line: {line}")
				yield line
				time_since_send = 0
			await asyncio.sleep(sleep)
			time_since_send += sleep
			if keepalive and time_since_send > keepalive:
				logger.info(f"sending keepalive: {keepalive_string}")
				yield keepalive_string
				time_since_send = 0

