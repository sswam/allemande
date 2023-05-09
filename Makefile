export

SHELL := /bin/bash

WEBCHAT := $(ALLYCHAT_HOME)
ROOMS := $(ALLEMANDE_ROOMS)
WATCH_LOG := $(ALLEMANDE_HOME)/watch.log
SCREEN := $(ALLEMANDE_SCREEN)
SCREENRC := $(ALLEMANDE_HOME)/config/screenrc
TEMPLATES := $(WEBCHAT)/templates


JOBS := server_start server_stop beorn server default run-i3 run frontend backend dev \
	run core vi vscode voice webchat llm whisper chat-api stream auth watch \
	bb2html nginx logs perms brain mike speak \
	firefox-webchat-local chrome-webchat-online stop mount umount fresh \
	install install-dev uninstall cleanup i3-layout


all: server_start beorn

default: beorn


server_start:
	ssh -t $(SERVER_SSH) "cd $(ALLEMANDE_HOME) && . ./env.sh && make server"

server_stop:
	ssh -t $(SERVER_SSH) "cd $(ALLEMANDE_HOME) && . ./env.sh && make stop"


beorn: mount run-i3-screen
i3: connect-i3-screen


server:: stop
server:: webchat


run-i3-screen:: i3-layout
run-i3-screen:: stop
run-i3-screen:: run

connect-i3-screen:: i3-layout
connect-i3-screen:: connect

run: frontend backend dev
connect: frontend backend.xtc dev.xtc
disconnect:
	psgrep 'xterm -e screen -x [a]llemande -p ' | k 2 | xa kill

frontend: vi.xt vscode firefox-webchat-local chrome-webchat-online

backend: core voice webchat
backend.xtc: core.xtc voice.xtc webchat.xtc

dev: cleanup nginx.xt logs.xt
dev.xtc: cleanup nginx.xtc logs.xtc

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

core.xtc: llm.xtc whisper.xtc

voice.xtc: brain.xtc mike.xtc speak.xtc

webchat.xtc: chat-api.xtc stream.xtc watch.xtc bb2html.xtc



cleanup:
	spool-cleanup
	spool-history-rm
	> watch.log

llm:
	sudo -E -u $(ALLEMANDE_USER) $(PYTHON) core/llm_llama.py -m $(LLM_MODEL)

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

auth:
	uvicorn main:app --app-dir auth --reload --timeout-graceful-shutdown 5 --port 8002 # --reload-include *.csv

watch:
	awatch.py -x bb -p $(ROOMS) >> $(WATCH_LOG)

bb2html:
	$(WEBCHAT)/bb2html.py -w $(WATCH_LOG)

nginx:
	(echo; inotifywait -q -m -e modify $(ALLEMANDE_HOME)/adm/nginx ) | while read e; do v restart-nginx.sh; echo ... done; done

logs:
	tail -f /var/log/nginx/access.log /var/log/nginx/error.log

firefox-webchat-local:
	(sleep 1; firefox -P "$$USER" "https://chat-local.allemande.ai/#$$room") & disown

chrome-webchat-online:
	(sleep 1; chrome "https://chat.allemande.ai/#$$room") & disown


%.xt:
	xterm-screen-run.sh "$(SCREEN)" "$*" nt-make "$*"

%.xtc:
	xterm-screen-connect.sh "$(SCREEN)" "$*"

i3-layout:
	if which i3-msg; then i3-msg "append_layout $(ALLEMANDE_HOME)/i3/layout.json"; fi

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
