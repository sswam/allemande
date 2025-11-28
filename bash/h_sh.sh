#!/bin/bash -eu
# 1-liner to greet a user in a specified language using AI or a simple print statement.
[[ $ai -eq 1 ]] && query "Greet ${1:-world} in ${LANG:-en}. Keep it short." || printf "Hi, %s\n" "$1"
