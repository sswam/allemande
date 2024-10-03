#!/bin/bash
# llm-summary: Summarize text from stdin using an LLM
m=s
. opts
llm process -m "$m" "Please replace this text with a short cogent summary. Only give the summary."
