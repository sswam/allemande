IMAGE_SFW=landscape-rainbow-vibrant-colorful-scenic-daylight-sunny-clear-sky-rol.jpg
IMAGE_NSFW=solo-person-Cleo-black-lace-lingerie-seductive-lingerie-details-1-2-se.jpg

all: nsfw/guide.md ../rooms/intro.bb ../rooms/guide.bb ../rooms/${IMAGE_SFW} ../rooms/nsfw/intro.bb ../rooms/nsfw/guide.bb ../rooms/nsfw/${IMAGE_NSFW} summaries.md ../rooms/agents/Yenta.yml

nsfw/guide.md: guide.md nsfw/guide_nsfw.md extra.md
	cat $^ >$@

extra.md: ../agents/cartoon ../agents/celeb ../agents/disney ../agents/fiction ../agents/muppet
	@echo "# Extra Characters" >$@
	@echo >>$@
	@echo "Note: All characters are configured to be at least 20 years old," >>$@
	@echo "aside from some of the muppets! Most have detailed visuals including LoRAs." >>$@
	@echo >>$@
	@(cd ../agents ; for cat in cartoon celeb disney fiction muppet; do echo "## $$cat"; echo; ls "$$cat" | sed 's/\.yml$$/, /' | tr -d '\n' | sed 's/, $$//'; echo; echo; done) | fmt >>$@

summaries.md: $(shell find ../agents/ -name '*.yml' | sed 's/ /\\ /g')
	webchat-agent-summaries-update
	./summaries_compile.sh > summaries.md

../rooms/agents/Yenta.yml: Yenta.0.yml summaries.md
	(cat Yenta.0.yml; sed 's/^/  /' < summaries.md) > $@

../rooms/intro.bb: intro.md
	rm -f $@ ../rooms/intro.html
	cp -a $< $@
	chmod a-w $@

../rooms/guide.bb: guide.md
	rm -f $@ ../rooms/guide.html
	cp -a $< $@
	chmod a-w $@

../rooms/${IMAGE_SFW}: ${IMAGE_SFW}
	rm -f $@
	cp -a $< $@
	chmod a-w $@

../rooms/nsfw/intro.bb: nsfw/intro.md
	rm -f $@ ../rooms/nsfw/intro.html
	cp -a $< $@
	chmod a-w $@

../rooms/nsfw/guide.bb: nsfw/guide_nsfw.md
	rm -f $@ ../rooms/nsfw/guide.html
	cp -a $< $@
	chmod a-w $@

../rooms/nsfw/${IMAGE_NSFW}: nsfw/${IMAGE_NSFW}
	rm -f $@
	cp -a $< $@
	chmod a-w $@
