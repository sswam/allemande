#!/bin/bash -eu
m=$ALLEMANDE_LLM_DEFAULT
. opts
query -m=$m "$@
Please reply with literally just Y/N (or '?' if there is no clear Y/N answer)"
