#!/bin/sh
set -eu
cd "$(git-root)"
file=.gitignore
new=$file.new.$$
(
if [ -e "$file" ]; then
	cat "$file"
fi
find-elf . | grep -v '/\.' | sed 's,^./,/,'
) | uniqo >"$new"
mv "$new" "$file"
