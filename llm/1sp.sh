#!/usr/bin/env bash

# [prompt [attachment...]]
# Process input text with an LLM, for a one-sentence answer

one_sentence() {
  local model= m=    # LLM model to use

  eval "$(ally)"

  local prompt="${1:-}"
  shift || true

  concise="Please reply with literally just one sentence, should fit in one line of a terminal, or absolutely as few lines as possible."

  process -m="$model" "$prompt"$'\n'"$concise" "$@" | text-strip
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  one_sentence "$@"
fi

# version: 0.1.1
