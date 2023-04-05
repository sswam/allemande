#!/bin/bash -eu
file="$1"
user="$2"
bot="$3"

v barbarella.py -w "$HOME/chat:$HOME/chatZ" -c ~/barbarella/config/experiment.yaml --delim $'\n' -u "$user" -b "$bot" -n 200
# not: -r --no-trim
