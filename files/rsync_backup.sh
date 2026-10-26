#!/bin/bash
#exec rsync -uaSzvP "$@"
# other options you might want:
#  --update --sparse --inplace --remove-source-files --hard-links
# can't have --sparse and --inplace together
#  --bwlimit=KBPS

: ${RSYNC_RSH:=ssh -o ControlPath=none}
export RSYNC_RSH

pretty=
if [ -t 0 -o -n "$RS_PRETTY" ]; then
	pretty="--progress --verbose"
fi

rs_options="${rs_options:---inplace --hard-links --no-whole-file}"
rs_archive="--recursive --links --perms --times --group --owner --devices --specials"   # -rlptgoD
  # --no-perms --no-group --no-owner

exec rsync $rs_archive --compress --partial $rs_options $pretty "$@"
