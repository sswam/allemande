#!/bin/sh
df -h "$@" 2>/dev/null |
grep -E '^Filesystem|/$|/home$| /media/| /mnt|/dev/mapper' | grep -v '^overlay ' |
sed 's/Mounted on/Mount/' |
txt2tsv | tsv-tidy | tsv2txt -t |
kutleft 6 4 5 3 2 | headless order | tsv2txt -t
