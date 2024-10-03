#!/usr/bin/env bash

# [prompt [reference files ...]] < input > output
# Convert something in the style of another file or author

alla() {
    local model m=       # LLM model
    local style s=0      # also refer to hello_$ext.$ext for style
    local translate t=0  # encourage translation
    local functional f=1 # ask for the result to be functionally equivalent

    eval "$(ally)"

    prompt="${1:-}"
    shift || true

    local refs=("$@")

    # Prepare file type style reference
    # shellcheck disable=SC2154
    style_ref="hello_$ext.$ext"
    if ((style)) && [ "$(wich "$style_ref")" ]; then
        refs+=("$style_ref")
    fi

    # Prepare the prompt for the AI
    local prompt2="Please restyle the input a la $prompt"
    if [ "${#refs[@]}" -gt 0 ]; then
        if [ -n "$prompt" ]; then
            prompt2+=" and"
        fi
        prompt2+=" the provided reference files."
    fi
    if [ -z "$prompt" ] && [ "${#refs[@]}" -eq 0 ]; then
        prompt2+=" carte blanche; i.e. you have complete freedom to act as you wish or think best."
    fi
    if ((translate)); then
        prompt2+=" You may even translate the input, or not, it's up to you."
    fi
    if ((functional)); then
        prompt2+=" Please restyle, but make the result functionally equivalent to the input, more or less."
    fi

    local input
    input=$(cat_named.py -p -b - "${refs[@]}")
    [ -z "$input" ] && input=":)"

    printf "%s\n" -- "$input" | process -m="$model" "$prompt2"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    alla "$@"
fi
