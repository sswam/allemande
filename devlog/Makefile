N=30
delay=30

default:
	@echo >&2 "devlog does not build with default target"

up:
	find -size 0 | xa rm; devlog -r,ref.md,ally_chat.md
many:
	for A in `seq 1 $(N)`; do make; sleep $(delay); echo; echo; done
simple:
	./make-simple.sh
share:
	./share.sh

.PHONY: default up many simple
