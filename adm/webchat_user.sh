#!/bin/bash -eu
# webchat-user: manage users in the Allemande webchat
cd ~/allemande
. ./env.sh
cd webchat
. opts

function add_user() {
	if list_users | grep -q -F -w "$1"; then
		echo "User $1 already exists"
		exit 1
	fi
	echo "`change_password "$@"`" |
	while read x user pass; do
		cat <<END
Here's the info to access Ally Chat:

user: $user
pass: $pass
https://allemande.ai

Log in, then click "Ally Chat". The default room "Ally Chat" is a public room. You can change the room name at the top then press enter, e.g. change it to $user/yourtopic

To talk with an AI character, mention their name, e.g. Ally, Emmy, Dav, Claude, Clia. The main image model is Illy. If an AI is talking to another AI or agent, you can press "poke" to allow the chat to continue.
END
	done
}

function change_password() {
	local user=${1:-} pass=${2:-}
	if [ -z "$user" ]; then
		read -p "Username: " user
	fi
	if [ -z "$pass" ]; then
		pass=`pwgen 6 -1 | head -n1 | tr -d '\n'`
	fi
	htpasswd -b .htpasswd "$user" "$pass"
	echo "+ $user $pass"
}

function remove_user() {
	local user=${1:-}
	if [ -z "$user" ]; then
		read -p "Username: " user
	fi
	htpasswd -D .htpasswd "$user"
	echo "- $user"
}

function disable_user() {
	local user=${1:-} comment=${2:-}
	if [ -z "$user" ]; then
		read -p "Username: " user
	fi
	if [ -z "$comment" ]; then
		read -p "Comment: " comment
	fi
	perl -pi -e "s/^\Q$user\E:(.*)\$/*$user:*\$1:$comment/" .htpasswd
	echo "_ $user"
}

function enable_user() {
	local user=${1:-}
	if [ -z "$user" ]; then
		read -p "Username: " user
	fi
	perl -pi -e "s/^\*\Q$user\E:\*(.*?):?\$/$user:\$1/" .htpasswd
	echo "+ $user"
}

function list_users() {
	local filter=${1:-}
	< .htpasswd cut -f1 -d":" | grep -i "$filter"
}

function main() {
	cmd=${1:-}
	shift || true
	case $cmd in
	"add")
		add_user "$@"
		;;
	"passwd")
		change_password "$@"
		;;
	"rm")
		remove_user "$@"
		;;
	"off")
		disable_user "$@"
		;;
	"on")
		enable_user "$@"
		;;
	"list")
		list_users "$@"
		;;
	*)
		echo "Usage: $0 {add|passwd|rm|off|on|list} [args...]"
		exit 1
		;;
	esac
}

if [[ "$0" == "$BASH_SOURCE" ]]; then
	main "$@"
fi
