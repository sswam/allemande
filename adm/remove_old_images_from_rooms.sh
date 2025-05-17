#!/bin/bash
set -euo pipefail

dir="$1"

# Get a list of all jpg files older than 2 days, not in the cast directory, and are owner writable
find "$dir" -mtime +2 -type f -name '*.jpg' -not -path '*/cast/*' -perm /200 | sed 's|^\./||' | sort > .all_jpg_files.txt

# Get list of files tracked by Git
git ls-files "*.jpg" | sed 's|^\./||' | sort > .git_jpg_files.txt

# Use comm to find files that are in all_jpg_files but not in git_jpg_files, and remove them
comm -23 .all_jpg_files.txt .git_jpg_files.txt | xargs-better move-rubbish

rm -f .all_jpg_files.txt .git_jpg_files.txt
