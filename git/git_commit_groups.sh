#!/usr/bin/env bash
#
# Group files for committing together, with AI help.

git_group_files() {
	local model= m=	# LLM model
	local max_diff_lines= M=40	# maximum number of lines in a diff to show

	eval "$(ally)"

	junk=$(junk-files)

	if [ -n "$junk" ]; then
		echo "Likely junk files detected:"
		echo "$junk"
		confirm -o move-rubbish $junk
	fi

	rundown_file=$(mktemp /tmp/git_group_files_rundown.XXXXXX)
	bad_file=$(mktemp /tmp/git_group_files_bad.XXXXXX)
	llm_input_file=$(mktemp /tmp/git_group_files_llm_input.XXXXXX)
	commit_plan=$(mktemp /tmp/git_group_files_commit_plan.XXXXXX)

	git-mod | rundown 2>"$bad_file" | tee "$rundown_file"

	if [ -s "$bad_file" ]; then
		echo "Bad files detected:"
		cat "$bad_file" >&2
		confirm "continue?"
	fi

	(
		git status

		echo "Brief rundown of files:"
		cat "$rundown_file"

		echo "Changes to files:"
		(
			git-mod staged-modified
			git-mod unstaged-modified
		) | while read -r file; do
			if [ ! -e "$file" ]; then
				printf "File \`%s\` was removed.\n\n" "$file"
				continue
			fi
			diff=$(git diff "$file")
			lines=$(printf "%s\n" "$diff" | wc -l)
			if [ "$lines" -le "$max_diff_lines" ]; then
				printf "File \`%s\` was changed:\n\n" "$file"
				printf "%s\n\n" "$diff"
			else
				printf "File \`%s\` was greatly changed, the diff is %d lines, too long to show here.\n\n" "$file" "$lines" >&2
			fi
		done
	) | tee "$llm_input_file"

	${PAGER:-pager} "$llm_input_file"

	echo "Token count and cost:"
	llm count --in-cost -m="$model" <"$llm_input_file"

	confirm "continue?"

	< "$llm_input_file" process -m="$model" "Please group these changed or new files into batches for committing together.
We should commit changes to closely related files together, I guess.

The output should be file names grouped together in batches on each line, separated by tabs.
The order of the lines is not important. You can also add comments after a # character if necessary.
Do not add any prelude or comments unless you use the # character.

For example:

code/prog.py	code/tests/prog_test.py
code/prog2.py	code/tests/prog2_test.py
code/untested.py
code/foo
# code/foo is new and sounds like a junk file
" | tee "$commit_plan"

	$EDITOR "$commit_plan"

	confirm "commit using messy-xterm?"

	< "$commit_plan" grep -v -e '^\s*$' -e '^#' | sed 's/\s*#.*//' | messy-xterm

	rm -f "$rundown_file" "$bad_file" "$llm_input_file"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	git_group_files "$@"
fi

# version: 0.1.1
