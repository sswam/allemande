#!/usr/bin/env bash
# Convert the Australian Curriculum website to markdown
# Mathematical Methods Units 1, 2, 3, 4

. confirm

confirm= c=0	# confirm AI processing
keep= k=0	# keep intermediate files

eval "$(ally)"

llm-text-to-markdown() {
	< unit$u-crop.txt process -m=4 "Please completely convert the entire document, in clean markdown with TeX for the math, with heading levels 1, 2 and 3 only. There are some line breaks / paragraph breaks in the input that should not be there. Any markdown format is fine, please do your best." > unit$u.md
}

for u in 1 2 3 4; do
	echo "Unit $u"
	wget -O unit$u.html "https://australiancurriculum.edu.au/senior-secondary-curriculum/mathematics/mathematical-methods/?unit=Unit+$u"
	flip -b -u "unit$u.html"
	< unit$u.html htmldebloater | htmlsplit | sed 's/^<.*//' > unit$u.txt
	< unit$u.txt text-strip | squeeze-blank-lines | sed -n "/^Unit $u Description$/,/^Follow ACARA:$/p" | head -n -1 > unit$u-crop.txt
	if (( confirm )); then
		less unit$u-crop.txt
		confirm -t llm-text-to-markdown
	else
		llm-text-to-markdown
	fi
	if (( keep == 0 )); then
		rm unit$u.html unit$u.txt unit$u-crop.txt
	fi
done
