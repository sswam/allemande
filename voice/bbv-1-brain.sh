#!/bin/bash -eu

nt brain

barbarella.py -w "$CHATPATH" -c "$BARBARELLA/config/experiment.yaml" --delim $'\n' -u "$user" -b "$bot" -n 200 --ignore-shrink --ignore "$user:"
# not: -r --no-trim
