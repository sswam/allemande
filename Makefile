export

SHELL := /bin/bash

WEBCHAT := $(ALLYCHAT_HOME)
ROOMS := $(ALLEMANDE_ROOMS)
AGENTS := $(ALLEMANDE_AGENTS)
WATCH_LOG := $(ALLEMANDE_HOME)/watch.log
SCREEN := $(ALLEMANDE_SCREEN)
SCREENRC := $(ALLEMANDE_HOME)/config/screenrc
TEMPLATES := $(WEBCHAT)/templates
SUBDIRS := $(dir $(wildcard */Makefile))

JOBS := server_start server_stop beorn server default run-i3 run frontend backend dev \
	run core vi-online vi-local vscode-online vscode-local voice webchat llm whisper chat-api stream auth watch \
	bb2html build-ui nginx logs perms brain mike speak \
	firefox-webchat-online firefox-webchat-local firefox-pro-local firefox-pro-online \
	chrome-webchat-online chrome-webchat-local \
	stop mount umount fresh \
	install install-dev uninstall clean i3-layout

all: api_doc subdirs canon

deps:: deb-deps
deps:: venv

deb-deps: deps-allemande_0.1_all.deb

deps-allemande_0.1_all.deb: debian-packages.txt
	env -i PATH=$$PATH HOME=$$HOME metadeb -n=deps-allemande debian-packages.txt

venv: requirements.txt
	[ -e venv ] || python -m venv venv
	. venv/bin/activate; pip install -r requirements.txt
	touch venv

subdirs: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@

server_start:
	ssh -t $(SERVER_SSH) "cd $(ALLEMANDE_HOME) && . ./env.sh && make server"

server_stop:
	ssh -t $(SERVER_SSH) "cd $(ALLEMANDE_HOME) && . ./env.sh && make stop"

beorn: clean run-i3-screen mount
i3: connect-i3-screen

server:: stop
server:: clean
server:: webchat brain.xt

run-i3-screen:: i3-layout
run-i3-screen:: stop
run-i3-screen:: run

connect-i3-screen:: i3-layout
connect-i3-screen:: connect

run: frontend backend dev flash.xt alfred.xt opal-loop.xt
# vi-online.xt
# pro-dev 
connect: frontend backend.xtc dev.xtc pro-dev.xtc flash.xtc alfred.xtc vi-online.xtc
disconnect:
	psgrep 'xterm -e screen -x [a]llemande -p ' | k 2 | xa kill

frontend: firefox-webchat-online vi-online.xt
# firefox-pro-online chrome-webchat-online
frontend-local: vscode-local firefox-webchat-local firefox-pro-local chrome-webchat-local

backend: core webchat
# voice
backend.xtc: core.xtc webchat.xtc
# voice.xtc 

dev: clean nginx.xt logs.xt
dev.xtc: clean nginx.xtc logs.xtc

install:
	allemande-install
	allemande-user-add www-data
	web-install

install-dev:
	allemande-install
	allemande-user-add $$USER
	web-install

uninstall:
	allemande-uninstall
	web-uninstall

core: connects.xt llm.xt images.xt a1111.xt whisper.xt vup.xt

voice: mike.xt speak.xt whisper.xt

webchat: chat-api.xt stream.xt watch.xt bb2html.xt auth.xt build-ui.xt wat.xt

pro: svelte.xt
pro-dev: svelte-dev.xt

svelte:
	cd $(ALLEMANDE_HOME)/pro && npm run build
	cd $(ALLEMANDE_HOME)/pro && node build

svelte-dev:
	cd $(ALLEMANDE_HOME)/pro && npm run dev

flash:
	cd $(ALLEMANDE_HOME)/apps/flash && \
	./flash-webui.py

alfred:
	cd $(ALLEMANDE_HOME)/apps/alfred && \
	./alfred-webui.py

core.xtc: connects.xtc llm.xtc images.xtc a1111.xtc whisper.xtc vup.xtc

voice.xtc: mike.xtc speak.xtc  # brain.xtc

webchat.xtc: chat-api.xtc stream.xtc watch.xtc bb2html.xtc auth.xtc build-ui.xtc

pro.xtc: svelte.xtc
pro-dev.xtc: svelte-dev.xtc

clean:
	spool-cleanup || true
	spool-history-rm || true
	> $(WATCH_LOG)

llm:
	while true; do make mount && $(PYTHON) core/llm_llama.py -g -n 60 -v; sleep 1; done

whisper:
	while true; do make mount && $(PYTHON) core/stt_whisper.py -v; sleep 1; done

images:
	while true; do make mount && $(PYTHON) core/image_a1111.py -v; sleep 1; done

a1111:
	cd ~/webui ; while true; do ./webui.sh --skip-install; done

vup:
	cd $(ALLEMANDE_VISUAL) && \
	while true; do sleep 5; make up; move-contrib; sleep 25; done

connects:
	connects

# brain-remote: clean
# 	cd chat && ./brain.sh --remote

brain: clean
	cd chat && ./brain.sh

# brain-local: clean
# 	cd chat && ./brain.sh --local

mike:
	cd voice-chat && ./bb_mike.sh

speak:
	cd voice-chat && ./bb_speak.sh

vi-online:
	ssh -t $(SERVER_SSH) 'cd $(ALLEMANDE_HOME) && vi -p "$$file"'

vi-local:
	vi -p "$$file"

vscode-online:
	code "$$file_server" & disown

vscode-local:
	code "$$file" & disown

chat-api:
	cd $(WEBCHAT) && awatch -a -i -p ../Makefile chat_api.py ../chat/chat.py ../chat/ally_room.py ../chat/ally_service.py -s -- uvicorn chat_api:app --reload --timeout-graceful-shutdown 5

stream:
	cd $(WEBCHAT) && awatch -a -i -p ../Makefile stream.py ../chat/chat.py ../chat/ally_room.py ../text/atail.py ../ally/cache.py ../chat/ally_service.py -s -- uvicorn stream:app --reload --port 8001 --timeout-graceful-shutdown 1

auth:
	cd auth && uvicorn auth:app --reload --timeout-graceful-shutdown 5 --port 8002

watch:
	awatch -I -r -A -x bb yml safetensors -p $(ROOMS) $(AGENTS) -E >> $(WATCH_LOG)  # -L was there, to follow symlinks; why?

bb2html:
	awatch -a -i -p Makefile $(WEBCHAT)/bb2html.py chat/chat.py chat/ally_markdown.py chat/ally_room.py chat/bb_lib.py text/atail.py -s -- $(WEBCHAT)/bb2html.py -w $(WATCH_LOG)

build-ui:
	# Note, changes to service_worker_in.js will require a manual rebuild
	# because we don't want to bump the version when the version changes, e.g. git stuff
	cd $(WEBCHAT) && awatch -p ../Makefile static ../js/util.js ../js/debug.js ../site/auth.js -e static/service_worker_in.js static/service_worker_gen.js static/room_gen.css -a -J ./Makefile

nginx:
	(echo; inotifywait -q -m -e modify $(ALLEMANDE_HOME)/adm/nginx ) | while read e; do v restart-nginx; echo ... done; done

logs:
	tail -f /var/log/nginx/access.log /var/log/nginx/error.log

firefox-webchat-local:
	(sleep 1; firefox -P "$$USER" "https://chat-local.$$ALLEMANDE_DOMAIN/#$$room") & disown

firefox-webchat-online:
	(sleep 1; firefox -P "$$USER" "https://chat.$$ALLEMANDE_DOMAIN/#$$room") & disown

firefox-pro-local:
	(sleep 1; firefox -P "$$USER" "https://pro-local.$$ALLEMANDE_DOMAIN/") & disown

firefox-pro-online:
	(sleep 1; firefox -P "$$USER" "https://pro.$$ALLEMANDE_DOMAIN/") & disown

chrome-webchat-local:
	(sleep 1; chrome "https://chat-local.$$ALLEMANDE_DOMAIN/#$$room") & disown

chrome-webchat-online:
	(sleep 1; chrome "https://chat.$$ALLEMANDE_DOMAIN/#$$room") & disown

%.xt:
	xterm-screen-run "$(SCREEN)" "$*" nt-make "$*"; sleep 0.1

%.xtc:
	xterm-screen-connect "$(SCREEN)" "$*"

i3-layout:
	if [ -n "$$DISPLAY" ] && which i3-msg; then i3-msg "append_layout $(ALLEMANDE_HOME)/i3/layout.json"; fi

stop:
	screen -S "$(SCREEN)" -X quit || true

mount:
	ally-mount

umount:
	ally-mount -u

wat:
	wat -s=10 -c sh -c 'cd "$(ROOMS)"; find . -mindepth 1 -name ".?*" -prune -o -printf "%P\n" | sortmtime | grep \\.bb | head -n 15 | secs2ago --human | sed "s/\t/ /"'

opal-loop:
	opal-loop

fresh::	stop
fresh::	rotate
fresh::	server

rotate:
	room-archive "$$file"

canon:
	ln -sf ../tools/python3_allemande.sh canon/python3-allemande
	$(ALLEMANDE_HOME)/files/canon_links.py $(ALLEMANDE_PATH)
	(cd canon ; rm -f guidance-*.md ; ln -sf ../*/guidance-*.md .)
	sudo ln -sf $(ALLEMANDE_HOME)/canon/usr-local-bin /usr/local/bin
	cd canon ; usr-local-bin python3-allemande confirm uniqo lecho i3-xterm-floating note waywo ally opts opts-long opts-help path-uniq day find-quick need-bash get-root llm query process que proc text-strip cat-named aligno include status-update i3status-wrapper name-terminal name-terminal-nicely mount-point move-rubbish mic speaker mdcd
	cd alias ; usr-local-bin v i

fresh-old:: 
	time=$$(date +%Y%m%d-%H%M%S) ; html=$${file%.bb}.html ; \
	if [ -s "$(file)" ]; then mv -v "$(file)" "$(file).$$time"; fi ; \
	if [ -s "$$html" ]; then mv "$$html" "$$html.$$time"; fi ; \
	touch "$(file)" "$$html"

api_doc: llm/llm.api

%.api: %.py
	func-py -a -I "$<" > "$@"

.PHONY: all default $(JOBS) %.xt canon api_doc subdirs $(SUBDIRS) deps deb-deps venv
