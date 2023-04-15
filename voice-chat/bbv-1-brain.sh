#!/bin/bash -eu

nt brain

chat.py -w "$CHATPATH" -c "$ALLEMANDE/config/experiment.yaml" --delim $'\n' -u "$user" -b "$bot" -n 200 --ignore-shrink --ignore "$user:"
# not: -r --no-trim
