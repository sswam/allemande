#!/usr/bin/env bats

# Tests for transpatch.sh

setup() {
	cd "$BATS_TEST_TMPDIR"

	# Stub debug (no-op)
	debug() { :; }

	# Stub die to behave like the project's die (exit current shell)
	die() { echo "$*" >&2; exit 1; }

	# Minimal ally stub: leave args unchanged, keep defaults
	ally() {
		# Output shell that does nothing, preserving "$@"
		cat <<'EOF'
true
EOF
	}

	# Stub query to produce controllable LLM output
	# Accepts -m= and -s= options but ignores them
	query() {
		while [ $# -gt 0 ]; do
			case "$1" in
				-m=*|-s=*) shift ;;
				*) break ;;
			esac
		done
		case "${QUERY_MODE:-good}" in
			good)
				cat <<'EOF'
<think>Apply simple substitution on line 2.</think>

``
EOF
				;;
			empty)
				# Produce nothing (empty output)
				;;
			nocode)
				echo "Some commentary but no ed code block."
				;;
			*)
				echo "Unknown QUERY_MODE: ${QUERY_MODE}" >&2
				;;
		esac
	}

	# Provide a minimal "ed" implementation sufficient for our tests,
	# so the tests do not depend on system ed availability.
	# Supports:
	# - address substitution like: 2s/OLD/NEW/
	# - w (write), q (quit)
	ed() {
		local silent= target
		if [ "$1" = "-s" ]; then
			silent=1
			shift
		fi
		target="$1"
		if [ -z "$target" ] || [ ! -f "$target" ]; then
			echo "?" >&2
			return 1
		fi

		# Read the ed script
		local script
		script=$(cat)

		# Work on a temp copy
		local tmp="$target.tmp"
		cp "$target" "$tmp" || return 1

		# Process script line by line
		while IFS= read -r line; do
			case "$line" in
				# Simple pattern: <number>s/<old>/<new>/
				([0-9]*s/*)
					local addr rest old new
					addr=${line%%s/*}
					rest=${line#*s/}
					old=${rest%%/*}
					rest=${rest#*/}
					new=${rest%%/*}
					# Apply substitution on that specific line
					awk -v n="$addr" -v old="$old" -v new="$new" '
						NR==n { gsub(old, new) } { print }
					' "$tmp" > "$tmp.new" || { rm -f "$tmp" "$tmp.new"; return 1; }
					mv "$tmp.new" "$tmp"
					;;
				(w)
					cp "$tmp" "$target" || { rm -f "$tmp" "$tmp.new"; return 1; }
					;;
				(q)
					# quit: nothing special needed here in stub
					:
					;;
				(*)
					# Ignore unsupported commands in this stub
					:
					;;
			esac
		done <<< "$script"

		rm -f "$tmp" "$tmp.new"
		return 0
	}

	# Ensure a non-interactive editor
	export EDITOR=true

	# Source the script under test without invoking it
	source "$BATS_TEST_DIRNAME/transpatch.sh"
}

@test "applies generated ed script in default (stdin) mode" {
	# Arrange
	cat > target.txt <<'EOF'
Hello
World
EOF
	export QUERY_MODE=good

	# Act
	run transpatch target.txt <<< "diff --git a/source b/source
@@ -1,2 +1,2 @@
-Hello
-World
+Hello
+There
"
	# Assert
	[ "$status" -eq 0 ]
	# Check target content changed
	run cat target.txt
	[ "$output" = $'Hello\nThere' ]

	# Check artifacts exist
	[ -f target.txt.ed ]
	[ -s target.txt.ed ]
	[ -f target.txt.ed.md ]
	[ -s target.txt.ed.md ]
	[ -f target.txt.ed.out ]
	[ -s target.txt.ed.out ]

	# Check success message mentions target
	[[ "$stderr" == *"Successfully applied changes to target.txt"* ]]
}

@test "fails when target file not found (default stdin mode)" {
	export QUERY_MODE=good
	run transpatch does-not-exist.txt <<< "irrelevant diff"
	[ "$status" -ne 0 ]
	[[ "$stderr" == *"target file not found: does-not-exist.txt"* ]]
}

@test "fails when LLM (query) returns empty output" {
	# Arrange
	echo -e "Hello\nWorld" > target.txt
	export QUERY_MODE=empty

	# Act
	run transpatch target.txt <<< "irrelevant diff"
	# Assert
	[ "$status" -ne 0 ]
	[[ "$stderr" == *"LLM generated empty output"* ]]
}

@test "fails when no ed code block can be extracted" {
	# Arrange
	echo -e "Hello\nWorld" > target.txt
	export QUERY_MODE=nocode

	# Act
	run transpatch target.txt <<< "irrelevant diff"
	# Assert
	[ "$status" -ne 0 ]
	[[ "$stderr" == *"Could not extract ed script from LLM output"* ]]
}
