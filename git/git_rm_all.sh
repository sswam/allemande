#!/bin/bash -eu
# [arg ...]
# Not as bad as it sounds! This script will stage removal of all files that have been deleted.
. opts
git ls-files --deleted "$@" | xa git rm --
