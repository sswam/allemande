#!/bin/bash -eu
m=
. opts
query -m="$m" "$@
Please reply as concise as possible, with no boilerplate or unnecessary explanation." | rstrip
