#!/usr/bin/make -f

# TODO: archives
# TODO: urls, download HTML, PDF, youtube, video, etc
# TODO: email attachments

INPUT_FILES=$(shell find input -type f)

TEXT_FILES=$(addsuffix .txt,$(INPUT_FILES))
WORK_FILES=$(addprefix w/,$(notdir $(TEXT_FILES)))

SUMMARY_FILES=$(addprefix summary/,$(notdir $(WORK_FILES)))

OUTPUTS=output.md output.pdf output.docx output.html

WHISPER=whisp  # speech recognition engine

SHELL=/bin/bash


.PHONY: goal mkdirs

goal: mkdirs | output.zip $(OUTPUTS)

mkdirs:
	mkdir -p input w summary

w/%: input/%
	same -s $< $@

w/%.html.txt: w/%.html
	w3m -dump $< > $@
w/%.html: w/%.htm
	ln $< $@

w/%.pdf.txt: w/%.pdf
	pdftotext $< $@

w/%.txt: w/%.office
	antiword $< > $@

w/%.xls.txt: w/%.xls
	xlsx2csv $< > $@
w/%.xlsx.txt: w/%.xlsx
	xlsx2csv $< > $@

# email: forget about attachments for now
# ripmime -i $< -d output

w/%.eml.txt: w/%.eml
	mail -f $< -N decode > $@

w/%.msg.txt: w/%.msg
	mail -f $< -N decode > $@
w/%.mbox.txt: w/%.mbox
	mail -f $< -N decode > $@

w/%.pst.txt: w/%.pst
	readpst -o output $<
	mv output/Inbox.mbox.txt $@
w/%.ost.txt: w/%.ost
	readpst -o output $<
	mv output/Inbox.mbox.txt $@

w/%.16k.wav: w/%.aud
	sox $< -r 16k -e signed -b 16 -c 1 $@

w/%.txt: w/%.16k.wav
	$(WHISPER) --output_format txt --output_dir w $<
	mv w/$$(basename $< .16k.wav).16k.txt $@

w/%.aud: w/%.vid
	ffmpeg -i $< -f wav $@

w/%.img.ocr.txt: w/%.img
	ocr $< > $@
w/%.img.desc.txt: w/%.img
	image2text.py -i $< > $@
w/%.txt: w/%.img.ocr.txt w/%.img.desc.txt
	catpg $^ > $@

summary/%.txt: w/%.txt
	words=`wc -w < $<`; \
	if [ $$words -gt 5000 ]; then model=c+; else model=4; fi; \
	echo >&2 "model: $$model"; \
	llm process -m $$model "$$(< $(PROG_DIR)/summary.prompt)" < $< > $@

summary.txt: $(SUMMARY_FILES)
	cat-sections $^ > $@

output.md: summary.txt mission.txt
	llm process -m 4 "$$(< mission.txt)" < $< > $@

output.%: output.md
	pandoc $< --pdf-engine=xelatex -o $@

output.zip: mission.txt $(OUTPUTS) summary.txt input w summary
	zip -r $@ $^

.PRECIOUS: %

w/%.doc.office: w/%.doc
	same -s $< $@
w/%.docx.office: w/%.docx
	same -s $< $@
w/%.ppt.office: w/%.ppt
	same -s $< $@
w/%.pptx.office: w/%.pptx
	same -s $< $@
w/%.odt.office: w/%.odt
	same -s $< $@

w/%.md.txt: w/%.md
	same -s $< $@

w/%.csv.txt: w/%.csv
	same -s $< $@
w/%.tsv.txt: w/%.tsv
	same -s $< $@
w/%.json.txt: w/%.json
	same -s $< $@
w/%.xml.txt: w/%.xml
	same -s $< $@
w/%.yaml.txt: w/%.yaml
	same -s $< $@

w/%.mp3.aud: w/%.mp3
	same -s $< $@
w/%.ogg.aud: w/%.ogg
	same -s $< $@
w/%.wav.aud: w/%.wav
	same -s $< $@
w/%.flac.aud: w/%.flac
	same -s $< $@

w/%.mp4.vid: w/%.mp4
	same -s $< $@
w/%.mkv.vid: w/%.mkv
	same -s $< $@
w/%.mov.vid: w/%.mov
	same -s $< $@
w/%.avi.vid: w/%.avi
	same -s $< $@
w/%.m4v.vid: w/%.m4v
	same -s $< $@
w/%.webm.vid: w/%.webm
	same -s $< $@

w/%.jpg.img: w/%.jpg
	same -s $< $@
w/%.jpeg.img: w/%.jpeg
	same -s $< $@
w/%.png.img: w/%.png
	same -s $< $@
w/%.gif.img: w/%.gif
	same -s $< $@
w/%.webp.img: w/%.webp
	same -s $< $@
