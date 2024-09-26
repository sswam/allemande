#!/bin/bash
for file in "$@"; do
	xterm -e llm-git-commit "$file" & disown
done
