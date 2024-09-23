MARKDOWN_FILES := $(wildcard *.md)
HTML_FILES := $(MARKDOWN_FILES:.md=.html)

all: $(HTML_FILES)

%.html: %.md
	pandoc -f markdown -t html -s -o $@ $<

.PHONY: clean

clean:
	rm -f *.html
