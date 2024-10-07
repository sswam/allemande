#!/bin/bash
# i3-get-window-info: get info about the currently focused window

what="some"
while getopts "nah" opt; do
	case $opt in
		n)
			what="name"
			;;
		a)
			what="all"
			;;
		h)
			echo "Usage: $0 [-n|-a|-h]"
			echo "  -n: show just the name of the window"
			echo "  -a: show all info about the window"
			echo "  -h: show this help"
			exit 0
			;;
	esac
done
shift $((OPTIND-1))

i3-msg -t get_tree | jq -r "
	recurse(.nodes[]) | select(.focused==true) |
	if \"$what\" == \"name\" then
		.name
	elif \"$what\" == \"some\" then
		(.window_properties | {title,class,instance})+.rect
	else
		.
	end
"
