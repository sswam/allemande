#!/usr/bin/env bash
# [targets...]

translate-mission() {
  local model= m=claude  # LLM model to use

  eval "$(ally)"

  # Build each requested target
  for target; do
    # Extract language code from target filename (last component after dot)
    local lang=${target##*.}
    local src=${target%.*}

    # Error if target is same as source (no extension)
    if [ "$src" = "$target" ]; then
      echo "Error: Target '$target' has no extension to indicate language code." >&2
      continue
    fi

    # Skip if target exists or is newer than source
    if [ -f "$target" ] && ! [ "$target" -ot "$src" ]; then
      continue
    fi

    # Translate file using the language model
    (
      echo "**IMPORTANT NOTE: This user prefers to speak \$LANGUAGE. Please always communicate with them in \$LANGUAGE, unless they request otherwise.**"
      echo
      cat "$src"
    ) | process -m="$model" "Please translate for language code '$lang', don't change any content or layout, no prelude or comment; just translate please and include the full language name in place of \$LANGUAGE." >"$target"
  done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  translate-mission "$@"
fi

# version: 0.1.1
