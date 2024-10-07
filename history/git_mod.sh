#!/bin/sh
# git status "${@:-.}" | sed -n 's/^\t\(.*:   *\)\?//p' | sortmtime | kut 2 | tac

st=`git status --short`

echo "$st" | grep '^[A-Z]' | cut -c4- | sortmtime -r | kut 2
echo "$st" | grep '^ [A-Z]' | cut -c4- | sortmtime -r | kut 2
echo "$st" | grep '^?' | cut -c4- | sortmtime -r | kut 2
