all: hello_wasm.wasm hello_wasm.js

%.wasm %.js: %.c
	emcc -sEXPORTED_RUNTIME_METHODS=ccall -sEXPORTED_FUNCTIONS=_malloc,_free $< -o $*.js -s WASM=1

clean:
	rm -f hello_wasm.wasm hello_wasm.js

.SECONDARY:
