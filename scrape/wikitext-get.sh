#!/bin/bash -eu
page="$1"

page_esc=${page// /_}

wget "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles=$page_esc&rvslots=main" -O- |
jq -r '.query.pages | .[].revisions | .[].slots.main."*"'
