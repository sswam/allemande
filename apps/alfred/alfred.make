#!/usr/bin/make -f

# TODO: archives
# TODO: urls, download HTML, PDF, docx, youtube, video, etc
# TODO: email attachments

SHELL=/bin/bash
export

INPUT_FILES=$(shell find input -type f -not -name '*.url')

TEXT_FILES=$(addsuffix .txt,$(INPUT_FILES))
WORK_FILES=$(addprefix w/,$(notdir $(TEXT_FILES)))

SUMMARY_FILES=$(addprefix summary/,$(notdir $(WORK_FILES)))

WHISPER=whisp

IMAGE2TEXT_MODE=best

LLM_MODEL_LONG=c+
LLM_MODEL_SUMMARY=4
LLM_MODEL_SUMMARY_MEGA=4
LLM_MODEL_BRAINY=4
OCR_MODEL=4
LLM_MODEL_TOKENS_MAX=8192
LLM_MODEL_TOKENS_FOR_RESPONSE=2048
LLM_MODEL_TOKENS_MAX_QUERY=$(shell echo $$[ $(LLM_MODEL_TOKENS_MAX) - $(LLM_MODEL_TOKENS_FOR_RESPONSE) ])
TOPIC=

summary_prompt=Please summarize this info regarding the topic: $(TOPIC), using markdown dot-point form. Be as comprehensive and factual as possible, but fairly concise without omiting anything relevant. Avoid repetition. Only Include info relevant to the topic: $(TOPIC). There may be a lot of other crap in the input document such as website boilerplate links and stuff. Please include relevant links (only) in [Markdown Hyperlink](https://en.wikipedia.org/wiki/Markdown\#Hyperlinks) format.

MISSIONS_IN=$(wildcard mission.*.in.txt)
MISSIONS=$(patsubst %.in.txt,%.txt,$(MISSIONS_IN))

# missions are like mission.1.txt
# output_md files are like output.1.md
# so we need to replace mission -> output at the start of the filename

HTML=1
PDF=1
DOCX=1

OUTPUTS_MD=$(patsubst mission.%.txt,output.%.md,$(MISSIONS))
OUTPUTS_HTML=$(patsubst mission.%.txt,output.%.html,$(MISSIONS))
OUTPUTS_PDF=$(patsubst mission.%.txt,output.%.pdf,$(MISSIONS))
OUTPUTS_DOCX=$(patsubst mission.%.txt,output.%.docx,$(MISSIONS))

OUTPUTS:=$(OUTPUTS_MD)

ifeq ($(HTML),1)
	OUTPUTS:=$(OUTPUTS) $(OUTPUTS_HTML)
endif
ifeq ($(PDF),1)
	OUTPUTS:=$(OUTPUTS) $(OUTPUTS_PDF)
endif
ifeq ($(DOCX),1)
	OUTPUTS:=$(OUTPUTS) $(OUTPUTS_DOCX)
endif

HTML_DUMP_FILTER=cat

.PHONY: goal mkdirs

goal: mkdirs | output.zip $(OUTPUTS)

mkdirs:
	mkdir -p input w summary

w: $(WORK_FILES)
	mkdir -p $@
	touch $@

w/%: input/%
	same -s $< $@

w/%.html.txt: w/%.html w/%.url
	# lynx -dump -base "$$(< w/$*.url)" $< > $@
	# w3m -dump $< > $@
	pandoc-dump "$<" $$(<w/$*.url) | $(HTML_DUMP_FILTER) > "$@"

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
	ffmpeg -i $< -ar 16000 -acodec pcm_s16le -ac 1 $@

w/%.txt: w/%.16k.wav
	$(WHISPER) --output_format txt --output_dir w $<
	mv w/$$(basename $< .16k.wav).16k.txt $@

w/%.aud: w/%.vid
	ffmpeg -i $< -f wav $@

w/%.img.ocr.txt: w/%.img
	ocr -m=$(OCR_MODEL) $< $@
w/%.img.desc.txt: w/%.img
	image2text.py -m $(IMAGE2TEXT_MODE) -i $< > $@
w/%.txt: w/%.img.ocr.txt w/%.img.desc.txt
	( printf "## Image Text:\n\n" ; \
	cat w/$*.img.ocr.txt ; \
	printf "\n## Image Description:\n\n" ; \
	cat w/$*.img.desc.txt ) > $@

summary/%.txt: w/%.txt
	sleep .$$RANDOM
	model= ; \
	tokens=`llm count -m $(LLM_MODEL_SUMMARY) < $<`; \
	echo >&2 "tokens: $$tokens"; \
	if [ $$tokens = 0 ]; then echo >&2 "empty input: $<"; > $@; \
	elif [ $$tokens -gt $(LLM_MODEL_TOKENS_MAX_QUERY) ]; then model=$(LLM_MODEL_LONG); else model=$(LLM_MODEL_SUMMARY); fi; \
	echo >&2 "model: $$model"; \
	if [ -n "$$model" ]; then llm process -m $$model "$(summary_prompt)" < $< > $@ ; fi

summary.txt: $(SUMMARY_FILES)
	cat-sections $^ > $@

summary-condensed.txt: summary.txt
	sleep .$$RANDOM
	tokens=`llm count -m $(LLM_MODEL_SUMMARY_MEGA) < $<`; \
	echo >&2 "tokens: $$tokens"; \
	if [ $$tokens -gt $(LLM_MODEL_TOKENS_MAX_QUERY) ]; then model=$(LLM_MODEL_LONG); else model=$(LLM_MODEL_SUMMARY_MEGA); fi; \
	echo >&2 "model: $$model"; \
	llm process -m $$model "$(summary_prompt)" < $< > $@

#mission.txt:
#	if [ -z "$(mission)" ]; then \
#		read -p "Enter the mission:" mission; \
#	fi; \
#	printf "%s\n" "$$mission" > $@

output.%.md: summary-condensed.txt mission.%.txt
	echo >&2 "mission: $$mission"
	sleep .$$RANDOM
	< summary-condensed.txt llm process -m $(LLM_MODEL_BRAINY) "$$(< mission.$*.txt)" < $< > $@

output.%.html: output.%.md
	pandoc $< --pdf-engine=xelatex -o $@
output.%.pdf: output.%.md
	pandoc $< --pdf-engine=xelatex -o $@
output.%.docx: output.%.md
	pandoc $< --pdf-engine=xelatex -o $@

output.zip: $(MISSIONS) $(OUTPUTS) summary.txt summary-condensed.txt input w summary
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

w/%.txt.txt: w/%.txt
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
