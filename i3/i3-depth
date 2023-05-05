#!/bin/bash
# i3-depth: get the depth of the current focused window in i3
# workspace is 0
# top-level window is 1
i3-msg -t get_tree |
jq '
	path(recurse(.nodes[]) |
	select(.focused==true)) |
	map(select(type == "number")) |
	length-3
'
