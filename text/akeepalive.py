#!/usr/bin/env python3
""" akeepalive: Async Keepalive Generator """

import sys
import argparse
import logging
import asyncio
import aiofiles

import ucm

logger = logging.getLogger(__name__)


async def async_keepalive(iterable, timeout, timeout_return=None):
	""" Async Keepalive Generator """

	iterator = aiter(iterable)
	next_item_task = None
	timeout_task = None

	while True:
		if timeout_task is None:
			timeout_task = asyncio.create_task(asyncio.sleep(timeout))
		if next_item_task is None:
			next_item_task = asyncio.create_task(anext(iterator))

		done, _ = await asyncio.wait(
			{next_item_task, timeout_task},
			return_when=asyncio.FIRST_COMPLETED,
		)

		assert len(done) == 1

		task = done.pop()

		if task == timeout_task:
			timeout_task = None
			yield timeout_return
			continue

		assert task == next_item_task

		next_item_task = None
		timeout_task.cancel()
		timeout_task = None

		try:
			yield task.result()
		except StopAsyncIteration:
			break

	for task in next_item_task, timeout_task:
		if task:
			task.cancel()


async def async_keepalive_demo(timeout, timeout_return):
	""" Async Timed Iterator Demo """
	async with aiofiles.open(sys.stdin.fileno(), mode='r') as iterable:
		async_iterable = async_keepalive(iterable, timeout, timeout_return)
		async for item in async_iterable:
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
