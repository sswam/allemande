export

SHELL := /bin/bash

WEBUI := $(ALLEMANDE_HOME)/webui
ROOMS := $(ALLEMANDE_ROOMS)
WATCH_LOG := $(ALLEMANDE_HOME)/watch.log
SCREEN := $(ALLEMANDE_SCREEN)
SCREENRC := $(ALLEMANDE_HOME)/config/screenrc


JOBS := default run-i3 run frontend backend dev run core vi vscode voice webui \
	llm whisper chat-api stream watch bb2html nginx logs perms \
	brain mike speak firefox-webui-local chrome-webui-local


default: run-i3-screen


run-i3-screen:: i3-layout
run-i3-screen:: stop
run-i3-screen:: run


run: frontend backend dev


frontend: vi.xt vscode firefox-webui-local chrome-webui-local

backend: core voice webui

dev: cleanup nginx.xt logs.xt

install-dev:
	allemande-install
	allemande-user-add www-data
	webui-install

install-dev:
	allemande-install
	allemande-user-add $$USER
	webui-install-dev

uninstall:
	allemande-uninstall
	webui-uninstall

core: llm.xt whisper.xt

voice: brain.xt mike.xt speak.xt

webui: chat-api.xt stream.xt watch.xt bb2html.xt


cleanup:
	spool-cleanup
	spool-history-rm
	> watch.log

llm:
	core/llm_llama.py

whisper:
	core/stt_whisper.py

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
	uvicorn chat-api:app --app-dir $(WEBUI) --reload --timeout-graceful-shutdown 5 # --reload-include *.csv

stream:
	cd $(ROOMS) && uvicorn stream:app --app-dir $(WEBUI) --reload  --reload-dir $(WEBUI) --port 8001 --timeout-graceful-shutdown 1

watch:
	awatch.py -x bb $(ROOMS) >> $(WATCH_LOG)

bb2html:
	$(WEBUI)/bb2html.py -w $(WATCH_LOG)

nginx:
	(echo; inotifywait -q -m -e modify $(WEBUI)/nginx ) | while read e; do v sudo systemctl restart nginx; done

logs:
	tail -f /var/log/nginx/access.log /var/log/nginx/error.log

firefox-webui-local:
	(sleep 1; firefox "https://chat-local.ucm.dev/#$$room") & disown

chrome-webui-local:
	(sleep 1; chrome "https://chat-local.ucm.dev/#$$room") & disown


%.xt:
	xterm-screen-run.sh "$(SCREEN)" "$*" nt-make "$*"

i3-layout:
	if which i3-msg; then i3-msg "append_layout $(ALLEMANDE_HOME)/i3-layout.json"; fi

stop:
	screen -S "$(SCREEN)" -X quit || true


.PHONY: default $(JOBS) %.xt
