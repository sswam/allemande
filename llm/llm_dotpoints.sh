#!/bin/bash
m=
. opts
llm process -m "$m" "Please summarize the following in dot points, in the same tense and person as the original. Only give the dot point summary, each line starting with '- '."
