#!/bin/bash -eu
# [file ...]
# AI critique a program

m=	# model
s=0	# short critique
p=	# prompt

. opts

short=$s
prompt=$p

critique() {
	if (( short )); then
		short=" *very* short"
	else
		short=""
	fi
	prompt="Please provide a$short critique.
Start with a paragraph of friendly and supportive praise if possible...
the author needs to retain some self-esteem\!
It's important to find errors.
Please also suggest creative ideas,
including unusual or 'out of the box' ones.
Other suggestions are welcome too.
$prompt"
	main_file="${1:--}"
	shift || true
	cat-named -b -p "$main_file" "$@" |
	(process -m="$m" "$prompt"; echo) |
	tee -a -- "$main_file.crit"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	critique "$@"
fi



# Prompting ideas to improve critique:
# - look for code that should be split off into a reusable function library

# Old long prompts, might need some ideas?
#	process "Please critique this program code, like a code review. Let me know how you like it, and suggest ways that we can improve it, possibly including code style, clarity, simplicity, generality, comments, and functionality. You might suggest adding or removing features. Don't actually rewrite the code for me, but you can show some code snippets."
#	process "Please review this program code as if conducting a code review. Provide both positive feedback and constructive criticism. Evaluate aspects such as code style, clarity, simplicity, generality, comments, and functionality. Suggest improvements or additional features, and identify any potential security or performance issues. Prioritize your suggestions. Don't rewrite the entire code, but you may include short code snippets to illustrate specific points. If relevant, consider adherence to [SPECIFIC CODING STANDARD]."
