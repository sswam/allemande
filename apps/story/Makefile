all: pure/story.sh pure/illustrate.py

pure/story.sh: story.sh Makefile
	<$< sed '/^\t*if.*\(pony\|adult\)/,/^\t*fi$$/d; /adult.*{/,/^}$$/d; /\<adult\>/d; /_adult_/d; s/"\$${pony_args\[@\]}" //; /pony/d;' | squeeze-blank-lines >$@

pure/illustrate.py: illustrate.py Makefile
	<$< grep -vw pony >$@
