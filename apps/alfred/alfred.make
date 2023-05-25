#!/usr/bin/make -f

# I have an info directory with HTML and PDF files in it. I want to make a
# list of .txt files with the same stem in the info directory.

DOCUMENT_FILE_EXTENSIONS=html htm pdf doc docx ppt pptx odt
TEXT_FILE_EXTENSIONS=txt md
DATA_FILE_EXTENSIONS=csv tsv json xml yaml xls xlsx
EMAIL_FILE_EXTENSIONS=eml msg mbox pst ost
AUDIO_FILE_EXTENSIONS=mp3 ogg wav flac
VIDEO_FILE_EXTENSIONS=mp4 mkv mov avi m4v webm
IMAGE_FILE_EXTENSIONS=jpg jpeg png gif webp

# TODO: archives
# TODO: forget about attachments for now
# TODO: urls, download HTML, PDF, youtube, video, etc

# find all input files with any of those extensions, under input/
INPUT_FILES=$(shell find input -type f)

# for each input file, make a txt version by appending .txt
TEXT_FILES=$(addsuffix .txt,$(INPUT_FILES))

SUMMARY_FILES=$(addprefix summary/,$(notdir $(TEXT_FILES)))

WHISPER=whisp --output_format txt  # speech recognition engine

SHELL=/bin/bash

.PHONY: goal

goal: output.md output.pdf output.html output.docx

%.html.txt: %.html
	w3m -dump $< > $@
%.htm.txt: %.htm
	w3m -dump $< > $@
%.pdf.txt: %.pdf
	pdftotext $< $@
%.doc.txt: %.doc
	antiword $< > $@
%.docx.txt: %.docx
	antiword $< > $@
%.ppt.txt: %.ppt
	antiword $< > $@
%.pptx.txt: %.pptx
	antiword $< > $@
%.odt.txt: %.odt
	antiword $< > $@
%.txt.txt: %.txt
	cp $< $@
%.md.txt: %.md
	cp $< $@

%.csv.txt: %.csv
	cp $< $@
%.tsv.txt: %.tsv
	cp $< $@
%.json.txt: %.json
	cp $< $@
%.xml.txt: %.xml
	cp $< $@
%.yaml.txt: %.yaml
	cp $< $@
%.xls.txt: %.xls
	xlsx2csv $< > $@
%.xlsx.txt: %.xlsx
	xlsx2csv $< > $@

%.eml.txt: %.eml
	mail -f $< -N decode > $@
	# forget about attachments for now
	# ripmime -i $< -d output
%.msg.txt: %.msg
	mail -f $< -N decode > $@
%.mbox.txt: %.mbox
	mail -f $< -N decode > $@
%.pst.txt: %.pst
	readpst -o output $<
	mv output/Inbox.mbox.txt $@
%.ost.txt: %.ost
	readpst -o output $<
	mv output/Inbox.mbox.txt $@

%.mp3.txt: %.mp3
	sox $< -t raw -r 16k -e signed -b 16 -c 1 - | $(WHISPER) > $@
%.ogg.txt: %.ogg
	sox $< -t raw -r 16k -e signed -b 16 -c 1 - | $(WHISPER) > $@
%.wav.txt: %.wav
	sox $< -t raw -r 16k -e signed -b 16 -c 1 - | $(WHISPER) > $@
%.flac.txt: %.flac
	sox $< -t raw -r 16k -e signed -b 16 -c 1 - | $(WHISPER) > $@

%.mp4.txt: %.mp4
	ffmpeg -i $< -f wav - | sox -t wav - -t raw -r 16k -e signed -b 16 -c 1 - | $(WHISPER) > $@
%.mkv.txt: %.mkv
	ffmpeg -i $< -f wav - | sox -t wav - -t raw -r 16k -e signed -b 16 -c 1 - | $(WHISPER) > $@
%.mov.txt: %.mov
	ffmpeg -i $< -f wav - | sox -t wav - -t raw -r 16k -e signed -b 16 -c 1 - | $(WHISPER) > $@
%.avi.txt: %.avi
	ffmpeg -i $< -f wav - | sox -t wav - -t raw -r 16k -e signed -b 16 -c 1 - | $(WHISPER) > $@
%.m4v.txt: %.m4v
	ffmpeg -i $< -f wav - | sox -t wav - -t raw -r 16k -e signed -b 16 -c 1 - | $(WHISPER) > $@
%.webm.txt: %.webm
	ffmpeg -i $< -f wav - | sox -t wav - -t raw -r 16k -e signed -b 16 -c 1 - | $(WHISPER) > $@

%.jpg.txt: %.jpg
	image-to-text $< > $@
%.jpeg.txt: %.jpeg
	image-to-text $< > $@
%.png.txt: %.png
	image-to-text $< > $@
%.gif.txt: %.gif
	image-to-text $< > $@
%.webp.txt: %.webp
	image-to-text $< > $@

summary/%.txt: input/%.txt
	words=`wc -w < $<`; \
	if [ $$words -gt 5000 ]; then model=c; else model=4; fi; \
	llm process -m $$model "$$(< $(PROG_DIR)/summary.prompt)" < $< > $@

full_input.txt: $(SUMMARY_FILES)
	cat-sections $^ > $@

output.md: full_input.txt mission.txt
	llm process -m 4 "$$(< mission.txt)" < $< > $@

output.%: output.md
	pandoc $< -o $@
