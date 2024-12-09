#!/usr/bin/env python3-allemande

# Here's a Python program that reads lines in groups of 'n' from stdin, outputs each group to stdout with flushing, and handles EOF as requested:
# 'd' is a sleep delay, and 'p1' and 'p2' are prefixes it adds to the first and all lines, 'p3' is added after the group of lines.

import sys
import time

def process_input(n, d, p1, p2, p3):
    buffer = []

    def out():
        print(p1, end="")
        for line in buffer:
            print(p2 + line)
        print(p3, end='')
        buffer.clear()
        time.sleep(d)

    while True:
        try:
            line = input()
            buffer.append(line)
            if len(buffer) == n:
                out()
        except EOFError:
            if buffer:
                out()
            break

def main():
    n = int(sys.argv[1])
    d = float(sys.argv[2])
    p1 = sys.argv[3]
    p2 = sys.argv[4]
    p3 = sys.argv[5]

    process_input(n, d, p1, p2, p3)

if __name__ == '__main__':
    main()
