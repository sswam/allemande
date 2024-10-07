#!/bin/bash
# i3-get-workspace-info: get the name of the current workspace

what="some"
while getopts "nh" opt; do
	case $opt in
		n)
			what="name"
			;;
		h)
			echo "Usage: $0 [-n|-h]"
			echo "  -n: show just the name of the workspace"
			echo "  -h: show this help"
			exit 0
			;;
	esac
done
shift $((OPTIND-1))

i3-msg -t get_workspaces | jq -r "
	.[] | select(.focused==true) |
	if \"$what\" == \"name\" then
		.name
	else
		.
	end
"
