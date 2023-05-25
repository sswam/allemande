#!/usr/bin/make -f

# TODO: archives
# TODO: urls, download HTML, PDF, youtube, video, etc
# TODO: email attachments

INPUT_FILES=$(shell find input -type f)

# from input/foo.wav to work/foo.wav.txt
TEXT_FILES=$(addsuffix .txt,$(INPUT_FILES))
WORK_FILES=$(addprefix work/,$(notdir $(TEXT_FILES)))

SUMMARY_FILES=$(addprefix summary/,$(notdir $(WORK_FILES)))

WHISPER=whisp  # speech recognition engine

SHELL=/bin/bash

.PHONY: goal mkdirs outputs

goal: mkdirs | output.zip outputs

mkdirs:
	mkdir -p input work summary

work/%: input/%
	same -s $< $@

%.html.txt: %.html
	w3m -dump $< > $@
%.html: %.htm
	ln $< $@

%.pdf.txt: %.pdf
	pdftotext $< $@

%.txt: %.office
	antiword $< > $@

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

%.txt: %.16k.wav
	$(WHISPER) --output_format txt $<

%.aud: %.vid
	ffmpeg -i $< -f wav $@

%.img.ocr.txt: %.img
	ocr $< > $@
%.img.desc.txt: %.img
	image2text.py -i $< > $@
%.txt: %.img.ocr.txt %.img.desc.txt
	catpg $^ > $@

summary/%.txt: work/%.txt
	words=`wc -w < $<`; \
	if [ $$words -gt 5000 ]; then model=c+; else model=4; fi; \
	echo >&2 "model: $$model"; \
	llm process -m $$model "$$(< $(PROG_DIR)/summary.prompt)" < $< > $@

summary.txt: $(SUMMARY_FILES)
	cat-sections $^ > $@

output.md: summary.txt mission.txt
	llm process -m 4 "$$(< mission.txt)" < $< > $@

output.%: output.md
	pandoc $< --latex-engine=xelatex -t latex -o $@

outputs: output.md output.pdf output.html output.docx

output.zip: outputs $(SUMMARY_FILES) summary.txt $(WORK_FILES) $(INPUT_FILES)
	zip -r $@ output.md output.pdf output.html output.docx summary.txt summary inputs

.PRECIOUS: %.txt

%.doc.office: %.doc
	same -s $< $@
%.docx.office: %.docx
	same -s $< $@
%.ppt.office: %.ppt
	same -s $< $@
%.pptx.office: %.pptx
	same -s $< $@
%.odt.office: %.odt
	same -s $< $@

%.md.txt: %.md
	same -s $< $@

%.csv.txt: %.csv
	same -s $< $@
%.tsv.txt: %.tsv
	same -s $< $@
%.json.txt: %.json
	same -s $< $@
%.xml.txt: %.xml
	same -s $< $@
%.yaml.txt: %.yaml
	same -s $< $@

%.mp3.aud: %.mp3
	same -s $< $@
%.ogg.aud: %.ogg
	same -s $< $@
%.wav.aud: %.wav
	same -s $< $@
%.flac.aud: %.flac
	same -s $< $@

%.mp4.vid: %.mp4
	same -s $< $@
%.mkv.vid: %.mkv
	same -s $< $@
%.mov.vid: %.mov
	same -s $< $@
%.avi.vid: %.avi
	same -s $< $@
%.m4v.vid: %.m4v
	same -s $< $@
%.webm.vid: %.webm
	same -s $< $@

%.jpg.img: %.jpg
	same -s $< $@
%.jpeg.img: %.jpeg
	same -s $< $@
%.png.img: %.png
	same -s $< $@
%.gif.img: %.gif
	same -s $< $@
%.webp.img: %.webp
	same -s $< $@
