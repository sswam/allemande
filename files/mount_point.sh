#!/bin/bash
A=${1:-.}
if [ ! -d "$A" ]; then
	A=$(dirname "$A")
fi
findmnt -n -o TARGET --target "$A"
