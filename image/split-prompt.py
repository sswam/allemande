#!/usr/bin/env python

""" split a stable diffusion prompt into multiple lines, to be more readable """

import sys
import re

def split_prompt(prompt):
    result = []
    start = 0
    nesting = 0
    for i, char in enumerate(prompt):
        if char == '(':
            nesting += 1
        elif char == ')':
            nesting -= 1
        elif char == ',' and nesting == 0:
            current = prompt[start:i+1].strip()
            following = prompt[i+1:].strip()
            if not (re.match(r'score_\d', current) and re.match(r'score_\d', following)):
                result.append(current)
                start = i + 1
    
    if start < len(prompt):
        result.append(prompt[start:].strip())

    result = '\n'.join(result)
    return result

if __name__ == '__main__':
    print(split_prompt(sys.stdin.read()).strip())
