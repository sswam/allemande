#!/bin/bash
# i3-tree-simple: print the layout of the current i3 tree simply

what="name"
out="tree"

while getopts "tjyh" opt; do
	case $opt in
		t)
			what="type, $what"
			;;
		j)
			out="json"
			;;
		y)
			out="yaml"
			;;
		h)
			echo "Usage: $0 [-t|-h]"
			echo "  -t: show the type of each node"
			echo "  -j: output json instead of yaml"
			echo "  -h: show this help"
			exit 0
			;;
	esac
done
shift $((OPTIND-1))

main() {
	i3-msg -t get_tree |
	jq "$@" "
		def simplify: {$what} + if (.nodes | length) > 0 then {nodes: (.nodes | map(simplify)?)} else {} end;
		simplify
	"
}

yaml() {
	main | yq -y -w 10000
}

filter() {
	perl -ne '
		s/^(\s*)- name: /$1- /;
		print if !/^ *nodes:$/;
	'
}

if [ "$out" = "json" ]; then
	main -C
elif [ "$out" = "yaml" ]; then
	yaml
elif [ "$out" = "tree" ]; then
	yaml | filter
fi | less -R
