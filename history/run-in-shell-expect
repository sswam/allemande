#!/usr/bin/env python3
""" spawn a child process in an interactive shell """

import sys
import shlex
import pexpect
import time
from functools import partial
import struct, fcntl, termios, signal, sys


SHELL = "/bin/bash"
SHELL_PROMPT_RE = r"[\$\#]\s"


def get_terminal_size():
	""" get the size of the enclosing tty """
	s = struct.pack("HHHH", 0, 0, 0, 0)
	size = struct.unpack('hhhh', fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, s))
	return size


def set_terminal_size(child, rows, cols):
	""" set the size of the tty for the given pexpect child """
	winsize = struct.pack('HHHH', rows, cols, 0, 0)
	fcntl.ioctl(child.fileno(), termios.TIOCSWINSZ, winsize)


def pass_terminal_size_to_child(child, *args):
	""" pass the enclosing terminal size to the child process """
	lines, columns, w, h = get_terminal_size()
	if not child.closed:
		child.setwinsize(lines, columns)


def spawn_and_interact(*command, line=None, lines=None, shell=SHELL, shell_prompt_re=SHELL_PROMPT_RE):
	""" spawn a child process in an interactive shell """

	if sum(bool(x) for x in [command, line, lines]) > 1:
		raise ValueError("only one of command, line, or lines can be specified")

	if command:
		line = " ".join(shlex.quote(arg) for arg in sys.argv[1:])
	if line:
		lines = [line]
	if lines is None:
		lines = []

	# Spawn the shell process
	child = pexpect.spawn(shell)

	# Set the initial window size
	pass_terminal_size_to_child(child)

	# Set the window size when the terminal changes
	signal.signal(signal.SIGWINCH, partial(pass_terminal_size_to_child, child))

	# Send the commands
	for line in lines:
		child.expect(shell_prompt_re)
		child.sendline(line)

	# Interact with the spawned process
	child.interact()


if __name__ == "__main__":
	spawn_and_interact(*sys.argv[1:])
