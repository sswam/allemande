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

* We strongly recommend you stay in the main "Ally Chat" room while you learn how the app works!
* and take up the developer's offer to give you a tour of the app

- Log in and select "Ally Chat".
- The main "Ally Chat" room is public.
- Use the "?" help function to read the intro and get in-depth help.
END
		done

	mkdir -p rooms/"$user"
	chmod o-rwx rooms/"$user"
	mkdir -p static/users/"$user"
	touch static/users/"$user"/styles.css
	touch static/users/"$user"/script.js
	ln -sf ../../themes/dark.css static/users/"$user"/theme.css

	ln -sf ../../rooms.dist/help.bb.base rooms/"$user"/.help.bb.base

	if ((!nsfw)); then
		ln -sf ../../doc/guide.md rooms/"$user"/.help.m
	fi

	if ((nsfw)); then
		echo "- $user" >> rooms/nsfw/.access.yml
		cat <<END > rooms/$user/.access.yml
reset: true
allow_agents: true
END
		cat <<END

NSFW Features:

- For NSFW chat and image generation, please go to the "nsfw" room.
- You can also use NSFW features in your private chat rooms.
END
		ln -sf ../../doc/nsfw/guide.md rooms/"$user"/.help.m
	fi

	if [ ! -e rooms/"$user"/help.bb ]; then
		# delay to avoid detecting the change twice, with the dir add and the file add
		(sleep 1; cp rooms/"$user"/.help.bb.base rooms/"$user"/help.bb; touch -t 197001010000 rooms/"$user"/help.bb) &
	fi

	# rooms git: ignore user's dir
	cd rooms
	echo "/$user" >> .gitignore

	# add git to user's dir with arcs
	cd "$user"
	yes n | arcs -i
}

change-password() {
	local user=${1:-} pass=${2:-}
	if [ -z "$user" ]; then
		read -r -p "Username: " user
	fi
	if [[ "$user" != "${user,,}" ]]; then
		die "Username must be lower-case"
	fi

	local gen
	if [ "$pass" = "-i" ]; then
		gen=0
		while true; do
			read -s -p "Enter password: " pass1
			echo
			read -s -p "Confirm password: " pass2
			echo

			if [ "$pass1" = "$pass2" ]; then
				pass="$pass1"
				break
			else
				echo "Passwords do not match. Please try again."
			fi
		done
	fi
	if [ -z "$pass" ]; then
		gen=1
		pass=$(pwgen 6 -1 | head -n1 | tr -d '\n')
	fi

	htpasswd -b .htpasswd "$user" "$pass"
	echo "$user:$pass" | sudo chpasswd || true

	if [ "$gen" = 1 ]; then
		printf "+ %s %s\n" "$user" "$pass"
	fi
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
	move-rubbish static/users/"$user"

	# Note: Does not remove their rooms/$user directory.
	sudo userdel "$user" || true

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
