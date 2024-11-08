#!/usr/bin/env python3-allemande

"""
A basic implementation of ed in Python, including commands a, c, i, d, s, w, q, and p.
"""

import sys
import logging
from typing import TextIO

from argh import arg

from ally import main

__version__ = "0.1.1"

logger = main.get_logger()


class PyEd:
    def __init__(self, filename: str):
        self.filename = filename
        self.lines = []
        self.current_line = 0
        self.modified = False

        try:
            with open(filename, 'r') as f:
                self.lines = f.readlines()
        except FileNotFoundError:
            logger.info(f"New file: {filename}")

    def run_command(self, command: str) -> str:
        cmd = command.strip().split()
        if not cmd:
            return ""

        action = cmd[0]
        args = cmd[1:]

        if action == 'a':
            return self.append()
        elif action == 'c':
            return self.change()
        elif action == 'i':
            return self.insert()
        elif action == 'd':
            return self.delete()
        elif action == 's':
            return self.substitute(args)
        elif action == 'w':
            return self.write()
        elif action == 'q':
            return self.quit()
        elif action == 'p':
            return self.print()
        elif action == '.':
            return str(self.current_line)
        elif action == 'n':
            return self.print_numbered()
        elif action == 'j':
            return self.join_lines()
        elif action.startswith('/'):
            return self.search(action)
        elif action.startswith('g/'):
            return self.global_command(command)
        elif action == 'u':
            return self.undo()
        else:
            return f"?\n{action}: Unknown command"

    def append(self) -> str:
        new_lines = []
        while True:
            line = input()
            if line == '.':
                break
            new_lines.append(line + '\n')
        self.lines[self.current_line:self.current_line] = new_lines
        self.current_line += len(new_lines)
        self.modified = True
        return ""

    def change(self) -> str:
        if self.current_line >= len(self.lines):
            return "?"
        del self.lines[self.current_line]
        return self.append()

    def insert(self) -> str:
        return self.append()

    def delete(self) -> str:
        if self.current_line >= len(self.lines):
            return "?"
        del self.lines[self.current_line]
        self.modified = True
        return ""

    def substitute(self, args: list[str]) -> str:
        if len(args) != 2:
            return "?"
        old, new = args
        if self.current_line >= len(self.lines):
            return "?"
        self.lines[self.current_line] = self.lines[self.current_line].replace(old, new)
        self.modified = True
        return ""

    def write(self) -> str:
        with open(self.filename, 'w') as f:
            f.writelines(self.lines)
        self.modified = False
        return f"{len(self.lines)}"

    def quit(self) -> str:
        if self.modified:
            return "?"
        sys.exit(0)

    def print(self) -> str:
        if self.current_line >= len(self.lines):
            return "?"
        return self.lines[self.current_line].rstrip()

    def print_numbered(self) -> str:
        if self.current_line >= len(self.lines):
            return "?"
        return f"{self.current_line + 1}\t{self.lines[self.current_line].rstrip()}"

    def join_lines(self) -> str:
        if self.current_line >= len(self.lines) - 1:
            return "?"
        self.lines[self.current_line] = self.lines[self.current_line].rstrip() + " " + self.lines.pop(self.current_line + 1).lstrip()
        self.modified = True
        return ""

    def search(self, pattern: str) -> str:
        pattern = pattern.strip('/').strip()
        for i, line in enumerate(self.lines[self.current_line+1:], start=self.current_line+1):
            if pattern in line:
                self.current_line = i
                return line.rstrip()
        return "?"

    def global_command(self, command: str) -> str:
        parts = command.split('/')
        if len(parts) < 3:
            return "?"
        pattern = parts[1]
        cmd = '/'.join(parts[2:]).strip()
        results = []
        for i, line in enumerate(self.lines):
            if pattern in line:
                self.current_line = i
                result = self.run_command(cmd)
                if result:
                    results.append(result)
        return '\n'.join(results)

    def undo(self) -> str:
        return "Undo not implemented"

    def process_commands(self, istream: TextIO, ostream: TextIO) -> None:
        get, put = main.io(istream, ostream)

        while True:
            command = get()
            if not command:
                break
            result = self.run_command(command)
            if result:
                put(result)


@arg("filename", help="file to edit")
def pyed(
    filename: str,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    A basic implementation of ed in Python, including commands a, c, i, d, s, w, q, p, n, j, /pattern/, g/pattern/command, and u.
    """
    editor = PyEd(filename)
    editor.process_commands(istream, ostream)


if __name__ == "__main__":
    main.run(pyed)
