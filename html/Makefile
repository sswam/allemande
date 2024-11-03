
exes = htmlsplit
tests = tests/htmlsplit_test

CC=gcc
CFLAGS=-Wall -Wextra -pedantic -std=c99 -ggdb

all: $(exes) $(tests)

%.h: %.c
	cproto $< >$@

tests/htmlsplit_test: tests/htmlsplit_test.o
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS) -lcheck -lsubunit -lm

clean:
	rm -f $(exes) $(tests) *.o

test: $(tests)
	./tests/htmlsplit_test
	@echo >&2 "All tests passed."

.PHONY: all clean test
