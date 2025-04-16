#!/bin/bash -eu
venv=${1%/}

find "$venv" -name __pycache__ | xargs rm -rf --

old=`< "$venv/bin/activate" sed -n '/^\s*VIRTUAL_ENV=/ { s/^\s*VIRTUAL_ENV=//; s/"'\''//g; p; }'`
new=`readlink -f "$venv"`

old2="(`basename "$old"`)"
new2="(`basename "$venv"`)"

if [ "$old" = "$new" ]; then
	echo "venv paths are already set correctly to $new"
else
	files=`fgrep -I -r "$old" "$venv" -l`
	echo "$files"
	echo "Replace $old with $new in the above files?"
	read -p "[yn] ? " YN
	if [ "$YN" = y ]; then
		echo "$files" | xargs --no-run-if-empty sed -i "s:$old:$new:g"
	fi

	files=`fgrep -I -r "$old2" "$venv"/bin/activate* -l`
	echo "$files"
	echo "Replace $old2 with $new2 in the above files?"
	read -p "[yn] ? " YN
	if [ "$YN" = y ]; then
		echo "$files" | xargs --no-run-if-empty sed -i "s:$old2:$new2:g" 
	fi
fi
