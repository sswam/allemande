#!/bin/bash
(
for m in i c 3+ 4; do
	time gpt query -m $m "Please write me a short Python program to play a very simple text adventure game with the user. Please respond with Python code only, no English or example output, and no backtick quotes" |
	grep -v '^`' | tee adv-$m.py | python
done
) 2>&1 | tee gen.log
