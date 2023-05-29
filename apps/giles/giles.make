#!/usr/bin/make -f

# giles: search on a topic, fetch webpages, and run alfred to perform a mission

SHELL=/bin/bash
IMAGE2TEXT_MODE=best  # not used
LLM_MODEL_LONG=c+
LLM_MODEL=4
OCR_MODEL=4
# Note: OCR_MODEL is not used by giles
LLM_MODEL_WORDS_MAX=1800

export

n_results=10
query=

default: output.zip
models: 4 3+ c i
summary_prompt=Please summarize this info in detail, using markdown dot-point form. Be as comprehensive and factual as possible. Please include as much factual information as possible. Cover a comprehensive scope of things to see, do, history, how to get there, what's around, and things to be careful of. Do not mention other areas. Be factual.

results.txt:
	if [ -z "$(query)" ]; then echo "ERROR: query is empty"; exit 1; fi
	search -m "$(n_results)" "$(query)" > $@

input: results.txt
	mkdir -p input
	(cd input && giles_get) < $<

mission.txt: mission.in.txt
	if [ -z "$(query)" ]; then echo "ERROR: query is empty"; exit 1; fi
	perl -pe 's/\$$query\b/$$ENV{query}/g' < $< > $@

output.zip: input mission.txt
	alfred IMAGE2TEXT_MODE="$(IMAGE2TEXT_MODE)" LLM_MODEL="$(LLM_MODEL)" LLM_MODEL_LONG="$(LLM_MODEL_LONG)" LLM_MODEL_WORDS_MAX="$(LLM_MODEL_WORDS_MAX)" OCR_MODEL="$(OCR_MODEL)"


.PHONY: default
