#!/usr/bin/env bash

# [options] target [source|old new]
# Apply changes from source document to target document in translated form using LLM-generated ed script

# shellcheck disable=SC1007,SC2034  # Disable certain shellcheck rules that conflict with ally options parser syntax

transpatch() {
	local git_mode= g=         # git diff mode: target source
	local diff_mode= d=        # diff mode: target old new
	local prompt= p=           # extra prompt
	local model= m=            # LLM model
	local edit= e=1            # edit the ed script before applying
	local confidence= C=       # ask LLM to rate confidence on each change
	local draft= D=            # ask LLM to make multiple drafts
	local context= c=5         # lines of context for diffs

	eval "$(ally)"

	local target source old_source new_source diff_input numbered_target

	# Determine mode and validate arguments
	if [ "$git_mode" = 1 ]; then
		if [ "$#" -ne 2 ]; then
			die "git mode requires exactly 2 arguments: target source"
		fi
		target="$1"
		source="$2"

		if [ ! -f "$target" ]; then
			die "target file not found: $target"
		fi
		if [ ! -f "$source" ]; then
			die "source file not found: $source"
		fi

		# Get git diff of source
		diff_input=$(git diff -U"$context" "$source" 2>/dev/null || git diff -U"$context" /dev/null "$source")

	elif [ "$diff_mode" = 1 ]; then
		if [ "$#" -ne 3 ]; then
			die "diff mode requires exactly 3 arguments: target old new"
		fi
		target="$1"
		old_source="$2"
		new_source="$3"

		if [ ! -f "$target" ]; then
			die "target file not found: $target"
		fi
		if [ ! -f "$old_source" ]; then
			die "old source file not found: $old_source"
		fi
		if [ ! -f "$new_source" ]; then
			die "new source file not found: $new_source"
		fi

		# Get diff between old and new source
		diff_input=$(diff -U"$context" "$old_source" "$new_source")

	else
		# Default mode: target from arg, diff from stdin
		if [ "$#" -ne 1 ]; then
			die "default mode requires exactly 1 argument: target"
		fi
		target="$1"

		if [ ! -f "$target" ]; then
			die "target file not found: $target"
		fi

		# Read diff from stdin
		diff_input=$(cat)
	fi

	# Create numbered version of target
	numbered_target=$(nl -ba -n rn -w1 -s $'\t')

	# Build the prompt
	local system_prompt="You are an expert at generating ed(1) scripts to apply changes to files.

IMPORTANT: You must output a valid ed(1) script in a markdown code block: \`\`\`\`\`ed
...script here...
\`\`\`\`\`

Note the 5 backticks: this is to support ed scripts containing text or patterns with 3 or 4 backtick quoting.

Before the code block, you may use a <think></think> section to reason through the changes if needed.
After or between sections, you may add commentary, but the ed(1) script itself must be in the code block.

The script will be extracted and piped directly to ed(1), so please make sure it's syntactically perfect :)

You can use standard ed commands and GNU extensions:
- Line addressing: 1, \$, /pattern/, 1,5
- Commands: a (append), c (change), d (delete), i (insert), s (substitute)
- Global: g/pattern/command
- Move: m, Copy: t

Be extremely careful with:
- Line numbers (they change after deletions/insertions)
- Pattern escaping
- Multi-line changes (use backslash continuation)

The target document is shown with line numbers. Apply the changes from the source diff/instructions to the target document.
Work from bottom to top when possible to avoid line number shifts.
Preserve the formatting and indentation conventions of the target document.
End with 'w' to write and 'q' to quit.

TRIPLE-CHECK YOUR SCRIPT BEFORE OUTPUTTING!"

	local confidence_prompt=""
	if [ "$confidence" = 1 ]; then
		confidence_prompt="

For each significant change, add a comment in the ed script like: # Confidence: 8/10 - reason"
	fi

	local draft_prompt=""
	if [ "$draft" = 1 ]; then
		draft_prompt="

Consider multiple approaches and refine your ed script before giving the final version."
	fi

	local user_prompt="Source changes/diff:

$diff_input

---

Target document with line numbers:

$numbered_target

---

Generate an ed(1) script to apply the appropriate changes from the source to the target.$prompt$confidence_prompt$draft_prompt"

	# Generate ed script using LLM and save directly to file
	printf "%s" "$user_prompt" | query -m="$model" -s="$system_prompt" > "$target.ed.md"

	if [ ! -s "$target.ed.md" ]; then
		die "LLM generated empty output"
	fi

	# Extract ed script from markdown code block to file
	local ed_script_file="$target.ed"
	sed -n '/`````ed/,/`````/p' "$target.ed.md" | sed '1d;$d' > "$ed_script_file"

	if [ ! -s "$ed_script_file" ]; then
		rm -f "$ed_script_file"
		die "Could not extract ed script from LLM output (saved in $target.ed.md)"
	fi

	# Interactive edit mode
	if [ "$edit" = 1 ]; then
		"${EDITOR:-vi}" "$ed_script_file"
	fi

	# Apply the ed script
	ed -s "$target" < "$ed_script_file" 2>&1 | tee "$target.ed.out" || die "ed script failed to apply"

	echo >&2 "Successfully applied changes to $target"
	echo >&2 "Full LLM output saved in $target.ed.md"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	transpatch "$@"
fi

# version: 0.2.0
