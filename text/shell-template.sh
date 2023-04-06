#!/bin/bash -eu
d=	# debug
p=  # permissive
eval_opts=

. opts

if [ "$p" != 1 ]; then
    eval_opts="$eval_opts -eu"
fi

template=$1

wrap-heredoc() {
    local template=$1
    echo "cat <<EOF"
    cat "$template"
    echo "EOF"
}

if [ -n "$d" ]; then
    wrap-heredoc "$template"
else
    wrap-heredoc "$template" | bash $eval_opts
fi
