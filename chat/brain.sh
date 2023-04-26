#!/bin/bash -eua

llama-chat.py -w "$CHATPATH" -c "/home/sam/allemande/config/llm_llama/experiment.yaml" --delim $'\n' -u "$user" -b "$bot" -n 200 --ignore-shrink --ignore "$user:"

# not using options: -r --no-trim
