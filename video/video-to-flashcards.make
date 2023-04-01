#!/usr/bin/make -f

img_rate=1

# threads=$(shell nproc)

MAKEFILE_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
export PATH := $(MAKEFILE_DIR):$(PATH)


SHELL := /bin/bash
WHISPER_MODEL := large

m=4


transcript.sent.txt: transcript.txt
	< $< split_sentences > $@

transcript.sent2.txt: transcript.sent.txt
	< $< ai_split_long_sentences.py > $@



default: goal

web-address.txt:
	if [ -n "$(url)" ]; then \
		echo "$(url)" >$@; \
		else read -p "Enter URL: " url; \
		echo $$url >$@; \
	fi

video.webm: web-address.txt
	yt-dlp -q -f bestvideo -o "$@" "`<$<`"
	if [ ! -e "$@" ]; then mv -i "$@".* "$@"; fi
	if [ -e "$@" ]; then touch $@; fi

audio.webm: web-address.txt
	yt-dlp -q -f bestaudio -o "$@" "`<$<`"
	if [ ! -e "$@" ]; then mv -i "$@".* "$@"; fi
	if [ -e "$@" ]; then touch $@; fi

av.webm: video.webm audio.webm
	ffmpeg -loglevel error -i video.webm -i audio.webm -c copy $@
	if [ ! -e "$@" ]; then mv -i "$@".* "$@"; fi

title.txt: web-address.txt
	web-title "`<web-address.txt`" >$@

# get images from the video, one every $img_rate seconds
images: video.webm
	mkdir -p images
	ffmpeg -loglevel error -i $< -vf fps=1/$(img_rate) -qscale:v 2 images/%06d.jpeg

audio-extract: av
	ffmpeg -loglevel error -i $< -vn -c copy $@

audio.txt: audio.webm
	whisper --language en --model $(WHISPER_MODEL) $<

transcript.md: transcript.txt
	< $< nl | (echo "| n | line |"; sed 's/^ *//') | tsv2markdown >$@

audio-clean.txt: audio.txt
	< $< tr -d '♪' | strip-lines.py | squeeze-blank-lines 1 > $@

summary.txt: audio-clean.txt
	< $< gpt_summary -m=$m > $@

name.txt: audio-clean.txt
	if [ -n "$(name)" ] ; then \
		echo "$(name)" > $@ ; \
	else \
		< $< gpt_process -m=$m "Please respond with just the name or a suitable name for the following:" > $@ ; \
	fi

topic.txt: audio-clean.txt
	< $< gpt_topic -m=$m > $@

flashcards-1.txt: audio-clean.txt
	< $< gpt_flashcards -m=$m > $@

flashcards.txt: flashcards-1.txt
	(< $< sed 's/^Prompt:/\n&/' | sed '1{/^$$/d}'; echo) | single_blank_lines > $@

flashcards.tsv: flashcards.txt
	< $< recs2tsv | grep '\S' > $@

correct.prompt:
	ln -s `wich correct.prompt` .

prompt-transcript.txt: audio-clean.txt correct.prompt
	CONTENT=`< $<` shell-template correct.prompt > $@

transcript.txt: prompt-transcript.txt
	< $< gpt_process -m=$m "Please reply with just the corrected transcript." > $@


# We could also search to find the title or canonical page.


search-lyrics.txt: name.txt
	search "\"`< name.txt`\" lyrics or transcript" > $@

lyrics-url.txt: search-lyrics.txt name.txt
	< $< gpt_process -m=$m "Please reply with just the best URL to get lyrics or a transcript for `<name.txt`, based on these search results or your knowledge. If nothing looks promising, just reply 'about:blank'." > $@

lyrics.html: lyrics-url.txt
	wg "`< $<`" -O- >$@ || true

lyrics-page.txt: lyrics.html
	w3m -dump $< > $@ || true

extract.prompt:
	ln -s `wich extract.prompt`

prompt-lyrics.txt: lyrics-page.txt extract.prompt
	if [ ! -s $< ]; then \
		echo "No lyrics found." ; > $@ ; \
	else \
		CONTENT=`< $<` shell-template extract.prompt > $@ ; \
	fi

lyrics.txt: prompt-lyrics.txt name.txt
	if [ ! -s $< ]; then \
		echo "No lyrics found." ; > $@ ; \
	else \
		< $< gpt_process -m=$m "Please reply with just the lyrics or transcript for `<name.txt`, based on the page `<lyrics-url.txt`." > $@ ; \
	fi

post.txt: title.txt web-address.txt name.txt topic.txt summary.txt flashcards.txt transcript.txt lyrics.txt
	cat-sections.py $^ > $@

%.words.txt: %.txt
	< $< words-split.py > $@

diff: transcript.words.txt audio-clean.words.txt lyrics.words.txt 
	vimdiff $^

goal: post.txt flashcards.tsv # images


.PRECIOUS:
.VIRTUAL: default
