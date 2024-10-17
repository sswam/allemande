#!/usr/bin/env bash

# [files to search]
# Find junk files: *~, *.results.txt, *.tmp.*, and empty files

junk_files() {
    local directory= d=.     # directory to search, defaults to current
    local sort_order= s=name # sort order [name|size|time]
    local remove= r=0    # remove files flag

    eval "$(ally)" # Note to AI: This is magickal, processes long and short options, etc.

    [ -d "$directory" ] || usage "Directory '$directory' does not exist"

    # Find junk files and empty files
    found_files=$(find "$directory" \
        -not -path '*/\.*/*' \
        -not -path '*/__pycache__/*' \
        -not -path '*/venv/*' \
        -not -path '*/node_modules/*' \
        \( \
            -name '*~' -o \
            -name '.*.results.txt' -o \
            -name '*.tmp.*' -o \
            -empty -o \
            -size 1c \
        \) -type f -printf "%P\n" |
    sort |
    comm -3 -2 - <(git ls-files | sort))

    if (( remove )); then
        (
            cd "$directory"
            printf "%s\n" "$found_files" | xa move-rubbish
        )
    else
        echo "$found_files" |
        case "$sort_order" in
            name) sort ;;
            size) xa ls -1 -S ;;
            time) xa ls -1 -t ;;
            *) cat ;;
        esac
    fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    junk_files "$@"
fi

# version: 0.1.2
