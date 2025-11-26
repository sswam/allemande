IMAGE_SFW=landscape-rainbow-vibrant-colorful-scenic-daylight-sunny-clear-sky-rol.jpg
IMAGE_NSFW=solo-person-Cleo-black-lace-lingerie-seductive-lingerie-details-1-2-se.jpg

AGENTS_PATHS_SFW := $(shell find ../agents/ -mindepth 1 -maxdepth 1 -type d \! -name 'nsfw')
AGENTS_PATHS_NSFW := $(shell find ../agents/ -mindepth 1 -maxdepth 1 -type d \! -name 'toon')

AGENTS_DIRS_SFW := $(shell find ../agents/ -mindepth 1 -maxdepth 1 -type d \! -name 'nsfw' -printf "%f\n")
AGENTS_DIRS_NSFW := $(shell find ../agents/ -mindepth 1 -maxdepth 1 -type d \! -name 'toon' -printf "%f\n")

HELP_MODEL := emmy
HELP_MODEL_NSFW := flashi

default:
	@echo >&2 "doc does not build with default target"

up: nsfw/guide.md ../rooms/intro.bb ../rooms/guide.bb ../rooms/${IMAGE_SFW} ../rooms/nsfw/intro.bb ../rooms/nsfw/guide.bb ../rooms/nsfw/${IMAGE_NSFW} ../rooms/agents/CastMembers.yml ../rooms/lora.bb ../rooms/nsfw/lora.bb ../rooms/terms.bb help.md nsfw/help_nsfw.md nsfw/help.md help.md summaries.md  # agent_colours.css

nsfw/guide.md: guide.md nsfw/guide_nsfw.md  # nsfw/extra.md
	rm -f $@
	cat $^ >$@
	chmod a-w $@

# guide+extra.md: guide.md extra.md
# 	rm -f $@
# 	cat $^ >$@
# 	chmod a-w $@

help.md: guide.md prompt_help.txt
	git diff --quiet "$@"  # fail if uncommitted changes to target
	chmod +w $@
	lecho transpatch -d -g -m=$(HELP_MODEL) -p="$$(<prompt_help.txt)" "$@" guide.md
	chmod a-w $@

nsfw/help_nsfw.md: nsfw/guide_nsfw.md prompt_help.txt
	git diff --quiet "$@"  # fail if uncommitted changes to target
	chmod +w $@
	lecho transpatch -d -g -m=$(HELP_MODEL_NSFW) -p="$$(<prompt_help.txt)" "$@" nsfw/guide_nsfw.md
	chmod a-w $@

nsfw/help.md: help.md nsfw/help_nsfw.md
	rm -f $@
	cat help.md >$@
	echo >>$@
	cat nsfw/help_nsfw.md >>$@
	chmod a-w $@

extra.md: $(AGENTS_PATHS_SFW)
	@echo "# Extra Characters" >$@
	@echo >>$@
	@(cd ../agents ; for cat in $(AGENTS_DIRS_SFW); do echo "## $$cat"; echo; find "$$cat" -name '*.yml' -printf "%f\n" | sed 's/\.yml$$/, /' | sort | tr -d '\n' | sed 's/, $$//'; echo; echo; done) | fmt >>$@

nsfw/extra.md: $(AGENTS_PATHS_NSFW)
	@echo "# Extra Characters" >$@
	@echo >>$@
	@echo "Note: All of these characters are configured to be at least 18 years old," >>$@
	@echo "aside from some of the muppets! Many have detailed visuals, and some have LoRAs." >>$@
	@echo "Do not create NCII / noncon deepfakes of real people." >>$@
	@echo >>$@
	@(cd ../agents ; for cat in $(AGENTS_DIRS_NSFW); do echo "## $$cat"; echo; find "$$cat" -name '*.yml' -printf "%f\n" | sed 's/\.yml$$/, /' | sort | tr -d '\n' | sed 's/, $$//'; echo; echo; done) | fmt >>$@

summaries.md: ../agents/dirs.txt $(shell find ../agents/ -path '*/.*' -prune -o -print | sed 's/ /\\ /g') $(shell find summary/ -mindepth 1 | sed 's/ /\\ /g')
	webchat-agent-summaries-update -n
	./summaries_compile.sh > summaries.md
	rm -f ../rooms/characters.html ../rooms/characters.bb
	(sleep 0.5; cp summaries.md ../rooms/characters.bb ; sudo cp -a $@ /home/nobodally/characters.bb)

../rooms/agents/CastMembers.yml: Mixin.0.yml summaries.md
	chmod +w $@ || true
	(cat Mixin.0.yml; sed 's/^/  /' < summaries.md) > $@
	chmod a-w $@

../rooms/intro.bb: intro.md
	rm -f $@ ../rooms/intro.html
	(sleep 0.5; cp -a $< $@; chmod a-w $@) &

../rooms/guide.bb: guide.md  # guide+extra.md
	rm -f $@ ../rooms/guide.html
	(sleep 0.5; cp -a $< $@; chmod a-w $@) &

../rooms/${IMAGE_SFW}: ${IMAGE_SFW}
	rm -f $@
	cp -a $< $@
	chmod a-w $@

../rooms/nsfw/intro.bb: nsfw/intro.md
	rm -f $@ ../rooms/nsfw/intro.html
	(sleep 0.5; cp -a $< $@; chmod a-w $@) &

../rooms/nsfw/guide.bb: nsfw/guide_nsfw.md
	rm -f $@ ../rooms/nsfw/guide.html
	(sleep 0.5; cp -a $< $@; chmod a-w $@) &

../rooms/nsfw/${IMAGE_NSFW}: nsfw/${IMAGE_NSFW}
	rm -f $@
	cp -a $< $@
	chmod a-w $@

../rooms/terms.bb: terms.md
	rm -f $@ ../rooms/terms.html
	(sleep 0.5; cp -a $< $@; chmod a-w $@; sleep 5; cp -af ../rooms/terms.html ../site/terms.html) &

../rooms/lora.bb: ../agents/special/Pixi.yml ../agents/special/Illu.yml
	rm -f $@ ../rooms/lora.html
	(sleep 0.5; lecho '| <lora:name:weight> | required trigger words | info |' '|--|--|--|' ;\
		cat $^ | grep '^    | <lora:' | grep -v '<lora:name:weight>' | sed 's/ *//') >$@ ;\
		chmod a-w $@ ;\
		sudo cp -a $@ /home/nobodally/lora.bb

../rooms/nsfw/lora.bb: ../agents/nsfw/Xilu.yml
	rm -f $@ ../rooms/nsfw/lora.html
	(sleep 0.5; lecho '| <lora:name:weight> | required trigger words | info |' '|--|--|--|' ;\
		cat $^ | grep '^    | <lora:' | grep -v '<lora:name:weight>' | sed 's/ *//') >$@ ;\
		chmod a-w $@ ;\
		sudo cp -a $@ /home/nobodally/lora-nsfw.bb

agent_colours.tsv: summaries.md
	./update_colours.sh
	cp agent_colours.tsv ~/my/allemande/agent_colours.tsv  # XXX

agent_colours.css: agent_colours.tsv
	<$< ./agent_colours_tsv_to_css.py >$@

.PHONY: default up
