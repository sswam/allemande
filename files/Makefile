exes = touch_ctime
tests = tests/touch_ctime_test

CC=gcc
CFLAGS=-Wall -Wextra -pedantic -std=c99 -ggdb

all: $(exes) $(tests)

%.h: %.c
	cproto $< >$@

tests/touch_ctime_test.o: tests/touch_ctime_test.c touch_ctime.c
	$(CC) -c $(CFLAGS) -o $@ tests/touch_ctime_test.c
tests/touch_ctime_test: tests/touch_ctime_test.o
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS) -lcheck -lsubunit -lm

clean:
	rm -f $(exes) $(tests) *.o

test: $(tests)
	./tests/touch_ctime_test
	@echo >&2 "All tests passed."

.PHONY: all clean test
