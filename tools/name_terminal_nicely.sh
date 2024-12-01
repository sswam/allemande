#!/bin/bash

title=""
if [ -n "$SSH_TTY" ]; then
    title+="$HOSTNAME: "
fi
if [ -n "$STY" ]; then
    title+="${STY#*.}: "
fi
if [ -n "$TERMINAL_TITLE" ]; then
    title+="$TERMINAL_TITLE: "
fi
title+="$*"
title=${title%: }
name-terminal "$title"
