#!/bin/bash
# git-vimdiff: view and edit git changes in vimdiff

v= #v
c= #confirm
from=HEAD
to=
commit=
cdroot=
tmp=1

. opts

if [ -n "$tmp" ]; then
	if [ "$tmp" = 1 ]; then
		tmp=$HOME/tmp
	fi
	if [ ! -d "$tmp" ]; then
		echo >&2 "use --tmp=dir, --tmp= or create ~/tmp"
		exit 1
	fi
fi

if [ -n "$v" ]; then
	v=v
fi
if [ -n "$c" ]; then
	c=confirm
fi
if [ -n "$commit" ]; then
	from="$commit~1"
	to="$commit"
fi

if [ "$#" = 0 -a -z "$VD_RECURSE" ]; then
	VD_RECURSE=1
	export VD_RECURSE
	cd "$(git-root)"
	git-mod all-changes | xa "$0" "${OPTS[@]}"
	exit
fi

dir=$PWD
root=`readlink -f "$(git-root)"`

diff_file() {(
	local file=$1

	file=`readlink -f "$file"`
	case "$file" in
	"$root"*)
		file=${file#$root/}
		;;
	esac

	cd "$root"

	if [ -n "$tmp" ]; then
		old="$tmp/vd.old.`basename "$file"`"
	else
		old="`dirname "$file"`/.vd.old.`basename "$file"`"
	fi

$v	git show "$from:$file" >"$old"

	if [ -n "$to" ]; then
		if [ -n "$tmp" ]; then
			new="$tmp/vd.new.`basename "$file"`"
		else
			new="`dirname "$file"`/.vd.new.`basename "$file"`"
		fi

$v		git show "$to:$file" >"$new"
	else
		new=$file
	fi

	old_abs=`readlink -f "$old"`
	new_abs=`readlink -f "$new"`

	if ! q cmp "$new" "$old"; then (
		if [ -z "$cdroot" ] ; then
			cd "$dir"
		fi
$c		vimdiff "$new_abs" "$old_abs" </dev/tty
	) fi
	mr "$old"
	if [ -n "$to" ]; then
		mr "$new"
	fi
)}

for file; do
	diff_file "$file"
done
