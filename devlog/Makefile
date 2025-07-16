N=30
delay=30

update:
	find -size 0 | xa rm; devlog -r,ref.md,ally_chat.md
many:
	for A in `seq 1 $(N)`; do make; sleep $(delay); echo; echo; done
simple:
	./make-simple.sh
share:
	mkdir -p "$$ALLEMANDE_ROOMS/devlog/tech"
	for A in 20??-??-??.md; do \
		cp "$$A" "tmp.bb"; mv "tmp.bb" "$$ALLEMANDE_ROOMS/devlog/tech/$${A%.md}.bb" ;\
		cp "simple/$$A" "tmp.bb"; mv "tmp.bb" "$$ALLEMANDE_ROOMS/devlog/$${A%.md}.bb" ;\
	done

.PHONY: update many simple
