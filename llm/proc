#!/bin/bash -eu
m=
. opts
process -m="$m" "$@" "Please reply as concise as possible, with no boilerplate \
or unnecessary explanation. Do not abbreviate text unrelated to the request. \
If editing, do not make edits that are not requested (e.g. removing comments \
or blank lines). If the input has code but does not include code quoting with \
\`\`\`, the output should not include \`\`\` either. If writing code, be \
concise but clear, not obscure." | rstrip
