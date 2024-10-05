#!/bin/sh
printf '%s\n' "$1" | sed 's/[][\.*^$\/\&]/\\&/g'
# | sed ':a;N;$!ba;s/\n/\\n/g'  # in case I ever need to escape newlines
