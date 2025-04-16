#!/usr/bin/env bash

# [add|passwd|rm|off|on|list]
# Manage users in the Allemande webchat

webchat-user() {
	local nsfw= n=   # include nsfw intro text

	eval "$(ally)"

	local command=${1:-}
	shift || true

	cd ~/allemande
	. ./env.sh
	cd webchat

	case $command in
	add)
		add-user "$@"
		;;
	passwd)
		change-password "$@"
		;;
	rm)
		remove-user "$@"
		;;
	off)
		disable-user "$@"
		;;
	on)
		enable-user "$@"
		;;
	list)
		list-users "$@"
		;;
	*)
		die "Usage: webchat-user {add|passwd|rm|off|on|list} [args...]"
		;;
	esac
}

add-user() {
	local user=${1-}
	if [ -n "$user" ] && list-users | grep -q -F -w "$user"; then
		die "User $user already exists"
	fi

	change-password "$@" |
		while read -r _ user pass; do
			cat <<END
Here's the info to access Ally Chat:

user: $user
pass: $pass
https://$ALLEMANDE_DOMAIN

Getting Started with Ally Chat:

- Log in and select "Ally Chat"
- The default "Ally Chat" room is public.
- Here you can interact with AI helpers like Flashi, Emmy, and Claude to learn about the app.
END
		done

	mkdir -p rooms/"$user"
	chmod o-rwx rooms/"$user"
	mkdir -p users/"$user"
	ln -s ../../static/themes/pastel.css users/"$user"/theme.css

	if ((nsfw)); then
		echo "- $user" >> rooms/nsfw/.access.yml
		cat <<END > rooms/$user/.access.yml
reset: true
allow_agents: true
END
		cat <<END

NSFW Features:

- Ally Chat supports NSFW chat and image generation.
- To use NSFW features, please go to the "nsfw/nsfw" room.
- In this room, Flashi can help you learn about the app, including NSFW features.
END
	fi
}

change-password() {
	local user=${1:-} pass=${2:-}
	if [ -z "$user" ]; then
		read -r -p "Username: " user
	fi
	if [[ "$user" != "${user,,}" ]]; then
		die "Username must be lower-case"
	fi
	if [ -z "$pass" ]; then
		pass=$(pwgen 6 -1 | head -n1 | tr -d '\n')
	fi
	htpasswd -b .htpasswd "$user" "$pass"
	printf "+ %s %s\n" "$user" "$pass"
}

remove-user() {
	local user=${1:-}
	if [ -z "$user" ]; then
		read -r -p "Username: " user
	fi
	htpasswd -D .htpasswd "$user"

	# remove from any .access.yml lists
	find rooms/ -name .access.yml | xargs sed -i "/^- $user\$/d"

	# remove style and user directory
	move-rubbish users/"$user"

	printf -- "- %s\n" "$user"
}

disable-user() {
	local user=${1:-} comment=${2:-}
	if [ -z "$user" ]; then
		read -r -p "Username: " user
	fi
	if [ -z "$comment" ]; then
		read -r -p "Comment: " comment
	fi
	perl -pi -e "s/^\Q$user\E:(.*)\$/*$user:*\$1:$comment/" .htpasswd
	printf "_ %s\n" "$user"
}

enable-user() {
	local user=${1:-}
	if [ -z "$user" ]; then
		read -r -p "Username: " user
	fi
	perl -pi -e "s/^\*\Q$user\E:\*(.*?):?\$/$user:\$1/" .htpasswd
	printf "+ %s\n" "$user"
}

list-users() {
	local filter=${1:-}
	cut <.htpasswd -f1 -d":" | grep -i "$filter"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	webchat-user "$@"
fi

# version: 0.1.0
