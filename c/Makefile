exes = test_python test_perl test_lua test_ruby test_quickjs test_v8 test_mozjs

all: $(exes)

%: %.c
	$(MAKE) -f $(patsubst test_%,Makefile_%,$@)
%: %.cc
	$(MAKE) -f $(patsubst test_%,Makefile_%,$@)

clean:
	rm -f $(exes) *.o
