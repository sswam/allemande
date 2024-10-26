#!/usr/bin/env bash

# [file]
# Creates a backup of the specified file
# Moves existing backup to rubbish if present
# Uses the file name with a tilde (~) appended as the backup name

backup() {
	file= f=   # file to backup
	quiet= q=  # suppress output

	eval "$(ally)"

	if [ -z "$file" ]; then
		die "No file specified"
	fi

	backup_file="${file}~"

	if [ -e "$backup_file" ]; then
		rubbish "$backup_file"
		[ "$quiet" != 1 ] && printf >&2 "Moved existing backup to rubbish: %s\n" "$backup_file"
	fi

	cp -f "$file" "$backup_file"
	[ "$quiet" != 1 ] && printf "Created backup: %s\n" "$backup_file"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	backup "$@"
fi

# version: 0.1.1

# Here's the edited `backup.sh` file, incorporating the style from `hello_sh.sh` and following the guidance provided:

# Changes made:
# 1. Added more detailed help/doc lines at the top of the script.
# 2. Implemented options using the ally library style.
# 3. Used printf instead of echo for variable output.
# 4. Added a quiet option to suppress output.
# 5. Improved error handling and messaging.
# 6. Bumped the patch version.
#
# Note: The script now expects the file to be passed as an option (-f or --file) rather than as a positional argument. This change aligns better with the ally library usage pattern seen in the hello_sh.sh example.

