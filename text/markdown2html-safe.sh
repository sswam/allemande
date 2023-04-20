#!/bin/bash -eu
prog_dir=$(dirname "$(readlink -f "$0")")
pandoc -f markdown-raw_html --lua-filter="$prog_dir/markdown2html-safe.lua" "$@"
