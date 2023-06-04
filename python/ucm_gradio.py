import sys
import os
import subprocess
import threading
from functools import partial


""" utilities for running subprocesses in a web interface """


def print_and_flush(*args, file=sys.stdout, **kwargs):
	""" print and flush """
	print(*args, file=file, flush=True, **kwargs)


def print_and_save_stream(stream, lines=None, printer=print, all_lines=None, label=None):
	""" print and save stream """
	for line in iter(stream.readline, ''):
		if lines is not None:
			lines.append(line)
		if all_lines is not None:
			all_lines.append({"label":label, "line":line})
		if printer is not None:
			printer(line, end='')


def run_subprocess(cmd, *args, **kwargs):
	""" run subprocess """
	# set environment variables
	env = os.environ.copy()
	for k, v in kwargs.items():
		env[k] = v

	cmd = [cmd, *args]

	stdout_lines = []
	stderr_lines = []
	all_lines = []

	process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
	thread_out = threading.Thread(
		target=print_and_save_stream,
		args=(process.stdout, stdout_lines, print_and_flush, all_lines, None)
	)
	thread_err = threading.Thread(
		target=print_and_save_stream,
		args=(process.stderr, stderr_lines, partial(print_and_flush, file=sys.stderr), all_lines, "err")
	)
	thread_out.start()
	thread_err.start()
	thread_out.join()
	thread_err.join()
	exit_code = process.wait()
	return exit_code, stdout_lines, stderr_lines, all_lines
