#!/bin/bash -eu
folder=$1
mkdir -p "$(dirname "$folder")"
imap_fetch.py -r -f "$folder"  | tee "$folder".txt
for A in "$folder"/*; do
	< "$A" email_clean.py |
		remove_links.py
		echo; echo
done |
proc -m=4 "Let's have an executive overview of these emails, combining info from several emails where appropriate." | tee "$folder"-summary.txt
