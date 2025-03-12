#!/bin/bash -eu
cd "$ALLYCHAT_THEMES"
modify -p=4 proc -m=c "Please add at the top of the :root section a --theme-mode: light or dark depending on text vs background. Good luck!" : *.css
