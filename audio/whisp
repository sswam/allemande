#!/bin/bash -eu
# <whisper options and args>
# whisp: a bash wrapper for whisper and whisper.cpp via whisper-cpp.sh

if [ "$1" == -c ] && shift || ! command -v whisper &> /dev/null; then
	v whisper-cpp.sh "$@"
else
	v whisper "$@" || v whisper-cpp.sh "$@"
fi

# TODO 1. use Allemande ports API if available
# TODO 2. use Python whisper 
# TODO 3. use whisper-cpp.sh
# TODO 4. use whisper-api.py to access whisper through OpenAI APIs if an API key is defined
