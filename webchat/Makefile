#!/usr/bin/make -Lf

SHELL=bash
.ONESHELL:

# BOOTSTRAP_ICONS_CSS=https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css
# BOOTSTRAP_ICONS_WOFF2=https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff2

static_files = $(wildcard static/*.html) $(wildcard static/*.css) $(wildcard static/*.js) $(wildcard static/*.wasm) $(wildcard static/*.json) $(wildcard static/*.png)

all: build.stamp get users.txt # static/icons.css

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
	ed $@ <<EOT
	$
	s/sourceMappingURL=.*/sourceMappingURL=
	wq
	EOT

static/graphvizlib.wasm:
	wget -O $@ "https://unpkg.com/@hpcc-js/wasm@0.3.11/dist/graphvizlib.wasm"

static/d3-graphviz.min.js:
	wget -O $@ https://unpkg.com/d3-graphviz@3.1.0/build/d3-graphviz.min.js

static/mermaid.min.js:
	wget -O $@ https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js

# icons.txt: static/icons.js
# 	<$< sed 's,//.*,,' | grep -o '\bbi-[-a-z0-9]*' | sed 's/^bi-//' | LC_ALL=C sort -u >$@
# 
# bootstrap-icons.css:
# 	wget -O $@ "$(BOOTSTRAP_ICONS_CSS)"
# 
# bootstrap-icons.woff2: bootstrap-icons.css
# 	wget -O $@ "$(BOOTSTRAP_ICONS_WOFF2)"
# 
# all-icons-unicode.txt: bootstrap-icons.css
# 	<$< grep '^\.bi-' | sed 's/^\.bi-//; s/::[^"]*"\\/\t/; s/".*//;' | LC_ALL=C sort >$@
# 
# icons-unicode.txt: icons.txt all-icons-unicode.txt
# 	LC_ALL=C join -j 1 -t $$'\t' icons.txt all-icons-unicode.txt >$@
# 
# static/icons.woff2: icons-unicode.txt bootstrap-icons.woff2
# 	pyftsubset --output-file=$@ --unicodes-file=<(cut -f 2 <icons-unicode.txt | sed 's/^/U+/') bootstrap-icons.woff2
# 
# static/icons.css: bootstrap-icons.css static/icons.woff2 icons-unicode.txt
# 	checksum=$$(sha1sum static/icons.woff2 | cut -f1 -d' ')
# 	<$< sed -n '/^\.bi-/q; p' >$@
# 	ed $@ <<EOT
# 	/Licensed
# 	a
# 	* Subset for Ally Chat, by Allemande AI
# 	.
# 	s/^/ /
# 	/"woff2"
# 	s/"[^"]*"/"icons.woff2?$$checksum"/
# 	s/,/;/
# 	+
# 	d
# 	wq
# 	EOT
# 	awk '{print ".bi-" $$1 "::before { content: \"\\" $$2 "\"; }"}' < icons-unicode.txt >>$@

users.txt: .htpasswd
	<"$<" cut -d: -f1 >"$@"

clean:
	rm -f static/d3.min.js static/wasm.min.js static/graphvizlib.wasm static/d3-graphviz.min.js static/mermaid.min.js
	# rm -f icons.txt bootstrap-icons.css bootstrap-icons.woff2 all-icons-unicode.txt icons-unicode.txt static/icons.woff2 static/icons.css
