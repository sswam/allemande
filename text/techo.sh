#!/bin/bash -eu
# techo: echo arguments, separated by tabs

out=`printf "%s\t" "$@"`
printf "%s\n" "${out%?}"

# explanation:

# printf "%s\t" "$@" prints each argument, separated by a tab
# ${out%?} removes the last character from the string
# (the last character is a tab, which we don't want)

# The code is much more complicated than lecho, because we need to
# remove the last character from the string.
