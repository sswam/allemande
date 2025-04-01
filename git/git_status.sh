#!/bin/sh
git -c color.status=always status "$@" | less -R -F -X
