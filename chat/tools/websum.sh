#!/bin/bash -eu
for url; do
	web-text -- "$url"
done |
summary -m="flasho" -p="Concise, cogent, clear language. Try to cover all the main info: a good summary."
