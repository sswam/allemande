#!/usr/bin/env bash

(
	# Get staged changes
	git diff --name-status --cached | kutout 1 | sed 's/.*\t//'

	# Get unstaged changes
	git diff --name-status | kutout 1 | sed 's/.*\t//'

	# Get untracked files
	git ls-files --others --exclude-standard
) | uniqo
