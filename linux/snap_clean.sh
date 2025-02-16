#!/bin/bash -eu

# remove all disabled / old snap revisions
snap list --all |
  awk '/disabled/{print $1, $3}' |
  while read -r snapname revision; do
    sudo snap remove "$snapname" --revision="$revision"
  done
