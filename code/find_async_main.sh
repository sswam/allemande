#!/usr/bin/env bash
# 
# Find async main functions that are called from main.go
qe grep main.go */* |
	perl -ne '/(.*?):\s*main\.go\((.*?)(,|\))/ && print "$1\t$2\n"' |
	while read file func; do
		grep -H "async def $func" "$file"
       	done |
		sed 's/:/\t/' |
			grep -v -e '^canon/' -e '^alias/'
