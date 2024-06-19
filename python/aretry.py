import asyncio
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def aretry(fn, n_tries, *args, sleep_min=1, sleep_max=2, bad_errors=None, **kwargs):
	""" Retry an async function n_tries times. """
	if bad_errors is None:
		bad_errors = []
	for i in range(n_tries):
		try:
			return await fn(*args, **kwargs)
		except Exception as ex:  # pylint: disable=broad-except
			delay = random.uniform(sleep_min, sleep_max)
			logger.warning("retry: exception, sleeping for %.3f: %s", delay, ex)
			msg = str(ex)
			bad = any(bad_error in msg for bad_error in bad_errors)
			if bad or i == n_tries - 1:
				raise
			await asyncio.sleep(delay)
			sleep_min *= 2
			sleep_max *= 2
	return None

fails = 3

async def failafew():
	global fails
	if fails:
		fails -= 1
		raise Exception("failed")
	return 100

async def test():
	print(await aretry(failafew, 4, sleep_min=0.1, sleep_max=0.2))

if __name__ == "__main__":
	asyncio.run(test())
