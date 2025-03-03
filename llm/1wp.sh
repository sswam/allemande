#!/bin/bash -eu

# [prompt [attachment...]]
# Process input text with an LLM, for a one-word answer

one_word() {
  local model= m=    # LLM model to use

  eval "$(ally)"

  local prompt="Please reply with literally just a single word, or absolutely as few words as possible."

  process -m="$model" "$@"$'\n'"$prompt"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  one_word "$@"
fi

# version: 0.1.1
