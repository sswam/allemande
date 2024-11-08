#!/usr/bin/env python3-allemande

# llm-pp: preprocess LLM conversations, to clean them up

# example usage with input and output:

"""
Example text file:

Sam:	Please improve this high-temperature AI generated story without making it longer.
Once upon a time, there was a princess who had been cursed by a wicked witch. The curse caused her to be cursed with a powerful sleep that she could not wake up from.
AI:	okay I'll do it...
Summary: The princess was cursed by a wicked witch and fell into an unbreakable sleep.

Any line starting with AI, assistant, ChatGPT, GPT or similar, the label is changed to "assistant:".
Any line starting with $USER in any case is changed to start with "user:"

Lines not starting with a label like that are indented with a tab.

Example output:

user:	Please improve this high-temperature AI generated story without making it longer.
	Once upon a time, there was a princess who had been cursed by a wicked witch. The curse caused her to be cursed with a powerful sleep that she could not wake up from.
assistant:	okay I'll do it...
	Summary: The princess was cursed by a wicked witch and fell into an unbreakable sleep.
"""

# llm-pp: preprocess LLM conversations

import os
import sys
import re

def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)

def preprocess(file):
	user = os.environ.get('LLM_USER', os.getlogin()).lower()
	User = user.title()

	assistant_labels = ['ai', 'assistant', 'chatgpt', 'gpt', 'gpt4', 'gpt-4', 'bot', 'robot', 'claude', 'claude-instant', 'instant']
	user_labels = ['user', user]
	system_labels = ['system', 'sys', 'mission', 'scenario']
	warn_unknown_labels = True

	first_line = True   # to flag, whether the first line has a label or not

	for line in file:
		# strip trailing white spaces
		line = line.rstrip()

		# split line on :
		if m := re.match(r'^(\w+):\t(.*)', line):
			label, text = m.groups()
		else:
			label, text = '', re.sub(r'^\t', '', line)

		label_lc = label.lower()

		# if the first line does not have a label, add the user label
		if first_line and not label:
			label = 'user'
		elif label_lc in assistant_labels:
			label = "assistant"
		elif label_lc in user_labels:
			label = "user"
		elif label_lc in system_labels:
			label = "system"
		elif label:
			eprint(f"Unknown label: {label}")
			label = ""
			text = line

		# write modified line to standard output
		print(f"{label}{':' if label else ''}\t{text}")

		# on 1st iteration, set flag False
		if first_line:
			first_line = False

if __name__ == "__main__":
	preprocess(sys.stdin)
