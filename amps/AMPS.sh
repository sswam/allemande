# AMPS.sh - execute AMPS-shell files by translating to shell script

# Ensure we are running bash
[ -n "$BASH_VERSION" ] || exec bash "$0" "$@"

# Exit on errors
set -e

# Find the source, target, and new target files
source=$(readlink -e "$0")
target="${source%/*}/.${source##*/}"
new="$target.new.$$"

# Translate if needed
if [ "$source" -nt "$target" ]; then
	touch "$target"
	AMPS_shell "$source" >"$new"
	chmod +x "$new"
	mv "$new" "$target"
fi

# Execute the target in this shell
. "$target"
exit $?
