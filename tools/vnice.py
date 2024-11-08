#!/usr/bin/env python3-allemande

import time
import os
import sys
import psutil
import argh
from argh import arg
import subprocess
import heapq
import logging


""" vnice.py: A script to adjust the activity of a process by stopping and starting it. """


logger = logging.getLogger(__name__)

# set info level





def stop(pid):
	""" Stop a process by sending it a SIGSTOP signal. """
	try:
		psutil.Process(pid).suspend()
	except psutil.NoSuchProcess:
		logger.info(f'Process {pid} has exited.')


def cont(pid):
	""" Continue a process by sending it a SIGCONT signal. """
	try:
		psutil.Process(pid).resume()
	except psutil.NoSuchProcess:
		logger.info(f'Process {pid} has exited.')


@arg('pids_or_command', nargs='*', help='Process ID of the target program or command to run.')
@arg('--active', '-a', default=0.1, help='Duration (in seconds) the target program should work.')
@arg('--sleep', '-s', default=0.1, help='Duration (in seconds) the target program should sleep.')
@arg('--command', '-c', action='store_true', help='Run and vnice a new command.')
def vnice(*pid_or_command, active_duration=0.1, sleep_duration=0.1, command=False):
	"""
	Adjust a running process' activity and sleep periods.

	Example usage:
	python vnice.py -a 1 -s 1 1234
	python vnice.py -a 1 -s 1 -c my_program --arg value
	"""

	if command:
		cmd = pids_or_command
		proc = subprocess.Popen(*cmd)
		pids = [proc.pid]
	else:
		pids = map(int, pids_or_command)

	heap = []

	now = time.time()
	spread = active_duration / len(pids)
	for i, pid in enumerate(pids):
		t = now + i * spread
		heapq.heappush(heap, (t, pid, 'stop'))

	while heap:
		t, pid, action = heapq.heappop(heap)
		time.sleep(t - time.time())

		# if process has exited, we do not add another event to the heap
		if not psutil.pid_exists(pid):
			logger.info(f'Process {pid} has exited.')
		elif action == 'stop':
			logger.info(f'Stopping process {pid}')
			stop(pid)
			heapq.heappush(heap, (t + sleep_duration, pid, 'cont'))
		else:
			logger.info(f'Continuing process {pid}')
			cont(pid)
			heapq.heappush(heap, (t + active_duration, pid, 'stop'))


if __name__ == '__main__':
	argh.dispatch_command(vnice)
