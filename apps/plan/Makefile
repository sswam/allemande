all: hello.wasm # chat.html design-chat.html

%.wasm: %.c
	emcc $< -o $@

%.md: %.bb
	bb2markdown_table.py < $< > $@

%.html: %.md
	title=$$(echo $* | sed 's/\.[^.]*$$//'); \
	pandoc --css=markdown-chat.css -s -f markdown+smart --toc --metadata pagetitle="$$title" --to=html5 --include-after-body=script.html $< -o $@

.SECONDARY:
