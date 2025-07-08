#!/usr/bin/env bash

# [add|passwd|rm|off|on|list]
# Manage users in the Allemande webchat

webchat-user() {
	local nsfw= n=   # enable nsfw for a user; list nsfw users only; 0 to list sfw users only

	eval "$(ally)"

	local command=${1:-}
	shift || true

	cd "$ALLEMANDE_HOME"
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
	if [ -n "$user" ] && nsfw= list-users | grep -q "^$user$"; then
		die "User $user already exists"
	fi

	change-password "$@" |
		while read -r _ user pass; do
			cat <<END
Welcome to Ally Chat!

Important Tips:
• Stay in the main "Ally Chat" room while learning
• Let me give you a quick demo to help you get started
• Your feedback helps improve the app
• Optional: Support us on Patreon (link in intro)

Login Details:
• Site: https://$ALLEMANDE_DOMAIN
• Username: $user
• Password: $pass

Quick Start:
1. Log in with credentials above
2. Join the main "Ally Chat" room (PG-rated) and say hi!
3. Check the "?" help button and read the intro
4. Use the "help" tab to chat with the assistant
5. Message Sam to schedule your demo
END
		done

	mkdir -p rooms/"$user"
	chmod o-rwx rooms/"$user"
	mkdir -p static/users/"$user"
	touch static/users/"$user"/styles.css
	touch static/users/"$user"/script.js
	ln -sf ../../themes/dark.css static/users/"$user"/theme.css

	ln -sf ../../rooms.dist/help.bb.base rooms/"$user"/.help.bb.base
	cp ../rooms.dist/mission.m rooms/"$user"/mission.m

	if ((!nsfw)); then
		ln -sf ../../doc/guide.md rooms/"$user"/.help.m
	fi

	echo "- $user" >> rooms/.access.yml

	if ((nsfw)); then
		echo "- $user" >> rooms/nsfw/.access.yml
		cat <<END > rooms/$user/.access.yml
reset: true
allow_agents: true
END
		cat <<END

NSFW Features:

• Use the "nsfw" room for NSFW chat/images
• NSFW features work in private rooms too
• Join public rooms to learn from others
END
		ln -sf ../../doc/nsfw/guide.md rooms/"$user"/.help.m
		ln -sf ../../rooms.dist/help.bb.base.nsfw rooms/"$user"/.help.bb.base
	else
		ln -sf ../../rooms.dist/help.bb.base rooms/"$user"/.help.bb.base
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
	users=$(
		cut <.htpasswd -f1 -d":" | grep -i "$filter" | sort
	)
	nsfw_users=$(
		< rooms/nsfw/.access.yml yq -r '.allow | .[]' | sort
	)
	case "$nsfw" in
	"")
		printf "%s\n" "$users"
		;;
	"1")
		printf "%s\n" "$nsfw_users"
		;;
	"0")
		comm -13 <(printf "%s\n" "$nsfw_users") <(printf "%s\n" "$users")
		;;
	esac
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	webchat-user "$@"
fi

# version: 0.1.0
