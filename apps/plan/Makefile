all: chat.html design-chat.html

%.md: %.bb
	bb2markdown_table.py < $< > $@

%.html: %.md
	title=$$(echo $* | sed 's/\.[^.]*$$//'); \
	pandoc --css=markdown-chat.css -s -f markdown+smart --toc --metadata pagetitle="$$title" --to=html5 --include-after-body=script.html $< -o $@
	#--include-in-header=script.html $< -o $@

.SECONDARY:
