#!/bin/bash -eu
# locker:	Locks a file and runs a command
# locker.sh

if [ "$#" -lt 2 ]; then
        echo "Usage: locker <lockfile> <command>"
        exit 1
fi

LOCKFILE="$1"
shift
COMMAND=("${@}")

(
    # Block until the lock is acquired
    flock -x 200

    # Run the command
    "${COMMAND[@]}"
) 200>"${LOCKFILE}"
