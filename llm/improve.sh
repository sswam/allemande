#!/bin/bash

# [file] "instructions to improve it" [reference files ...]
# Improve something using AI

improve() {
	local model= m=      # model
	local style= s=0     # refer to hello-<ext> for style
	local guidance= g=1  # refer to lang/guidance.md for style
	local prompt= p=     # extra prompt
	local edit= e=1      # open an editor after the AI does it's work
	local use_ai= a=1    # use AI, can turn off for testing with -a=0
	local concise= c=0   # concise
	local basename= b=0  # use basenames
	local test= t=1      # run tests if found (default: on)
	local testok= T=0    # tests are okay, don't change
	local codeok= C=0    # code is okay, don't change
	local changes= S=1   # allow changes to existing functionality or API changes
	local features= F=1  # allow new features
	local lint= L=1      # run linters and type checkers if possible
	local format= F=1    # format code
#	local writetest= w=1 # write tests if none found
	local numline= n=    # number lines
	local strict= X=1    # only do what is requested
	local ed= E=0        # provide changes as an ed script
	local diff= d=0      # provide changes as a unified diff
	local think= t=1     # encourage thinking
	local funcs= f=()    # process only listed functions

	eval "$(ally)"

	local file=$1
	local prompt2=${2:-}
	shift 2 || shift 1 || true
	local refs=("$@")

	prompt="${prompt:+$prompt }${prompt2}"

	if ((basename)); then
		opt_b=("-b")
	else
		opt_b=()
	fi

	if ((diff || ed)) && [ "$numline" = "" ]; then
		numline=1
	fi

	if ((numline)); then
		opt_n=("--number-lines")
	else
		opt_n=()
	fi

	# -C or -T options imply -t
	if ((codeok)) || ((testok)); then
		test=1
	fi

	# Check if the file exists
	if [ ! -e "$file" -o -d "$file" ]; then
		local prog2=$(which "$file")
		if [ ! -e "$prog2" ]; then
			echo >&2 "not found: $file"
			exit 1
		fi
		file=$prog2
	fi

	# resolve symlinks
	file=$(readlink -f "$file")

	# files and directories
	local dir=$(dirname "$file")
	local base=$(basename "$file")
	#	local name=${base%.*}
	local ext=${file##*.}
	if [ "$ext" == "$base" ]; then
		ext="sh"
	fi

	# Results file for checks and tests
	local results_file="$dir/.$base.results.txt"
	if [ -e "$results_file" ]; then
		move-rubbish "$results_file"
	fi

	checks_prompt=""

	# Reformat code
	if ((format)); then
		{ formy "$file" || true; } | tee -a "$results_file"
	fi

	# Lint and type check
	if ((lint)); then
		{ linty "$file" || true; } | tee -a "$results_file"
	fi

	# Find and run tests
	local tests_file=""
	local test_ext="bats"
	local temp_results_file=$(mktemp)

	if ((test)); then
		testy "$file" | tee "$temp_results_file" || true
		tests_file=$(head -n 1 "$temp_results_file")
		tail -n +2 "$temp_results_file" >>"$results_file"
		rm "$temp_results_file"
	fi
	# remove empty results file
	if [ -e "$results_file" ] && [ ! -s "$results_file" ]; then
		rm -f "$results_file"
	fi

	if [ -e "$results_file" ]; then
		echo >&2 "Checks failed: $results_file"
		refs+=("$results_file")
		check_msg="With check issues, please either fix the issue, or disable the warning with a comment."
		if ((testok)); then
			checks_prompt="Some checks failed. The tests are CORRECT, you MUST NOT CHANGE THEM; please fix the main program code. $check_msg"
		elif ((codeok)); then
			checks_prompt="Some checks failed. The main program code is CORRECT, you MUST NOT CHANGE IT; please fix the tests."
		else
			checks_prompt="Some checks failed. Please fix the program and/or the tests. If the code looks correct as it is, please update the tests to match the code, or vice versa. $check_msg"
		fi
	elif [ "$tests_file" ]; then
		echo >&2 "Checks passed"
		checks_prompt="Our checks passed."
		rm -f "$results_file"
	elif ((test)); then
		echo >&2 "No tests found"
		test=""
	fi

	if [ -n "$tests_file" ] && [ "$tests_file" != "$file" ]; then
		refs+=("$tests_file")
	fi

	# guidance reference and prompt for -g --guidance option
	guidance_ref="guidance-$ext.md"
	if ((guidance)) && [ "$(which-file "$guidance_ref")" ]; then
		echo >&2 "Using guidance reference: $guidance_ref"
		refs+=("$guidance_ref")
		prompt="refer to \`$guidance_ref\`, $prompt"
	fi

	# style reference and prompt for -s --style option
	if [ -n "$ext" ]; then
		style_ref="$ALLEMANDE_HOME/$ext/hello_$ext.$ext"
		if ((style)) && [ -e "$style_ref" ]; then
			echo >&2 "Using style reference: $style_ref"
			refs+=("$style_ref")
			prompt="use the style of \`$style_ref\`, $prompt"
		fi
	fi

	files_to_edit='`'"$base"'`'
	if [ -f "$tests_file" ] && [ -s "$tests_file" ]; then
		if ((codeok)); then
			files_to_edit='`'"$(basename "$tests_file")"'`'
		elif ((!testok)); then
			files_to_edit+='and/or `'"$(basename "$tests_file")"'`'
		fi
	fi

	strict_part=""
	if [ -z "$prompt" ] && [ -z "$checks_prompt" ]; then
		prompt="Please improve"
		strict=0
	elif ((strict)) && [ -n "$prompt" ]; then
		prompt="*** MAIN TASK: $prompt ***"
		strict_part="Please perform the *** MAIN TASK *** requested above. Secondarily, please fix any certain bugs or issues. Do not make other proactive changes at this time. Do not remove any comments."
	elif ((strict)); then
		prompt=""
		strict_part="Please fix any certain bugs or issues. Do not make other proactive changes at this time."
	else
		prompt="*** TASK: $prompt ***"
	fi

	if [ "$think" = 1 ]; then
		prompt="$prompt  If necessary, and only where necessary, please think before and during your response, using <think> containers. For simple things, or when you already know the answer, it won't be necessary to think, and it saves the user money if you don't! Don't think for too long unless it seems important, or the user asks you to. When thinking, focus on generating new insights rather than restating the obvious parts of the question."
	fi

	# TODO "Add a header line \`#File: filename\` before each file's code."

	prompt="Please edit $files_to_edit. $prompt
	$strict_part
	You may comment on other issues you see, or ideas you have.
	$checks_prompt.
	Bump the patch version if present. Don't add comments to mark your changes, only if a comment is needed going forward."

	if ((changes == 0)); then
		prompt="$prompt. Strictly no changes to existing functionality or APIs."
	fi

	if ((features == 0)); then
		prompt="$prompt. Strictly no new features."
	fi

	if ((concise)); then
		prompt="$prompt, Please reply concisely with only the changes."
	fi

	if ((numline)); then
		prompt="$prompt, Lines are numbered for your convenience, but please do not number lines in your output."
	fi

	if ((diff)); then
		prompt="$prompt
	Please provide the changes as a unified diff patch. Use the following format:
	\`\`\`diff
	--- filename
	+++ filename
	@@ -start,count +start,count @@
	 context line
	-removed line
	+added line
	 context line
	\`\`\`
	Include the \`\`\` around the diff. Try to include minimal context (about 3 lines) around the changes."
	fi

	if ((ed)); then
		prompt="$prompt
	Please provide the changes as minimal ed scripts, one per file, for example:
	\`\`\`ed filename
	3,5c
	hello world
	.
	\`\`\`
	Include the \`\`\` around the ed commands. Try not to include many unchanged lines.
	You can use the a c i d s commands with single lines or ranges.
	Return the changes in order from top to bottom if possible. I will sort the changes in reverse order before applying them, so you don't have to worry about earlier changes affecting later line numbers.
	Be super careful that your line numbers match the original code you want to replace. I numbered the lines for you, so there's no excuse! :)
	"
	fi

	local target_file="$file"

	local input
	if [ ${#funcs[@]} -gt 0 ]; then
		target_file="$file.funcs"
		input=$(
			echo "#File: $(basename "$file")"
			echo "#Functions: ${funcs[*]}"
			func "$file" "${funcs[@]}" | tee "$target_file"
			cat-named -p -b "${refs[@]}"
			v cat-named -p -S $'\n' "${opt_b[@]}" "${opt_n[@]}" "${refs[@]}"
		)
	else
		input=$(v cat-named -p -S $'\n' "${opt_b[@]}" "${opt_n[@]}" "$file" "${refs[@]}")
	fi

	# Backup original file
	if [ -e "$file.new" ]; then
		move-rubbish "$file.new"
	fi
	# shellcheck disable=SC2216
	echo n | cp-a-ignore-time-errors -i "$file" "$file.new" # WTF, there's no proper no-clobber option?!

	comment_char="#"
	case "$ext" in
	c | cpp | java | js | ts | php | cs | go | rs)
		comment_char="//"
		;;
	sh | py | pl | rb)
		comment_char="#"
		;;
	md | txt)
		comment_char=""
		;;
	esac

	output_file="$file.changes"

	# By default, it should edit the main code.
	# if using -C option, it must edit the tests, so the output file is the tests file plus a tilde
	if ((codeok)) && [ -n "$tests_file" ]; then
		target_file="$tests_file"
		output_file="$tests_file.changes"
	fi

	if ((use_ai == 0)); then
		function process() { nl; }
	fi

	# Process input and save result
	printf "%s\n" "$input" | process -m="$model" "$prompt" |
		if [ -n "$comment_char" ]; then
			markdown-code -F -c "$comment_char"
		else
			cat
		fi >"$output_file"

	# check not empty
	if [ ! -s "$output_file" ]; then
		echo >&2 "empty output"
		rm "$output_file"
		exit 1
	fi

	# make the file executable if appropriate
	chmod-x-shebang "$output_file"

	# Compare original and improved versions
	if ((edit)); then
		if [ -n "$tests_file" ] && ((!codeok)); then
			vim -d "$output_file" "$target_file" -c "botright vnew $tests_file"
		else
			vimdiff "$output_file" "$target_file"
		fi
	fi

	# auto-apply
	applied=0
	if auto_apply; then
		applied=1
	fi

	if [ ${#funcs[@]} -gt 0 ] && ((applied)); then
		confirm func-replace "$file" <"$target_file" && return
	fi
	if [ ${#funcs[@]} -gt 0 ]; then
		confirm func-replace "$file" <"$output_file" && return
	fi

	if ((applied)); then
		return
	fi

	# if using -t but not -C or -T, it may edit the code and/or the tests, so we don't automatically replace the old version with the new one
	confirm="true"
	if ((test)) && ((codeok == 0)) && ((testok == 0)); then
		confirm="confirm -t" # means it might have edited either or both files
	fi

	cycle_3_files() {
		local a=$1 b=$2 c=$3
		if ! $confirm "Update $a -> $b -> $c ?"; then
			return 1
		fi
		move-rubbish "$target_file.old" 2>/dev/null || true
		cp -a "$target_file" "$target_file.old"
		cat "$output_file" >"$target_file"  # preserve inode and mode of target_file
		move-rubbish "$output_file"
	}

	# Swap in the hopefully improved version
	cycle_3_files "$output_file" "$target_file" "$target_file.old" ||
	if [ "$confirm" ] && [ "$target_file" = "$file" ] && [ -n "$tests_file" ] && ((!codeok)); then
		cycle_3_files "$output_file" "$tests_file" "$tests_file.old"
	fi

	# In the case that it edited both files, the user should have figured it out in their editor,
	# we can't handle that automatically yet.
}

auto_apply() {
	echo >&2 "test: $test codeok: $codeok testok: $testok"
	echo >&2 "tests_file: $tests_file exists? $(test -e "$tests_file" && echo yes || echo no)"

	if ((test)) && ((codeok == 0)) && ((testok == 0)) && [ -e "$tests_file" ]; then
		confirm -t apply -c="$output_file" "$target_file" "$tests_file" && return
	fi

	if ((test)) && ((codeok == 1)) && ((testok == 0)) && [ -e "$tests_file" ]; then
		confirm -t apply -c="$output_file" "$tests_file" && return
	fi

	if ((codeok == 0)); then
		confirm -t apply -c="$output_file" "$target_file" && return
	fi
	return 1
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	improve "$@"
fi

# version: 3.0.0
