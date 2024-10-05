#!/usr/bin/env bash

# Says Hello, world

use_ai=0
model=""

while getopts "am:" opt; do
	case $opt in
	a)	use_ai=1 ;;
	m)	model="$OPTARG" ;;
	*)	exit 1 ;;
	esac
done
shift $((OPTIND-1))

user_name=${1:-world}

case "${LANGUAGE:0:2}" in
fr)	greeting="Bonjour" ;;
es)	greeting="Hola" ;;
de)	greeting="Hallo" ;;
jp)	greeting="こんにちは" ;;
cn)	greeting="你好" ;;
en|*)	greeting="Hello" ;;
esac

if [ "$use_ai" = 1 ]; then
	query -m="$model" "Please greet ${user_name} in $LANGUAGE. Be creative, but not more than 50 words."
else
	printf -- "%s, %s\n" "$greeting" "$user_name"
fi

if [ -t 0 ]; then
	echo -e "\nEnter shopping list items (one per line, Ctrl+D to finish):"
fi

shopping_list=$(cat)

if [ -n "$shopping_list" ]; then
	echo -e "\nShopping list:"
	if [ "$use_ai" = 1 ]; then
		echo "$shopping_list" | process -m="$model" "Please echo the input and add any extra items we might need, in $LANGUAGE."
	else
		echo "$shopping_list"
	fi
fi
