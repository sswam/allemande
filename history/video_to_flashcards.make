#!/usr/bin/make -sf

img_rate=1

# threads=$(shell nproc)

default: goal

url.txt:
	read -p "Enter URL: " url; echo $$url >$@

video.webm: url.txt
	yt-dlp -f bestvideo+bestaudio -o $@ $(shell cat $<)
	touch $@

# get images from the video, one every $img_rate seconds
images: video.webm
	mkdir -p images
	ffmpeg -i $< -vf fps=1/$(img_rate) -qscale:v 2 images/%06d.jpeg

audio.webm: video.webm
	ffmpeg -i $< -vn -c copy $@

audio.txt: audio.webm
	whisper $<

summary.txt: audio.txt
	< $< chatgpt_summary > $@

topic.txt: audio.txt
	< $< chatgpt_topic > $@

flashcards.txt: audio.txt
	< $< chatgpt_flashcards > $@

post.txt: topic.txt summary.txt flashcards.txt
	catpg $^ > $@

goal: post.txt images

.PRECIOUS:
