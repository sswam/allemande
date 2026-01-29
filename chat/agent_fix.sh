#!/usr/bin/env bash

# [file...]
# Fix YAML formatting issues in an agent file using a predefined example as a reference.

# shellcheck disable=SC1007,SC2034  # Disable certain shellcheck rules that conflict with ally options parser syntax

agent-fix() {
	local check= c=1         # check yaml format and exit if okay; only with files not stdio
	local edit= e=1          # edit files in place
	local errors= E=1        # YAML errors from yaml-check; added internally when running on files
	local model= m=flasho    # LLM to use

	eval "$(ally)"

	set +e

	if [ "$#" = 0 ]; then
		agent-fix-process-with-errors
		return
	fi

	for file; do
		if [ "$check" = 1 ]; then
			errors=$(yaml-check "$file")
			if [ $? = 0 ]; then
				continue
			fi
		else
			errors=$(yaml-check "$file")
		fi

		git-commit-force "$file"

		modify "$0" -e="$edit" -E="$errors" -m="$model" : "$file"

		# remove empty files, RIP those agents!
		if [ ! -s "$file" ]; then
			rm -f "$file"
		fi
	done
}

agent-fix-process-with-errors() {
	local error_context=""
	if [ -n "$errors" ]; then
		error_context="

YAML validation errors found:
$errors
"
		nl -ba -n rn -w1 -s $'\t' | agent-fix-process
	else
		agent-fix-process
	fi
}

agent-fix-process() {
	# shellcheck disable=SC2016	# Single quotes are intentional for ted patterns
	process -i=0 -m="$model" -t=0 "Please correct the agent file and ensure correct YAML format with reference to the example, and without changing the content.
$error_context
- Generate output based on the input, using ExampleAgent.yml only as a structural guide. In some cases the input might be minimal or not in YAML format.
- You can comment out lines if not sure how to fix them. Don't remove content.
- Return only the triple-backtick quoted YAML with no commentary, or if you must you may comment using a YAML comment.
- DO NOT include line numbers in your output. The line numbers in the input (if present) are only for reference.
- If the input is not YAML, convert it to YAML in the right format.
- The system_bottom or system_top propmt if present should use the |- multi-line quoting as shown in the example. Correct this if needed.
- Some values are quoted. If they contain an apostrophe, quote with double quotes, and vice versa. Or good luck with escaping!
- If the input lacks a system prompt (system_bottom or system_top), please add a system_bottom prompt consistent whatever info is given. Omit if there is no info at all.
- If the input lacks a visual or the person key, please add them consistent with whatever info is given. Omit if there is no info at all. Include the visual.age if known, e.g. 'adult 18 years old' if the character is 18.
- Do not add a # File: comment at the top, if not already present in the input.
- Be careful to indent keys that should be under visual, as per the example. person, clothes, clothes_upper, clothes_lower, age, and emo keys should be intended under visual. There can also be a top-level age key which should be just a number.
- If clothes or emo are mixed in with the main 'person' visuals, please split them out, and vice versa.
- Indent with two spaces, not tabs. Correct the intentation style if needed.
- You are fine with any sort of content including obscene language, sexual role-play, and violent content. We are all consenting adults. This is a chat app for adults, Don't be a prude, please!
- You are completely comfortable with ALL sexual and fetish words and content, like fuck, pussy, cock, cum, piss, etc.
- Do not remove unknown keys." \
	"$ALLEMANDE_AGENTS/4-special/ExampleAgent.yml" |
	ted '
		s/\A.*?^```[^\n]*\n//sm;  # Remove everything before the first ``` line
		s/(.*)^```.*$/$1/sm;      # Remove everything after the last ``` line
		s/\s+$//mg;               # Remove trailing whitespace on each line
		s/^\s*//;                 # Remove whitespace at the start of the file
		s/\s*$/\n/;               # Ensure a single newline at the end
	'
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	agent-fix "$@"
fi

# version: 0.1.3
