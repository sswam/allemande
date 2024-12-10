#!/bin/bash -eu
m=
. opts
prompt="${1:-}"
shift || true
query -m="$m" "$prompt
Please reply as concise as possible, with no boilerplate or unnecessary explanation." "$@" | text-strip
