#!/bin/bash
len=${1:-30}
shift
grep -r -I -E "[A-Za-z0-9/_\-]{$len,}" --exclude-dir={old,usr,lib,etc,tmp,var,images,python} --color=auto "$@" |
	less -R
