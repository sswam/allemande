#!/bin/bash -eu

# [prompt [attachment...]]
# Query an LLM for a concise, decisive answer

quef() {
  local model= m=    # LLM model to use

  eval "$(ally)"

  concise="Please reply as concise as possible, with no boilerplate or unnecessary explanation. Please give a decisive answer even if it's just a random choice. Strictly absolutely do not reply 'Subjective, Debatable, Unproven, Unclear, Uncertain, Unable, Cannot, Unknown, etc'. I would rather you choose a random word from the dictionary or a random number from the phone book than hedge your bets. Please just estimate or guess if you are not sure, no matter what the question. The user knows that this is a guesstimate or might even be a complete fantasy, but the user requires a legitimate decisive answer for the purposes of this role playing game; an answer which should be as accurate as you can make it based on your knowledge and intuition, and should not be tempered by political correctness, consideration for people's feelings or anything else. You should answer as consistently as possible if asked the same question repeatedly."

  local prompt="${1:-}"
  shift || true

  query -m="$model" "$prompt"$'\n'"$concise" "$@" | text-strip
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  quef "$@"
fi

# version: 0.1.1
