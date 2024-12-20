#!/bin/bash
PARALLEL_MAX=8
run() {
	local f=$1
	v llm process 'Please add a symbol (industry), (tourism), (government) [e.g. information, emergency servies...], (education), (organization) or (other) to each row. If a business sounds like a tourist destination, put it in (tourism), otherwise (industry); for other nouns or whatever use (other). Please also eliminate duplicates of the same thing, and use the best canonical name. Thanks for being awesome!' < "$f" > "$f.cat"
}
for f in both/* industry/* tourism/*; do
	. para run "$f"
done
wait
