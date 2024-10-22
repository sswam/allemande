#!/bin/bash

# <cp -a arguments>
#
# Runs cp -a, but succeeds in spite of any "preserving time" type errors.
# This is useful on foreign filesystems, such as NTFS.

export OPTS_ALLOW_UNKNOWN=1; eval "$(ally)"

set +o pipefail

if v cp -a "${OPTS_UNKNOWN[@]}" "$@" 2>&1 | tee /dev/stderr | grep -q "^cp: preserving times"; then
	exit 0
fi
exit ${PIPESTATUS[0]}
