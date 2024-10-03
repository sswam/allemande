#!/bin/bash -eu
m=$ALLEMANDE_LLM_DEFAULT
. opts
query -m=$m "$@
Please reply with literally just Y/N. If there's no clear answer please take your best guess, or just a random choice. You must always reply Y or N."
