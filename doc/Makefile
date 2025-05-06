all: nsfw/guide.md

nsfw/guide.md: guide.md nsfw/guide_nsfw.md extra.md
	cat $^ >$@

Here's the adjusted Makefile using >$@ to output to the designated file:

extra.md: ../agents/cartoon ../agents/celeb ../agents/disney ../agents/fiction ../agents/muppet
	@echo "# Extra Characters" >$@
	@echo >>$@
	@echo "Note: All characters are configured to be at least 20 years old," >>$@
	@echo "aside from some of the muppets! Most have detailed visuals including LoRAs." >>$@
	@echo >>$@
	@(cd ../agents ; for cat in cartoon celeb disney fiction muppet; do echo "## $$cat"; echo; ls "$$cat" | sed 's/\.yml$$/, /' | tr -d '\n' | sed 's/, $$//'; echo; echo; done) | fmt >>$@
