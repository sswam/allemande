#!/usr/bin/env python3

import sys

input_text = sys.stdin.read()
paragraphs = input_text.split('\n\n')
paragraphs.reverse()

for paragraph in paragraphs:
    print(paragraph.rstrip("\n"), end='\n\n')
