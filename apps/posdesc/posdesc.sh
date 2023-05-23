#!/bin/bash -eu
# posdesc: generate a position description from a set of documents

pos="Executive Director of Bongotronics International. The candidate should be strong in web development, graphic design, community management, IT admininstration, network administation, people skills and politics."
template="template.txt"

for A in *.pdf; do pdftotext "$A" ; done

mkdir -p dp

for A in *.txt; do < "$A" gpt process "Please summarize the requirements for this position description without omitting anything, in dot point form" >dp/"$A"; done

for try in `seq 1 3`; do
	cat dp/*.txt | gpt process "Please produce a comprehensive single position description from these documents, with detailed dot points, maybe 1 or 2 pages of markdown. The position is $pos Please add details around these requirements also. Follow the outline format of this document:
	TEMPLATE DOCUMENT:
	`cat "$template"`
	END TEMPLATE DOCUMENT" | tee pos-desc-$try.md

	pandoc pos-desc-$try.md -o pos-desc-$try.docx
done
