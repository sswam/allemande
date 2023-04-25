WEBUI := $$ALLEMANDE_HOME/webui
ROOMS := $$ALLEMANDE_ROOMS
WATCH_LOG := $$ALLEMANDE_HOME/watch.log


JOBS := default run-i3 run frontend backend dev run core vi vscode voice webui \
	llm whisper chat-api stream watch bb2html nginx logs perms \
	brain mike speak firefox-webui-home chrome-webui-home


default: run-i3


run-i3:: i3-layout
run-i3:: run


run: frontend backend dev


frontend: vi.xt vscode firefox-webui-home chrome-webui-home

backend: core voice webui

dev: perms cleanup nginx.xt logs.xt


core: llm.xt whisper.xt

voice: brain.xt mike.xt speak.xt

webui: chat-api.xt stream.xt watch.xt bb2html.xt


cleanup:
	spool-cleanup

llm:
	core/llm_llama.py

whisper:
	core/stt_whisper.py

brain:
	cd voice-chat && ./brain.sh

mike:
	cd voice-chat && ./mike.sh

speak:
	cd voice-chat && ./speak.sh

vi:
	vi $$file

vscode:
	code $$file &

chat-api:
	uvicorn chat-api:app --app-dir $(WEBUI) --reload  # --reload-include *.csv

stream:
	cd $(ROOMS) && uvicorn stream:app --app-dir $(WEBUI) --reload  --reload-dir $(WEBUI) --port 8001

watch:
	awatch.py -x bb $(ROOMS) >> $(WATCH_LOG)

bb2html:
	$(WEBUI)/bb2html.py -w $(WATCH_LOG)

nginx:
	inotifywait -q -m -e modify $(WEBUI)/nginx | while read e; do v sudo systemctl restart nginx; done

logs:
	tail -f /var/log/nginx/access.log /var/log/nginx/error.log

perms:
	cd $(WEBUI) && adm/perms

firefox-webui-home:
	firefox "https://chat-home.ucm.dev/#$$room" &

chrome-webui-home:
	chrome "https://chat-home.ucm.dev/#$$room" &


%.xt:
	xt nt-make "$*" &

i3-layout:
	if which i3-msg; then i3-msg "append_layout $$ALLEMANDE_HOME/i3-layout.json"; fi


.PHONY: default $(JOBS) %.xt
