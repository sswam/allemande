#!/bin/bash -eu

# setup the allemande portals for a user
# usage: allemande-user-add [user [module ...]]

. get-root

user=${1:-$SUDO_USER}
if [ "$#" -gt 0 ]; then shift; fi
modules=(${@:-$ALLEMANDE_MODULES})
portals="$ALLEMANDE_PORTALS"
host="$HOSTNAME"

for module in "${modules[@]}"; do
	module_dir="$portals/$module"
	user_dir="$module_dir/${host}_${user}"

	mkdir -p "$module_dir"
	chown $ALLEMANDE_USER:$ALLEMANDE_USER "$module_dir"

	umask 007
	mkdir -p "$user_dir"
	(
		cd "$user_dir"
		mkdir -p $ALLEMANDE_BOXES
	)
	chown -R $user:$ALLEMANDE_USER "$user_dir"

	chmod -R g+s,ug-x+X "$user_dir"   # the 2 is for setgid (group sticky bit)
done
