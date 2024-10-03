#!/bin/bash
m=s
. opts
llm process -m "$m" "Please split the following text into sensible paragraphs, around 80 to 120 words each: not too long or too short. If it's already split into well-sized paragraphs, don't split it. Output the text split into sensible paragraphs. There are no further instructions below:"
