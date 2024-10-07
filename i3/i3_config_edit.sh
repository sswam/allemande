#!/bin/bash -eu
# i3-config-edit: Edit i3 config file in a new terminal window.

step=${1:-1}
case "$step" in
1)
	xterm -e "bash -c '$0 2'"
	;;
2)
	vi ~/.i3/config +'nnoremap <C-z> <Nop>' +'normal gg' +/__WORKSPACES__ +'normal zt'
	i3 reload
	;;
esac
