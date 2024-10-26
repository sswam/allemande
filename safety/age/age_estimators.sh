#!/bin/bash -eu
confirm "Generate age estimation programs?"
< age-estimation-google.txt grep -v -i civit | while IFS=$'\t' read A B C; do
	create -s=0 -m=prof "$A".py "Please write a script using $B from huggingface. Usage would be Image pathnames on stdin, one per line, output detected info on stdout in TSV, with the filename in the right-most column of output. TSV header is not necessary. Refer to the example script for code style and try to follow it closely. Relevant URL: $C" age_estimate_civitai.py
done
