export

SHELL := /bin/bash

WEBCHAT := $(ALLEMANDE_HOME)/webchat
ROOMS := $(ALLEMANDE_ROOMS)
WATCH_LOG := $(ALLEMANDE_HOME)/watch.log
SCREEN := $(ALLEMANDE_SCREEN)
SCREENRC := $(ALLEMANDE_HOME)/config/screenrc


JOBS := server_start server_stop home server default run-i3 run frontend backend dev \
	run core vi vscode voice webchat llm whisper chat-api stream watch \
	bb2html nginx logs perms brain mike speak \
	firefox-webchat-local chrome-webchat-local stop mount umount fresh \
	install install-dev uninstall cleanup i3-layout


default: server_start home


server_start:
	ssh -t $(SERVER_SSH) "cd $(ALLEMANDE_HOME) && . ./env.sh && make server"

server_stop:
	ssh -t $(SERVER_SSH) "cd $(ALLEMANDE_HOME) && . ./env.sh && make stop"


home: mount run-i3-screen


server:: stop
server:: webchat


run-i3-screen:: i3-layout
run-i3-screen:: stop
run-i3-screen:: run


run: frontend backend dev


frontend: vi.xt vscode firefox-webchat-local chrome-webchat-local

backend: core voice webchat

dev: cleanup nginx.xt logs.xt

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

core: llm.xt whisper.xt

voice: brain.xt mike.xt speak.xt

webchat: chat-api.xt stream.xt watch.xt bb2html.xt


cleanup:
	spool-cleanup
	spool-history-rm
	> watch.log

llm:
	sudo -E -u $(ALLEMANDE_USER) $(PYTHON) core/llm_llama.py

whisper:
	sudo -E -u $(ALLEMANDE_USER) $(PYTHON) core/stt_whisper.py

brain:
	cd chat && ./brain.sh

mike:
	cd voice-chat && ./mike.sh

speak:
	cd voice-chat && ./speak.sh

vi:
	vi $$file

vscode:
	code $$file & disown

chat-api:
	uvicorn chat-api:app --app-dir $(WEBCHAT) --reload --timeout-graceful-shutdown 5 # --reload-include *.csv

stream:
	cd $(ROOMS) && uvicorn stream:app --app-dir $(WEBCHAT) --reload  --reload-dir $(WEBCHAT) --port 8001 --timeout-graceful-shutdown 1

watch:
	awatch.py -x bb -p $(ROOMS) >> $(WATCH_LOG)

bb2html:
	$(WEBCHAT)/bb2html.py -w $(WATCH_LOG)

nginx:
	(echo; inotifywait -q -m -e modify $(ALLEMANDE_HOME)/adm/nginx ) | while read e; do v sudo systemctl restart nginx; done

logs:
	tail -f /var/log/nginx/access.log /var/log/nginx/error.log

firefox-webchat-local:
	(sleep 1; firefox "https://chat-local.allemande.ai/#$$room") & disown

chrome-webchat-local:
	(sleep 1; chrome "https://chat-local.allemande.ai/#$$room") & disown


%.xt:
	xterm-screen-run.sh "$(SCREEN)" "$*" nt-make "$*"

i3-layout:
	if which i3-msg; then i3-msg "append_layout $(ALLEMANDE_HOME)/i3-layout.json"; fi

stop:
	screen -S "$(SCREEN)" -X quit || true

mount:
	mkdir -p $(ALLEMANDE_ROOMS_SERVER)
	sshfs $(SERVER_ROOMS_SSH) $(ALLEMANDE_ROOMS_SERVER) -o cache=no || true

umount:
	fusermount -u $(ALLEMANDE_ROOMS_SERVER) || true

fresh:
	time=$$(date +%Y%m%d-%H%M%S) ; html=$${file%.bb}.html ; \
	if [ -s $(file) ]; then mv -v $(file) $(file).$$time; fi ; \
	if [ -s $$html ]; then mv $$html $$html.$$time; fi ; \
	touch $(file) $$html


.PHONY: default $(JOBS) %.xt
