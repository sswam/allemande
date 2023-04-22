#!/bin/bash
cd "$ALLEMANDE_HOME"
# kill subprocesses on exit
trap "kill 0" EXIT
core/llm_llama.py &
core/stt_whisper.py &
wait
