#!/usr/bin/env bash

# Tests for fusecache.c
# - Mounts the filesystem with a temp source/cache/mount
# - Verifies read-through and cache population
# - Verifies directory listing
# - Verifies read-only behavior (writes fail)
# - Verifies traversal protection via symlink outside source

# Notes about fusecache.c:
# - getattr returns -ENOMEM if get_source_path fails, but that helper sets errno;
#   getattr should probably return -errno instead.
# - getattr uses lstat on a fully resolved path (via realpath), which loses
#   symlink semantics (i.e., it stats the symlink target, not the link).
# - These are noted only; the test exercises behavior as-implemented.

if command -v ally >/dev/null 2>&1; then
	eval "$(ally)"
else
	set -euo pipefail
fi

# Options (simple, optional)
keep=0
while [ $# -gt 0 ]; do
	case "$1" in
		--keep|-k) keep=1; shift ;;
		--) shift; break ;;
		-*) printf >&2 "Unknown option: %s\n" "$1"; exit 2 ;;
		*) break ;;
	esac
done

require_cmd() {
	if ! command -v "$1" >/dev/null 2>&1; then
		printf >&2 "%s not found\n" "$1"
		exit 127
	fi
}

# Try to find fusecache.c near this test script
script_dir=$(cd "$(dirname "$0")" && pwd)
repo_root="$script_dir/.."
candidates=(
	"$repo_root/fusecache.c"
	"$repo_root/input/fusecache.c"
	"$script_dir/../input/fusecache.c"
	"$script_dir/../../input/fusecache.c"
	"$script_dir/../fusecache.c"
)
prog_src=""
i=0
while [ $i -lt ${#candidates[@]} ]; do
	p="${candidates[$i]}"
	if [ -f "$p" ]; then
		prog_src="$p"
		break
	fi
	i=$((i+1))
done
if [ -z "$prog_src" ]; then
	printf >&2 "fusecache.c not found near %s\n" "$script_dir"
	exit 1
fi

# Build or select launcher
tmp_root="$(mktemp -d)"
cleanup() {
	# Unmount and kill background process if still running
	if mount_is_active "$mnt_dir"; then
		umount_mnt "$mnt_dir" || true
	fi
	if [ -n "${fs_pid:-}" ] && kill -0 "$fs_pid" >/dev/null 2>&1; then
		kill "$fs_pid" >/dev/null 2>&1 || true
		sleep 0.2 || true
		kill -9 "$fs_pid" >/dev/null 2>&1 || true
	fi
	if [ "${keep}" -eq 0 ]; then
		rm -rf -- "$tmp_root" || true
	else
		printf >&2 "Keeping temp dir: %s\n" "$tmp_root"
	fi
}
trap cleanup EXIT INT TERM

# Helper: is something mounted on a path?
mount_is_active() {
	local m="$1"
	if [ ! -d "$m" ]; then
		return 1
	fi
	# Avoid mountpoint(1) dependency; check mountinfo
	grep -F " $m " /proc/self/mountinfo >/dev/null 2>&1
}

umount_mnt() {
	local m="$1"
	if command -v fusermount3 >/dev/null 2>&1; then
		fusermount3 -u "$m" || return $?
	elif command -v fusermount >/dev/null 2>&1; then
		fusermount -u "$m" || return $?
	else
		umount "$m" || return $?
	fi
}

# Prepare dirs
src_dir="$(mktemp -d "$tmp_root/src.XXXX")"
cache_dir="$(mktemp -d "$tmp_root/cache.XXXX")"
mnt_dir="$(mktemp -d "$tmp_root/mnt.XXXX")"

# Create source content
mkdir -p "$src_dir/sub"
printf "hello world\n" > "$src_dir/hello.txt"
printf "nested\n" > "$src_dir/sub/nested.txt"

# Symlink that points outside source_dir to test traversal defense
# If /etc/hosts doesn't exist (unlikely), point to /etc/passwd
ext_target="/etc/hosts"
if [ ! -e "$ext_target" ]; then ext_target="/etc/passwd"; fi
ln -s "$ext_target" "$src_dir/outside_link"

# Locate or build the executable
fs_cmd=""
if command -v ccx >/dev/null 2>&1; then
	# Use the ccx shebang, execute the source directly
	chmod +x "$prog_src" || true
	fs_cmd="$prog_src"
else
	# Fallback: compile with cc and fuse3 via pkg-config
	require_cmd cc
	if ! pkg-config --exists fuse3 >/dev/null 2>&1; then
		printf >&2 "fuse3 development package not available for build\n"
		exit 1
	fi
	# Collect flags safely into an array
	mapfile -t fuse3_flags < <(pkg-config --cflags --libs fuse3)
	out_bin="$tmp_root/fusecache.bin"
	cc -Wall -D_FILE_OFFSET_BITS=64 -D_GNU_SOURCE -o "$out_bin" "$prog_src" "${fuse3_flags[@]}"
	fs_cmd="$out_bin"
fi

# Ensure fusermount is available for unmount
if ! command -v fusermount3 >/dev/null 2>&1 && ! command -v fusermount >/dev/null 2>&1; then
	printf >&2 "fusermount not found; cannot run FUSE tests\n"
	exit 1
fi

# Launch the filesystem in foreground and background the process
# Force foreground (-f) to avoid daemonizing
# Note: fusecache shifts its args so -f must be after mount point.
"$fs_cmd" "$src_dir" "$cache_dir" "$mnt_dir" -f &
fs_pid=$!

# Wait for mount to show up
attempts=50
mounted=0
n=0
while [ $n -lt $attempts ]; do
	if mount_is_active "$mnt_dir"; then
		mounted=1
		break
	fi
	# Probe with a directory listing to tickle mount setup
	ls "$mnt_dir" >/dev/null 2>&1 || true
	sleep 0.1
	n=$((n+1))
done
if [ $mounted -ne 1 ]; then
	printf >&2 "Failed to mount at %s\n" "$mnt_dir"
	exit 1
fi

# Tests begin
fail=0

# 1) readdir shows our files/dirs
if ! ls "$mnt_dir" >/dev/null 2>&1; then
	printf >&2 "readdir failed on mountpoint\n"
	fail=1
fi
if ! [ -f "$mnt_dir/hello.txt" ]; then
	printf >&2 "hello.txt not visible in mount\n"
	fail=1
fi
if ! [ -d "$mnt_dir/sub" ]; then
	printf >&2 "sub directory not visible in mount\n"
	fail=1
fi

# 2) read-through equals source, and populates cache afterward
if ! cmp -s "$src_dir/hello.txt" "$mnt_dir/hello.txt"; then
	printf >&2 "Content mismatch for hello.txt\n"
	fail=1
fi
# After reading, cache should have the file with same content
if ! [ -f "$cache_dir/hello.txt" ]; then
	printf >&2 "Cache miss not populated for hello.txt\n"
	fail=1
else
	if ! cmp -s "$src_dir/hello.txt" "$cache_dir/hello.txt"; then
		printf >&2 "Cache content mismatch for hello.txt\n"
		fail=1
	fi
fi

# 3) nested file read
if ! cmp -s "$src_dir/sub/nested.txt" "$mnt_dir/sub/nested.txt"; then
	printf >&2 "Content mismatch for sub/nested.txt\n"
	fail=1
fi
if ! [ -f "$cache_dir/sub/nested.txt" ]; then
	printf >&2 "Cache miss not populated for sub/nested.txt\n"
	fail=1
fi

# 4) read-only: write should fail
if sh -c 'printf x > "$1"' sh "$mnt_dir/hello.txt"; then
	printf >&2 "Write unexpectedly succeeded on read-only FS\n"
	fail=1
fi

# 5) traversal defense: symlink to outside should not be readable
# getattr or open should deny access; reading should fail
if cat "$mnt_dir/outside_link" >/dev/null 2>&1; then
	printf >&2 "Traversal protection failed; outside symlink was readable\n"
	fail=1
fi

# Wrap up
# Unmount and wait a moment for process to exit
if ! umount_mnt "$mnt_dir"; then
	printf >&2 "Unmount failed for %s\n" "$mnt_dir"
	fail=1
fi

# Give the process a moment to exit cleanly
sleep 0.2
if [ -n "${fs_pid:-}" ] && kill -0 "$fs_pid" >/dev/null 2>&1; then
	# Try a gentle termination
	kill "$fs_pid" >/dev/null 2>&1 || true
	sleep 0.2 || true
	if kill -0 "$fs_pid" >/dev/null 2>&1; then
		printf >&2 "Filesystem process did not exit after unmount\n"
		fail=1
	fi
fi

if [ $fail -ne 0 ]; then
	exit 1
fi

exit 0
