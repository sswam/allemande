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
*** WARNING: Ally Chat is a cutting-edge power tool.  It's not a dumbed-down app for chuckle-monkeys.

There are a few rules, but we don't believe in censorship or "AI safety".  You are responsible for your own behaviour and your own safety.

Before you start, please read the story of "Wally".  It's short and it's sad.

Wally joined Ally Chat, but he didn't press the ? button, to read the Intro and use the AI Help!  He certainly didn't read the User Guide.  Wally expected Ally Chat to be simple like ChatGPT, but Ally Chat is a power tool.  Wally got confused right away, and gave up on Ally Chat before he even got started.  Don't be a chuckle-monkey like Wally!

We are building the best damn app on the planet.  Don't miss out.

^^^ You read that carefully, right? :)


Okay, then...

=== Welcome to Ally Chat! ===

Login at https://$ALLEMANDE_DOMAIN
Username: $user
Password: $pass

Getting Started:
1. Say "hi" in the "Ally Chat" room!
2. Press '?' and read the Intro
3. Visit the AI 'help' tab and ask some questions
4. Ask Sam for a demo.

If you don't follow these steps, we reserve the right to delete your account!

Please consider joining our Patreon to support the project.
- https://www.patreon.com/allychat

Free-tier users have access to all models and features, but subscribers get some good perks too.

We do need your help, if you can. Subscriptions start at \$5 / month.  You can also join as a free member.
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
• You can read the NSFW intro and guide when you are in the "nsfw" zone
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
