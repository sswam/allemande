#!/bin/bash -eu
for url; do
	web-text -- "$url"
done |
summary -m="flasho" -p="Concise clear language. If multiple pages, please do each separately, a paragraph or two for each page; try to cover all the main info: a good summary."
