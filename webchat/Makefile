static_files = $(wildcard static/*.html) $(wildcard static/*.css) $(wildcard static/*.js) $(wildcard static/*.json) $(wildcard static/*.png)

all: build.stamp get

build.stamp: $(static_files)
	./update_version.sh
	touch build.stamp

get: static/d3.min.js static/wasm.min.js static/d3-graphviz.min.js

static/d3.min.js:
	wget -O $@ "https://unpkg.com/d3@7.9.0/dist/d3.min.js"

static/wasm.min.js:
	wget -O $@ "https://unpkg.com/browse/@hpcc-js/wasm@2.22.4/dist/index.js"

static/graphviz.js:
	wget -O $@ "https://unpkg.com/browse/@hpcc-js/wasm@2.22.4/dist/graphviz.js"

static/d3-graphviz.min.js:
	wget -O $@ https://unpkg.com/d3-graphviz@3.1.0/build/d3-graphviz.min.js

clean:
	rm -f static/d3.min.js static/wasm.min.js static/d3-graphviz.min.js

