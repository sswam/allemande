#!/usr/bin/make -f

# giles: search on a topic, fetch webpages, and run alfred to perform a mission

SHELL=/bin/bash
IMAGE2TEXT_MODE=best
# Note: IMAGE2TEXT_MODE is not not used by giles yet
LLM_MODEL_LONG=c+
LLM_MODEL=4
LLM_MODEL_SUMMARY=4
LLM_MODEL_SUMMARY_MEGA=4
LLM_MODEL_BRAINY=4
OCR_MODEL=4
# Note: OCR_MODEL is not used by giles yet
LLM_MODEL_WORDS_MAX=1800

HTML=0
PDF=0
DOCX=0

MISSIONS_IN=$(wildcard mission.*.in.txt)
MISSIONS=$(patsubst %.in.txt,%.txt,$(MISSIONS_IN))

HTML_DUMP_FILTER=

export

n_results=10
query=

default: output.zip
models: 4 3+ c i
summary_prompt="Please summarize this info in detail, as relating to $$query, using markdown dot-point form. Be as comprehensive and factual as possible. Please include as much factual information as possible. Stay focused on the topic. Be factual."

results.txt:
	if [ -z "$(query)" ]; then echo "ERROR: query is empty"; exit 1; fi
	search -l -m "$(n_results)" "$(query)" > $@

input.ls: results.txt
	mkdir -p input
	(cd input && giles_get) < $<
	ls input > $@

mission.%.txt: mission.%.in.txt
	if [ -z "$(query)" ]; then echo "ERROR: query is empty"; exit 1; fi
	perl -pe 's/\$$query\b/$$ENV{query}/g' < $< > $@

output.zip: input.ls $(MISSIONS)
	alfred HTML=$(HTML) PDF=$(PDF) DOCX=$(DOCX) IMAGE2TEXT_MODE="$(IMAGE2TEXT_MODE)" LLM_MODEL_SUMMARY="$(LLM_MODEL_SUMMARY)" LLM_MODEL_SUMMARY_MEGA="$(LLM_MODEL_SUMMARY_MEGA)" LLM_MODEL_BRAINY=$(LLM_MODEL_BRAINY) LLM_MODEL_LONG="$(LLM_MODEL_LONG)" \
		LLM_MODEL_WORDS_MAX="$(LLM_MODEL_WORDS_MAX)" OCR_MODEL="$(OCR_MODEL)" \
		TOPIC="$(query)" HTML_DUMP_FILTER="$(HTML_DUMP_FILTER)"


.PHONY: default
