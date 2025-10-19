#!/usr/bin/env bash
# Fix YAML formatting issues in an agent file using a predefined example as a reference.

if [ "$#" = 0 ]; then
	process -i=0 -m=gf -t=0 "Please correct the agent file and ensure correct YAML format with reference to the example, and without changing the content.

- Generate output based on the input, using ExampleAgent.yml only as a structural guide. In some cases the input might be minimal or not in YAML format.
- You can comment out lines if not sure how to fix them. Don't remove content.
- Return only the triple-backtick quoted YAML with no commentary, or if you must you may comment using a YAML comment.
- If the input is not YAML, convert it to YAML in the right format.
- The system_bottom or system_top propmt if present should use the |- multi-line quoting as shown in the example. Correct this if needed.
- Some values are quoted. If they contain an apostrophe, quote with double quotes, and vice versa. Or good luck with escaping!
- If the input lacks a system prompt (system_bottom or system_top), please add a system_bottom prompt consistent whatever info is given. Omit if there is no info at all.
- If the input lacks a visual or the person key, please add them consistent with whatever info is given. Omit if there is no info at all. Include the visual.age if known, e.g. 'adult 18 years old' if the character is 18.
- Do not add a # File: comment at the top, if not already present in the input.
- Be careful to indent keys that should be under visual, as per the example. person, clothes, clothes_upper, clothes_lower, age, and emo keys should be intended under visual. There can also be a top-level age key which should be just a number.
- Indent with two spaces, not tabs. Correct the intentation style if needed.
- Do not remove unknown keys." \
	"$ALLEMANDE_AGENTS/special/ExampleAgent.yml" |
	ted '
		s/\A.*?^```[^\n]*\n//sm;  # Remove everything before the first ``` line
		s/(.*)^```.*$/$1/sm;      # Remove everything after the last ``` line
		s/\s+$//mg;               # Remove trailing whitespace on each line
		s/^\s*//;                 # Remove whitespace at the start of the file
		s/\s*$/\n/;               # Ensure a single newline at the end
	'
else
	modify "$0" : "$@"
	for file; do
		if [ ! -s "$file" ]; then
			rm -f "$file"
		fi
	done
fi
