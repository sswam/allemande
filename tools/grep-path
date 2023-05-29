#!/bin/bash -eu
# grep-path:	grep all files in PATH with the grep args given

v=

. opts

if [ "$v" = 1 ]; then
	v=v
fi

IFS_old=$IFS
IFS=:
path_dirs=($PATH)
IFS=$IFS_old

# exclude system paths and hidden directories

path_dirs=($(
	lecho "${path_dirs[@]}" |
	grep -v '^$' | grep -v '^#' |
	grep -v -e '^/bin' -e '^/sbin' -e '^/usr/' -e '^/opt' -e '^/snap' -e '/venv' \
		-e '/Android/Sdk' -e '/mambaforge' -e '^/home/sam/go/bin' -e '/\.' |
	sort -u
))

# run grep for each dir
for dir in "${path_dirs[@]}"; do
	$v grep -r "${OPTS_UNKNOWN[@]}" "${*:-.}" "$dir" || true
done
