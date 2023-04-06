#!/usr/bin/env python3 
""" brace.py - Convert Python-style indented lines to C-style braces """

import argh
import sys
import itertools

def brace(stream_in=sys.stdin, stream_out=sys.stdout, tab="\t", colons=False, semicolons=True):
    indent_level = 0
    first_line = True
    for line in itertools.chain(stream_in, ["."]):
        line = line.rstrip()
        if not line:
            continue
        if not colons:
            line = line.rstrip(":")
        line_indent_level = line.count(tab)
        if semicolons and line_indent_level <= indent_level and not first_line:
            print(tab * indent_level + ";", file=stream_out)
        while indent_level < line_indent_level:
            print(tab * indent_level + "{", file=stream_out)
            indent_level += 1
        while indent_level > line_indent_level:
            indent_level -= 1
            print(tab * indent_level + "}", file=stream_out)
        print(line, file=stream_out)
        indent_level = line_indent_level
        first_line = False

if __name__ == '__main__':
    argh.dispatch_command(brace)
