#!/usr/bin/make -f

# I have an info directory with HTML and PDF files in it. I want to make a
# list of .txt files with the same stem in the info directory.

EXTRA_HMTL_FILES=$(wildcard extra/*.html)
EXTRA_PDF_FILES=$(wildcard extra/*.pdf)
EXTRA_TEXT_FILES=$(patsubst %.html,%.txt,$(EXTRA_HTML_FILES)) $(patsubst %.pdf,%.txt,$(EXTRA_PDF_FILES))

IKIGAI_MODEL=claude-v1

SHELL=/bin/bash

.PHONY: goal

goal: resume4.html resume.css

ikigai.chat: info.txt $(PROG_DIR)/ikigai.prompt
	> $@
	cat $(PROG_DIR)/ikigai.prompt >> $@
	echo "	Some info about me:" >> $@
	< info.txt sed 's/^/\t/' >> $@
	llm-chat-ed -m=$(IKIGAI_MODEL) $@

ikigai.txt: ikigai.chat
	< $< llm process -m 4 "Please summarize the following chat about ikigai in structured markdown with dotpoint lists and perhaps other markdown features, to help with preparing a resume. Focus on the agreed possible ikigai, findings, and other final thoughts not so much on the process." | tee $@

extra.txt: $(EXTRA_TEXT_FILES)
	# if no extras, just blank
	echo > extra.txt
#	if [ -z "$(EXTRA_TEXT_FILES)" -o "$(EXTRA_TEXT_FILES)" = " " ]; then \
#		echo "" > $@; \
#	else \
#		catpg -break=$$'\n----\n' $^ | llm process -m 4 "Please summarize the additional info in the following files in structured markdown with dotpoint lists, to help with preparing a resume." | tee $@ \
#	fi

#info.txt: ikigai.chat resume.txt supplementary.txt
#	cat $< | llm process -m 4 "Please fill in the following information about yourself." | tee $@

%.txt: %.pdf
	pdftotext $<
	cat $@

%.txt: %.html
	w3m -dump $< > $@
	cat $@

%.txt: %.doc
	antiword $< > $@
	cat $@

info.txt: resume.txt
	< $< llm process -m 4 "Please summarize the most important points from the following resume in structured markdown with dotpoint lists. Include name, skills, hobbies, interests, but not so much detailed job and education history." | tee $@


suggest-%.txt: resume.txt
	< $< llm process -m $* "Please read my resume and suggest how we can improve it, in a step by step plan." | tee $@

plan.txt: suggest-4.txt suggest-c.txt suggest-3+.txt
	catpg -break=$$'\n----\n' $^ | llm process -m 4 "Please combine these three lists of suggestions to improve a resume, into one step-by-step plan without any repetition." | tee $@

form.txt: resume.txt plan.txt ikigai.txt extra.txt
	(catpg -break=$$'\n----\n' $^ ; date +"It is now %b %Y, might need to add recent work etc.") | \
		llm process -m 4 "$$(<$(PROG_DIR)/form.prompt)" | tee $@

form-filled.txt: form.txt
	cp $< $@
	$$EDITOR $@

report.md: form-filled.txt ikigai.txt
	cat-sections.py $^ > $@

resume2.md: resume.txt plan.txt report.md
	catpg -break=$$'\n----\n' $^ | llm process -m 4 "Please revise this resume based on the plan and addition info provided, in markdown format." | tee $@

resume3.md: resume2.md
	< $< markdown-cleanup.py > $@

resume3.html: resume3.md
	pandoc -s -o $@ $<

resume4.html: resume3.html
	< $< llm process -m 4 "Please modify this HTML removing the inline stylesheet and adding classes for various things, and add a link to use resume.css." | tee $@

resume.css: resume4.html
	< $< llm process -m 4 "Please write a CSS stylesheet resume.css for this resume to make it look awesome." | tee $@
