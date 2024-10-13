all: hello.wasm hello.js

%.wasm %.js: %.c
	emcc -sEXPORTED_RUNTIME_METHODS=ccall -sEXPORTED_FUNCTIONS=_malloc,_free $< -o $*.js -s WASM=1

clean:
	rm -f hello.wasm hello.js

%.md: %.bb
	bb2markdown_table.py < $< > $@

%.html: %.md
	title=$$(echo $* | sed 's/\.[^.]*$$//'); \
	pandoc --css=markdown-chat.css -s -f markdown+smart --toc --metadata pagetitle="$$title" --to=html5 --include-after-body=script.html $< -o $@

.SECONDARY:
