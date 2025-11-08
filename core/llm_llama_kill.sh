#!/bin/bash -eu
# Kill the llm_llama process,
# if case of failure, so it will restart and hopefully work!
PID=$(psgrep 'core/llm_llama' | grep -vw bash | awk '{print $2}')
if [ -n "$PID" ]; then
	v kill $PID || true
fi
