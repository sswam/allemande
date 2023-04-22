
class AsyncKeepalive:
	"""Async Keepalive Iterator"""

	def __init__(self, iterable, timeout=1, timeout_return=None):
		self._iterator = iterable.__aiter__()
		self.timeout = timeout
		self.timeout_return = timeout_return
		self._timeout_task = None
		self._next_item_task = None

	def __aiter__(self):
		return self

	async def _wait_timeout(self):
		await asyncio.sleep(self.timeout)
		return self.timeout_return

	async def __anext__(self):
		"""Async Timed Iterator Async Next"""

		if not self._timeout_task:
			self._timeout_task = asyncio.create_task(self._wait_timeout())

		if not self._next_item_task:
			self._next_item_task = asyncio.create_task(self._iterator.__anext__())

		done, pending = await asyncio.wait(
			{ self._next_item_task, self._timeout_task },
			return_when=asyncio.FIRST_COMPLETED
		)

		if len(done) != 1:
			raise RuntimeError("Unexpected number of completed tasks")

		if self._next_item_task in done:
			self._next_item_task = None
			self._timeout_task.cancel()
			self._timeout_task = None
		else:
			assert self._timeout_task in done
			self._timeout_task = None

		try:
			return done.pop().result()
		except StopAsyncIteration:
			for task in pending:
				task.cancel()
			self._next_item_task = None
			self._timeout_task = None
			raise


async def async_timed_iterator_demo(timeout, timeout_return):
	""" Async Timed Iterator Demo """
	async with aiofiles.open(sys.stdin.fileno(), mode='r') as iterable:
#		async_iterable = async_timeout_iterator(iterable, timeout, timeout_return)
		async_iterable = AsyncTimedIterator(iterable, timeout, timeout_return)
		async for item in async_iterable:
			if item is None:
				print("Timeout")
			else:
				print(item, end='')


def get_opts():
	""" Get command line options """
	parser = argparse.ArgumentParser(description="atimeout", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-t', '--timeout', type=float, default=1, help="Timeout value in seconds")
	parser.add_argument('-r', '--timeout-return', default=None, help="Value to return on timeout")
	ucm.add_logging_options(parser)
	opts = parser.parse_args()
	return opts


def main():
	""" Main function """
	opts = get_opts()
	ucm.setup_logging(opts)
	asyncio.run(async_timed_iterator_demo(opts.timeout, opts.timeout_return))


if __name__ == '__main__':
	main()

