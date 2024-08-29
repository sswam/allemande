#!/bin/bash -eu
folder=$1
./imap_fetch.py -r -f INBOX/$folder  | tee $folder.txt
for A in INBOX/$folder/*; do
	< "$A" ./email_clean.py |
		./remove_links.py
		echo; echo
done |
proc -m=4 "Let's have an executive overview of these emails, a few points for each." | tee $folder-summary.txt
