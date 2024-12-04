#!/bin/bash -eu

# setup the allemande portals for a user
# usage: allemande-user-add [user [module ...]]

case "$1" in
-h|--help)
	echo "usage: allemande-user-add [user [module ...]]"
	exit 0
	;;
esac

. get-root

user=${1:-$SUDO_USER}
if [ "$#" -gt 0 ]; then shift; fi
modules=(${@:-$ALLEMANDE_MODULES})
portals="$ALLEMANDE_PORTALS"

for module in "${modules[@]}"; do
	module_dir="$portals/$module"
	mkdir -p "$module_dir"
	chown $ALLEMANDE_USER:$ALLEMANDE_USER "$module_dir"
	for client in $ALLEMANDE_PORTAL_CLIENTS; do
		portal_path="$module_dir/${client}_${user}"
		umask 007
		mkdir -p "$portal_path"
		(
			cd "$portal_path"
			mkdir -p $ALLEMANDE_BOXES
		)
		chown -R $user:$ALLEMANDE_USER "$portal_path"
		chmod -R g+s,ug-x+X "$portal_path"   # the 2 is for setgid (group sticky bit)
	done
done
