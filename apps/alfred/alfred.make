#!/usr/bin/make -f

# I have an info directory with HTML and PDF files in it. I want to make a
# list of .txt files with the same stem in the info directory.

DOCUMENT_FILE_EXTENSIONS=html htmp pdf doc docx ppt pptx odt
VIDEO_FILE_EXTENSIONS=mp4 mkv mov avi m4v webm
IMAGE_FILE_EXTENSIONS=jpg jpeg png gif webp
AUDIO_FILE_EXTENSIONS=mp3 ogg wav flac
TEXT_FILE_EXTENSIONS=txt md
DATA_FILE_EXTENSIONS=csv tsv json xml yaml xls xlsx
EMAIL_FILE_EXTENSIONS=eml msg mbox pst ost cvf

# find all input files with any of those extensions, under input/
INPUT_FILES=$(shell find input -type f -name '*.$(DOCUMENT_FILE_EXTENSIONS)' -o -name '*.$(VIDEO_FILE_EXTENSIONS)' -o -name '*.$(IMAGE_FILE_EXTENSIONS)' -o -name '*.$(AUDIO_FILE_EXTENSIONS)' -o -name '*.$(TEXT_FILE_EXTENSIONS)' -o -name '*.$(DATA_FILE_EXTENSIONS)' -o -name '*.$(EMAIL_FILE_EXTENSIONS)')

# for each input file, make a txt version by appending .txt
TEXT_FILES=$(addsuffix .txt,$(INPUT_FILES))

WHISPER=whisp

SHELL=/bin/bash

.PHONY: goal

goal: output.md output.pdf output.html output.docx

output.md: $(TEXT_FILES)
	printf "%s\n" "Hello, world: $^" > $@

output.%: output.md
	pandoc $< -o $@
