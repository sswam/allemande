#!/bin/bash
# 
# edit files on PATH

eval "$(ally)"

set +a
IFS='
'
exec ${EDITOR:-vi} -O $(p $(which-file "$@"))
