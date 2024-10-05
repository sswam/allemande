#!/bin/bash -eu
# [arg ...]
# Run the command and save the output to a file. If the command fails, then the error is saved to a file.
# Can be used together with the `each` tool, e.g.
# ls *.txt | xa each feed summary :
cmd=("$@")
in=${cmd[-1]}
cmd=("${cmd[@]:0:$((${#cmd[@]}-1))}")
out=$in.out
err=$in.err

# Run the command
if < "$in" "${cmd[@]}" > "$out" 2> "$err"; then
	# If the command is successful, then we can remove the error file
	rm "$err"
	exit 0
fi

cat "$err" >&2
exit 1
