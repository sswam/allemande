#!/usr/bin/make -f

# I have an info directory with HTML and PDF files in it. I want to make a
# list of .txt files with the same stem in the info directory.

HTML_FILE_EXTENSIONS=html htm
PDF_FILE_EXTENSION=pdf
OFFICE_FILE_EXTENSIONS=doc docx ppt pptx odt
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

WHISPER=whisp  # speech recognition engine

SHELL=/bin/bash

.PHONY: goal

goal: output.zip outputs

%.html.txt: %.html
	w3m -dump $< > $@
%.html: %.htm
	ln -s $< $@

%.pdf.txt: %.pdf
	pdftotext $< $@

%.txt: %.office
	antiword $< > $@
%.doc.office: %.doc
	ln -s $< $@
%.docx.office: %.docx
	ln -s $< $@
%.ppt.office: %.ppt
	ln -s $< $@
%.pptx.office: %.pptx
	ln -s $< $@
%.odt.office: %.odt
	ln -s $< $@

%.md.txt: %.md
	ln -s $< $@

%.csv.txt: %.csv
	ln -s $< $@
%.tsv.txt: %.tsv
	ln -s $< $@
%.json.txt: %.json
	ln -s $< $@
%.xml.txt: %.xml
	ln -s $< $@
%.yaml.txt: %.yaml
	ln -s $< $@
%.xls.txt: %.xls
	xlsx2csv $< > $@
%.xlsx.txt: %.xlsx
	xlsx2csv $< > $@

# email: forget about attachments for now
# ripmime -i $< -d output

%.eml.txt: %.eml
	mail -f $< -N decode > $@

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

%.16k.wav: %.aud
	sox $< -r 16k -e signed -b 16 -c 1 $@
%.mp3.aud: %.mp3
	ln -s $< $@
%.ogg.aud: %.ogg
	ln -s $< $@
%.wav.aud: %.wav
	ln -s $< $@
%.flac.aud: %.flac
	ln -s $< $@

%.txt: %.16k.wav
	$(WHISPER) --output_format txt $<

%.aud: %.vid
	ffmpeg -i $< -f wav $@
%.mp4.vid: %.mp4
	ln -s $< $@
%.mkv.vid: %.mkv
	ln -s $< $@
%.mov.vid: %.mov
	ln -s $< $@
%.avi.vid: %.avi
	ln -s $< $@
%.m4v.vid: %.m4v
	ln -s $< $@
%.webm.vid: %.webm
	ln -s $< $@

%.jpg.img: %.jpg
	ln -s $< $@
%.jpeg.img: %.jpeg
	ln -s $< $@
%.png.img: %.png
	ln -s $< $@
%.gif.img: %.gif
	ln -s $< $@
%.webp.img: %.webp
	ln -s $< $@
%.img.ocr.txt: %.img
	ocr $< > $@
%.img.desc.txt: %.img
	image2text.py -i $< > $@
%.txt: %.img.ocr.txt %.img.desc.txt
	catpg $^ > $@

summary/%.txt: input/%.txt
	mkdir -p summary
	words=`wc -w < $<`; \
	if [ $$words -gt 5000 ]; then model=c+; else model=4; fi; \
	echo >&2 "model: $$model"; \
	llm process -m $$model "$$(< $(PROG_DIR)/summary.prompt)" < $< > $@

full_input.txt: $(SUMMARY_FILES)
	cat-sections $^ > $@

output.md: full_input.txt mission.txt
	llm process -m 4 "$$(< mission.txt)" < $< > $@

output.%: output.md
	pandoc $< -o $@

outputs: output.md output.pdf output.html output.docx

output.zip: outputs $(SUMMARY_FILES) full_input.txt $(TEXT_FILES) $(INPUT_FILES)
	zip -r $@ output.md output.pdf output.html output.docx full_input.txt summary inputs

.PRECIOUS: %.txt
