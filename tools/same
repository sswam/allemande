#!/bin/bash -eu
# same: exit success if A and B have same content, owner and permissions, etc.
# usage: same A B
# warn if something is different on stderr unless -q and exit 1

q=	# quiet
D=	# same device
i=	# same inode
s=	# symlink the files
l=	# link the files
v=	# verbose

. opts

A=$1 B=$2

# check opts

if [ -n "$l" ]; then
	i=1
fi

if [ -n "$v" -a -n "$q" ]; then
	die "same: -v and -q are mutually exclusive" >&2
fi

if [ -n "$v" ]; then
	v=v
	# TODO could change opts to do that for flags?
fi

# functions, TODO move to lib, see "die"
# die aka warn_exit

die() {
	if [ -z "$q" ]; then
		printf "%s\n" "$@" >&2
	fi
	exit 1
}

# if $B doesn't exist, and -l or -s option, just link it
if [ ! -e "$B" -a -n "$l" ]; then
	ln -f$v "$A" "$B"
	exit 0
fi
if [ ! -e "$B" -a -n "$s" ]; then
	ln -sf$v "$(realpath "$A")" "$B"
	exit 0
fi

# check args

for f in "$A" "$B"; do
	if [ ! -e "$f" ]; then
		die "same: does not exist: $f" >&2
	fi
	if [ -d "$f" ]; then
		die "same: is a directory: $f" >&2
	fi
done

# it's okay to have different mtime / ctime / etc, and different inodes.

is_symlink_to() {
	local f=$1
	local target=$2
	[ -L "$f" ] || return 1
	target=$(realpath "$target")
	link_target=$(readlink "$f")
	link_target=$(realpath "$link_target")
	[ "$link_target" = "$target" ] || return 1
	return 0
}

if is_symlink_to "$A" "$B"; then
	echo "same: already symlinked: $A -> $B" >&2
	exit 0
fi

if is_symlink_to "$B" "$A"; then
	echo "same: already symlinked: $B -> $A" >&2
	exit 0
fi

if [ "$(stat -c %F "$A")" != "$(stat -c %F "$B")" ]; then
	die "same: different type: $A ($(stat -c %F "$A")) vs $B ($(stat -c %F "$B"))" >&2
fi

if [ "$(stat -c %s "$A")" != "$(stat -c %s "$B")" ]; then
	die "same: different size: $A $B" >&2
fi

if [ "$(stat -c %U:%G "$A")" != "$(stat -c %U:%G "$B")" ]; then
	die "same: different owner:group: $A $B" >&2
fi

if [ "$(stat -c %a "$A")" != "$(stat -c %a "$B")" ]; then
	die "same: different permissions: $A $B" >&2
fi

# check same device if -D

if [ -n "$D" ]; then
	if [ "$(stat -c %d "$A")" != "$(stat -c %d "$B")" ]; then
		die "same: different device: $A $B" >&2
	fi
fi

# check same inode if -i

if [ -n "$l" ]; then
	if [ "$(stat -c %h "$A")" != "$(stat -c %h "$B")" ]; then
		die "same: different link: $A $B" >&2
	fi
fi

# check same content with cmp
if ! cmp -s "$A" "$B"; then
	die "same: different content: $A $B" >&2
fi

# link together similar files if -l
# links older files to newer files
if [ -n "$l" ]; then
	# check not already linked
	if [ "$(stat -c "%d:%i" "$A")" = "$(stat -c "%d:%i" "$B")" ]; then
		echo "same: already linked: $A $B" >&2
	elif [ "$A" -ot "$B" ]; then
		ln -f$v "$A" "$B"
	else
		ln -f$v "$B" "$A"
	fi
elif [ -n "$s" ]; then
	if [ "$A" -ot "$B" ]; then
		ln -sf$v "$(realpath "$A")" "$B"
	else
		ln -sf$v "$(realpath "$B")" "$A"
	fi
fi
