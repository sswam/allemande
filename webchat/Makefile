#!/usr/bin/make -Lf

static_files = $(wildcard static/*.html) $(wildcard static/*.css) $(wildcard static/*.js) $(wildcard static/*.wasm) $(wildcard static/*.json) $(wildcard static/*.png)

all: build.stamp get

build.stamp: $(static_files) ../site/auth.js
	echo $(static_files)
	./update_version.sh
	touch build.stamp

get: static/d3.min.js static/wasm.min.js static/graphvizlib.wasm static/d3-graphviz.min.js static/mermaid.min.js # static/katex.min.css static/katex.min.js
# ln -sfT ~/soft-ai/KaTeX/fonts static/fonts

# Using CDN, because fonts are tricky to fetch cross-origin
# static/katex.min.css:
# 	wget -O $@ https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.css
#
# static/katex.min.js:
# 	wget -O $@ https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.js

static/d3.min.js:
	wget -O $@ "https://unpkg.com/d3@5.16.0/dist/d3.min.js"

static/wasm.min.js:
	wget -O- "https://unpkg.com/@hpcc-js/wasm@0.3.11/dist/index.js" | sed 's/{credentials:"same-origin"}/{credentials:"include"}/g' >$@

static/graphvizlib.wasm:
	wget -O $@ "https://unpkg.com/@hpcc-js/wasm@0.3.11/dist/graphvizlib.wasm"

static/d3-graphviz.min.js:
	wget -O $@ https://unpkg.com/d3-graphviz@3.1.0/build/d3-graphviz.min.js

static/mermaid.min.js:
	wget -O $@ https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js

clean:
	rm -f static/d3.min.js static/wasm.min.js static/graphvizlib.wasm static/d3-graphviz.min.js static/mermaid.min.js

