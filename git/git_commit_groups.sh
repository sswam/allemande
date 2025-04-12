#!/usr/bin/env bash
#
# Group files for committing together, with AI help.

git_commit_groups() {
	local model= m=gp   # LLM model
	local ci_model= c=  # LLM model for commit messages
	local max_diff_lines= M=40	# maximum number of lines in a diff to show

	eval "$(ally)"

	cd "$(git-root)"

	junk=$(junk-files)

	if [ -n "$junk" ]; then
		echo "Likely junk files detected:"
		echo "$junk"
		confirm -o move-rubbish $junk || true
	fi

	rundown_file=$(mktemp /tmp/git_commit_groups_rundown.XXXXXX)
	bad_file=$(mktemp /tmp/git_commit_groups_bad.XXXXXX)
	llm_input_file=$(mktemp /tmp/git_commit_groups_llm_input.XXXXXX)
	commit_plan=$(mktemp /tmp/git_commit_groups_commit_plan.XXXXXX)

	git-mod | rundown --number-headers 2>"$bad_file" | tee "$rundown_file"

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
			diff=$(git diff HEAD -- "$file")
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
We usually commit different programs separately, even if they are in the same folder.
If the changes are similar or serve a common purpose across several programs or files, we commit them together.
Do not use any globbing or abbreviations in the output, we need to include each filename exactly.

The output should be file names grouped together in batches on each line, separated by tabs.
The order of the lines is not important. You can also add comments after a # character if necessary.
Do not add any prelude or comments unless you use the # character.
Please list the numbers of the files you have included in a leftmost column, comma separated.

For example:

1,2	code/prog.py	code/tests/prog_test.py	# prog and its tests
3,4	code/prog2.py	code/tests/prog2_test.py	# prog2 and its tests
5	code/untested.py	# untested
6	code/foo	# code/foo is new, sounds like a junk file
" | tee "$commit_plan"

	move-rubbish "$rundown_file" "$bad_file" "$llm_input_file"

	$EDITOR "$commit_plan"

	confirm "commit using messy-screen?"

	< "$commit_plan" sed -n 's/^[0-9, ]*[[:space:]]*//; s/\s*#.*//; /\S/p' | messy-screen -a="$ci_model"
	screen -x ci

	move-rubbish "$commit_plan"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	git_commit_groups "$@"
fi

# version: 0.1.1
