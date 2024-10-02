#!/bin/bash

# Function to check if a command is available
want() {
    command -v "$1" >/dev/null 2>&1
}

# Reformat functions for different languages
reformat_sh() {
    local prog="$1"
    want shfmt && quiet shfmt -w "$prog" || true
}

reformat_py() {
    local prog="$1"
    want black && quiet black "$prog" || true
}

reformat_c() {
    local prog="$1"
    want clang-format && quiet clang-format -i "$prog" || true
}

reformat_pl() {
    local prog="$1"
    want perltidy && quiet perltidy -b "$prog" || true
}

reformat_go() {
    local prog="$1"
    want gofmt && quiet gofmt -w "$prog" || true
}

reformat_rs() {
    local prog="$1"
    want rustfmt && quiet rustfmt "$prog" || true
}

reformat_js() {
    local prog="$1"
    want prettier && quiet prettier --write "$prog" || true
}

reformat_ts() {
    reformat_js "$1"
}

# Main reformat function
reformat() {
    local prog="$1"
    local ext=${prog##*.}
    reformat_$ext "$prog"
}

# Main execution
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file1> [file2] ..."
    exit 1
fi

for file in "$@"; do
    if [ -f "$file" ]; then
        reformat "$file"
    else
        echo "File not found: $file" >&2
    fi
done
