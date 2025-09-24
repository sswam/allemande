#!/bin/bash

title=""
if [ -n "$TERMINAL_TITLE" ]; then
    title+="$TERMINAL_TITLE: "
fi

if [ -z "$title" ]; then
    if [ -n "$STY" ]; then
        title="${STY#*.}: $title"
    fi
    if [ -n "$SSH_TTY" ]; then
        title="$HOSTNAME: $title"
    fi
fi

title+="$*"
title=${title%: }

name-terminal "$title"
