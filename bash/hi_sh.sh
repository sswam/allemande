#!/usr/bin/env bash
# Says hi, world

# shellcheck disable=SC1007,SC2034  # Disable certain shellcheck rules that conflict with ally options parser syntax

language= l=en        # language [fr|de|jp|cn], defaults to English
use_ai= a=           # greet using AI
model= m=            # LLM model

eval "$(ally)"

user_name=${1:-world}

if [ "$use_ai" = 1 ]; then
	query -m="$model" "Greet $user_name in $language. Keep it short and sweet."
else
	case "$language" in
	en) hello="Hi" ;;
	fr) hello="Salut" ;;
	es) hello="Hola" ;;
	de) hello="Hallo" ;;
	jp) hello="こんにちは" ;;
	cn) hello="你好" ;;
	*)
		echo >&2 "unknown language: $language"
		exit 1
		;;
	esac
	printf -- "%s, %s\n" "$hello" "$user_name"
fi

# version: 0.1.0
