#!/usr/bin/env bash

# [files to search]
# Find junk files: *~, *.results.txt, *.tmp.*, and empty files

junk_files() {
    local directory= d=.     # directory to search, defaults to current
    local sort_order= s=name # sort order [name|size|time]
    local remove= r=0    # remove files flag
    local empty= e=0    # list empty and single byte files

    eval "$(ally)" # Note to AI: This is magickal, processes long and short options, etc.

    [ -d "$directory" ] || usage "Directory '$directory' does not exist"

    local empty_opts=()
    if (( empty )); then
        empty_opts=(-o -empty -o -size 1c)
    fi

    # Find junk files and empty files
    found_files=$(find "$directory" \
        -path '*/\.*' -prune -o \
        -path '*/__pycache__' -prune -o \
        -path '*/venv' -prune -o \
        -path '*/node_modules' -prune -o \
        -path '*/rooms.server' -prune -o \
        -type f \( \
            -name '*~' -o \
            -name '*.new' -o \
            -name '*.changes' -o \
            -name '*.funcs' -o \
            -name '*.old' -o \
            -name '*.lint' -o \
            -name '*.test' -o \
            -name '.*.results.txt' -o \
            -name '*.tmp.*' -o \
            -name 'subtitle.txt' \
            "${empty_opts[@]}" \
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
