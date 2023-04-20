#!/bin/bash -eu

# Run assistant in watch mode with the experiment config, the -r option for
# raw / free-form input, the --delim "" option to avoid adding delimiters,
# and the --no-trim option to allow the model to predict the user.

dir="$PWD"
cd "$(dirname "$(readlink -f "$0")")/.."
chat.py -w "$dir" -c config/llm_llama/experiment.yaml "$@" -r --no-trim --delim $'\n'
