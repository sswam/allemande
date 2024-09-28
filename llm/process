#!/bin/bash -eu
m=
I=	# don't fix indentation
. opts
process_main() {
	llm process -m "$m" "${@:-""}" | rstrip
}
if [ "$I" ]; then
	process_main "$@"
else
	input=$(cat)
	indent=$(printf "%s\n" "$input" | aligno --detect)
	printf "%s\n" "$input" | process_main "$@" | aligno --apply "$indent"
fi
