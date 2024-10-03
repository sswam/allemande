#!/bin/bash
m=s
. opts
llm process -m "$m" "Please give a topic for the following, in the same tense and person as the original. Only give the topic."
