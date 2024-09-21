#!/bin/bash -eu
. confirm
m=
folder=$1
mkdir -p "$(dirname "$folder")"
imap_fetch.py -r -f "$folder"  | tee "$folder".txt
for A in "$folder"/*; do
	< "$A" email_clean.py |
		remove_links.py
		echo; echo
done |
	tee "${folder}-text.txt"
echo -n "token count: "
llm count -m=$m < "${folder}-text.txt"
summarize() {
	proc -m=$m "Please give an executive overview of these emails for me ($USER), combining info from several emails where appropriate." < "${folder}-text.txt" |
		tee "$folder"-summary.txt
}
confirm summarize
