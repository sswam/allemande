#!/usr/bin/env bash

# usage: eval "$(ally)"
# Sets strict mode, gets options with opts, enables aliases,
# defines some functions and aliases.
#
# This script provides a set of utility functions and aliases for Bash
# environments. It includes:
# - Strict mode settings for better error handling
# - Option parsing functionality
# - Utility functions for command quoting, file backup, and more
# - Debugging and notification helpers
# - Countdown and timing functions
#
# Version: 0.1.1
# ENDDOC

. need-bash

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    case "${1:-}" in
    -h|--help)
        exec <"${BASH_SOURCE[0]}" sed -n '/^#!/d; /^# ENDDOC$/q; s/# //; p'; exit 1
    esac
    exec <"${BASH_SOURCE[0]}" sed -n '/^# START$/,$p'; exit 1
fi

# START

. each

if [[ $- == *i* ]]; then
    :
else
    shopt -s expand_aliases

    . opts

    eval "$(opts_long.py "$0")"

    # strict mode
    old_opts=$(set +o)
    set -e -u -o pipefail
    trap 'trap - RETURN; eval "$old_opts"' RETURN
fi

quote_command() {
    local cmd=$(printf "%q " "$@")
    cmd=${cmd% }
    printf "%s\n" "$cmd"
}

alias qc=quote_command
alias X=eval

ret() {
    qc "$@"
    echo 'return $?'
}

tryit() {
    X "$(ret ls /)"
}

backup() {
    local file=$1
    if [ -e "$file~" ]; then
        move-rubbish "$file~"
    fi
    cp -i -a "$file" "$file~" || true
}

locate_file() {
    local file=$1
    if [ ! -e "$file" ]; then
        local file2=$(which "$file")
        if [ ! -e "$file2" ]; then
            echo >&2 "not found: $file"
            return 1
        fi
        file=$file2
    fi
    file=$(readlink -e "$file")
    echo "$file"
}

code_modify() {
    local E=0 # do not edit

    . opts

    local file=$1
    shift
    local command=("$@")

    # If no file is provided, process input stream
    if [ -z "$file" ] || [ "$file" = "-" ]; then
        "${command[@]}" | markdown-code -c '#'
        return
    fi

    # Locate the file and create a backup
    file=$(locate_file "$file")
    [ -n "$file" ] || return 1
    backup "$file"

    # Process the file content and save to a temporary file
    <"$file" "${command[@]}" | markdown-code -c '#' >"$file~"

    # Swap the original and processed files
    swapfiles "$file" "$file~"

    # Open both files in vimdiff for comparison
    if [ "$E" = 0 ]; then
        vimdiff "$file" "$file~"
    fi
}

die() {
    printf >&2 "%s: fatal: %s\n" "${0##*/}" "$*"
    exit 1
}

log() {
    printf >&2 "%s\n" "$*"
}

notify() {
    local name="${0##*/}"
    name=${name%.*}
    notify-send -u critical -t 10000 \
        -i /usr/share/icons/gnome/48x48/status/appointment-soon.png \
        "$name" "$1"
}

countdown() {
    local remaining=$1 warn=$2 warn_interval=${3:-10}
    shift 2
    while [ "$remaining" -gt 0 ]; do
        if [ "$remaining" -le "$warn" ] && (( remaining % warn_interval == 0 || remaining < warn_interval )); then
            notify "$remaining seconds"
        fi
        sleep 1
        remaining=$((remaining - 1))
    done
}

countdown_wrap() {
    local timeout=$1 warn=$2
    shift 2
    if ((timeout)); then
        countdown "$timeout" "$warn" &
        countdown_pid=$!
        old_opts=$(set +o)
        ret=1
        set +e
        "$@"
        ret=$?
        kill $countdown_pid 2>/dev/null
        eval "$old_opts"
        return $ret
    else
        "$@"
        return
    fi
}

finder() {
    local file=$1
    if [ ! -f "$file" ]; then
        file=$(which-file "$file")
    fi
    file=$(readlink -f "$file")
    printf "%s\n" "$file"
}

debug() {
    local _echovar_var
    for _echovar_var; do
        eval "echo -n \"$_echovar_var=\$$_echovar_var \"" >&2
    done
    echo
}
