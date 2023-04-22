#!/usr/bin/env python3
""" akeepalive: Async Keepalive Generator """

import sys
import argparse
import logging
import asyncio
import aiofiles

import ucm

logger = logging.getLogger(__name__)


class AsyncKeepalive:
	""" Async Keepalive Generator """

	def __init__(self, iterable, timeout, timeout_return=None):
		""" Initialize the Async Keepalive Generator """
		self.iterator = aiter(iterable)
		self.timeout = timeout
		self.timeout_return = timeout_return
		self.next_item_task = None
		self.timeout_task = None

	async def run(self):
		""" Run the Async Keepalive Generator """

		try:
			while True:
				async for item in self.step():
					yield item
		except StopAsyncIteration:
			pass

		for task in self.next_item_task, self.timeout_task:
			if task:
				task.cancel()

	async def step(self):
		""" Step the Async Keepalive Generator """

		if self.timeout_task is None:
			self.timeout_task = asyncio.create_task(asyncio.sleep(self.timeout))
		if self.next_item_task is None:
			self.next_item_task = asyncio.create_task(anext(self.iterator))

		done, _ = await asyncio.wait(
			{ self.next_item_task,  self.timeout_task },
			return_when=asyncio.FIRST_COMPLETED,
		)

		assert len(done) == 1

		task = done.pop()

		if task == self.timeout_task:
			self.timeout_task = None
			yield self.timeout_return
		else:
			assert task == self.next_item_task

			self.next_item_task = None
			self.timeout_task.cancel()
			self.timeout_task = None

			yield task.result()


async def async_keepalive_demo(timeout, timeout_return):
	""" Async Timed Iterator Demo """
	async with aiofiles.open(sys.stdin.fileno(), mode='r') as iterable:
		keepalive = AsyncKeepalive(iterable, timeout, timeout_return)
		async for item in keepalive.run():
			print(item, end='', flush=True)


def get_opts():
	""" Get command line options """
	parser = argparse.ArgumentParser(description="atimeout", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-t', '--timeout', type=float, default=1, help="Timeout value in seconds")
	parser.add_argument('-r', '--timeout-return', default=".", help="Value to return on timeout")
	ucm.add_logging_options(parser)
	opts = parser.parse_args()
	return opts


def main():
	""" Main function """
	opts = get_opts()
	ucm.setup_logging(opts)
	asyncio.run(async_keepalive_demo(opts.timeout, opts.timeout_return))


if __name__ == '__main__':
	main()
