SOURCE_FILES = $(shell ls -p | grep -v / | grep '^[a-z]' | grep -v '\.')
DOT_FILES = $(addsuffix .dot,$(SOURCE_FILES))

build: $(DOT_FILES) all.dot
%.dot: %
	AMPS_dot $< >$@

# create all for all the source files, not dot files
all: $(SOURCE_FILES)
	cat $^ >$@
