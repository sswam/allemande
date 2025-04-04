DOT_FILES = $(wildcard *.dot)
SOURCE_FILES = $(DOT_FILES:.dot=)

build: $(DOT_FILES) all.dot
%.dot: %
	AMPS_dot $< >$@

# create all for all the source files, not dot files
all: $(SOURCE_FILES)
	cat $^ >$@
