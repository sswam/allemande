#!/usr/bin/env python3
""" atimeout: Async Timeout Iterator """

import sys
import argparse
import logging
import asyncio
import aiofiles

import ucm

logger = logging.getLogger(__name__)


async def async_keepalive(iterable, timeout, timeout_return=None):
	""" Async Keepalive Generator """

	iterator = iterable.__aiter__()
	timeout_task = next_item_task = None

	while True:
		if timeout_task is None:
			timeout_task = asyncio.create_task(asyncio.sleep(timeout))
		if next_item_task is None:
			next_item_task = asyncio.create_task(iterator.__anext__())

		done, pending = await asyncio.wait(
			{next_item_task, timeout_task},
			return_when=asyncio.FIRST_COMPLETED,
		)

		if len(done) != 1:
			raise RuntimeError("Unexpected number of completed tasks")

		if next_item_task in done:
			next_item_task = None
			timeout_task.cancel()
			timeout_task = None
		else:
			assert timeout_task in done
			timeout_task = None

		try:
			yield done.pop().result()
		except StopAsyncIteration:
			for task in pending:
				task.cancel()
			break


async def async_keepalive_demo(timeout, timeout_return):
	""" Async Timed Iterator Demo """
	async with aiofiles.open(sys.stdin.fileno(), mode='r') as iterable:
		async_iterable = async_keepalive(iterable, timeout, timeout_return)
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
	asyncio.run(async_keepalive_demo(opts.timeout, opts.timeout_return))


if __name__ == '__main__':
	main()
