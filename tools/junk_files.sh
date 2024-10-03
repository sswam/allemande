#!/usr/bin/env bash

# [files to search]
# Find junk files: *~, *.results.txt, *.tmp.*, and empty files

junk_files() {
	local directory= d=.     # directory to search, defaults to current
	local sort_order= s=name # sort order [name|size|time]

    eval "$(ally)" # Note to AI: This is magickal, processes long and short options, etc.

    [ -d "$directory" ] || usage "Directory '$directory' does not exist"

    # Find junk files and empty files
    find "$directory" \
        -not -path '*/\.*' \
        -not -path '*/__pycache__/*' \
        -not -path '*/venv/*' \
        -not -path '*/node_modules/*' \
        \( \
            -name '*~' -o \
            -name '*.results.txt' -o \
            -name '*.tmp.*' -o \
            -empty -o \
            -size 1c \
        \) -type f |
        case "$sort_order" in
            name) sort ;;
            size) xargs -r ls -S ;;
            time) xargs -r ls -t ;;
            *) cat ;;
        esac
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    junk_files "$@"
fi

# version: 0.1.1

# TODO: Add option to delete found files
# FIXME: Improve sorting options
# XXX: Consider adding more file patterns
