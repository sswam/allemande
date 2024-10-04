all: pure/story.sh pure/illustrate.py

pure/story.sh: story.sh
	<$< sed '/adult.*{/,/^}$$/d; /\<adult\>/d; /_adult_/d; /if.*pony/,/fi/d; s/"\$${pony_args\[@\]}" //; /pony/d;' | squeeze-blank-lines >$@

pure/illustrate.py: illustrate.py
	<$< grep -vw pony >$@
