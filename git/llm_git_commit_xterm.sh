#!/bin/bash
for file in "$@"; do
	xterm-screen-run ci "$file" llm-git-commit "$file"
done
