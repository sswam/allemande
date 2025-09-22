exes = ccx test_python test_perl test_lua test_ruby test_quickjs test_v8 test_mozjs
tests = tests/sea_test tests/hello_c_test

CC=gcc
CXX=g++
CFLAGS=-Wall -Wextra -pedantic -std=c99 -ggdb
CXXFLAGS=-Wall -Wextra -pedantic -std=c++11 -ggdb

all: $(exes) $(tests)

%.h: %.c
	cproto $< >$@

%: %.c Makefile_%
	$(MAKE) -f Makefile_$@
%: %.cc Makefile_%
	$(MAKE) -f Makefile_$@

.%.c.test: %.c
	<$< sed 1d >$@

# %: %.c
# 	$(CC) $(CFLAGS) -o $@ $<
# %: %.cc
# 	$(CXX) $(CXXFLAGS) -o $@ $<

ccx.o: ccx.c

# hello_c.o: hello_c.c sea.h
tests/sea_test.o: tests/sea_test.c sea.h

# hello_c: hello_c.o sea.o

tests/sea_test: tests/sea_test.o sea.o
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS) -lcheck -lsubunit -lm

tests/hello_c_test.o: tests/hello_c_test.c hello_c.c sea.h .hello_c.c.test
	$(CC) -c $(CFLAGS) -o $@ tests/hello_c_test.c
tests/hello_c_test: tests/hello_c_test.o sea.o
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS) -lcheck -lsubunit -lm

clean:
	rm -f $(exes) $(tests) *.o

test: $(tests)
	./tests/sea_test
	./tests/hello_c_test
	@echo >&2 "All tests passed."

.PHONY: all clean test
