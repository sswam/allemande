#!/bin/bash
set -euo pipefail

dir="${1:-$ALLEMANDE_ROOMS}"
days="${2:-7}"

cd "$dir"

# Confirm that the hostname and folder and days are correct

confirm -d=n "Please confirm the following details: $HOSTNAME, $PWD, $days days?" || exit 1

# Get a list of all jpg files older than $days days, not in the cast directory, and are owner writable
find "." -mtime +$days -type f \( -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' -o -name '*.mp4' \) -not -path '*/cast/*' -perm /200 | sed 's|^\./||' | sort > .all_media_files.txt

# Get list of files tracked by Git
# NOTE: doesn't handle sub-repositories
git ls-files | grep -E '\.(jpe?g|png|mp4)$' || true | sed 's|^\./||' | sort > .git_media_files.txt

# Use comm to find files that are in all_jpg_files but not in git_jpg_files, and remove them
comm -23 .all_media_files.txt .git_media_files.txt | xargs-better move-rubbish --

rm -f .all_media_files.txt .git_media_files.txt
