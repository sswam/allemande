#!/bin/sh
exec find "$@" -name .git -prune -o -type f ! -name '*.o' ! -name '*.so' -print0 | xargs -0 file | grep ': *ELF ' | sed 's/:.*//' | sort
