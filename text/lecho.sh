#!/bin/bash -eu
# lecho: echo each argument on a separate line
printf "%s\n" "$@"

# explanation:
# printf "%s\n" "$@" prints each argument, separated by a newline

# The code is much simpler than techo, because we don't need to
# remove the last character from the string.
