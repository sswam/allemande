WEBUI := $$ALLEMANDE_HOME/webui
ROOMS := $$ALLEMANDE_ROOMS
WATCH_LOG := $$ALLEMANDE_HOME/watch.log


JOBS := run-dev run core vi vscode voice webui webui-dev llm whisper \
	chat-api stream watch bb2html nginx logs perms brain mike speak \
	firefox-webui-home chrome-webui-home


default: run-dev.xt


run-dev.xt: core.xt vi.xt vscode voice.xt webui-dev.xt firefox-webui-home chrome-webui-home

run.xt: core.xt vi.xt vscode voice.xt webui.xt

core.xt: llm.xt whisper.xt

voice.xt: brain.xt mike.xt speak.xt

webui.xt: chat-api.xt stream.xt watch.xt bb2html.xt

webui-dev.xt: perms webui.xt nginx.xt logs.xt 

firefox-webui-home:
	firefox "https://chat-home.ucm.dev/#chat" &

chrome-webui-home:
	chrome "https://chat-home.ucm.dev/#chat" &

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


%.xt:
	xterm -e "nt $* ; $(MAKE) $*" &


.PHONY: default $(JOBS) %.xt
