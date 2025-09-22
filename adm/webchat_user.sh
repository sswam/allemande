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
	missions)
		update-missions "$@"
		;;
	*)
		die "Usage: webchat-user {add|passwd|rm|off|on|list|missions} [args...]"
		;;
	esac
}

add-user() {
	local user=${1-}

	if [ -z "$user" ]; then
		read -r -p "Username: " user
	fi
	if [[ "$user" != "${user,,}" ]]; then
		die "Username must be lower-case"
	fi
	# can't start with -, a safety feature for me not typing -n in the wrong place!
	if [[ "$user" == -* ]]; then
		die "Username cannot start with a dash"
	fi

	if [ -n "$user" ] && nsfw= list-users | grep -q "^$user$"; then
		die "User $user already exists"
	fi

	local start_nsfw patreon_links
	if ((nsfw)); then
		start_nsfw="
For NSFW content:

5. Press the 'E' or enter 'nsfw' in the room field to visit the NSFW zone.
6. NSFW features also work in private chat.
"
		patreon_links=$'- https://www.patreon.com/allychat (SFW)\n- https://www.patreon.com/allychatx (NSFW)'
	else
		patreon_links="- https://www.patreon.com/allychat"
	fi

	change-password "$@" |
	while read -r _ user pass; do
		cat <<END
=== Welcome to Ally Chat! ===

Log in at https://$ALLEMANDE_DOMAIN
Username: $user
Password: $pass


=== Getting Started ===

1. Say hi in the main 'Ally Chat' room
2. Press the '?' button and read the Intro
3. Open the 'help' tab and ask the AI some questions
  - This is the place to get help about the app
4. Close the help with the X at top-right
$start_nsfw

=== Beta Program ===

- Ally Chat is a power tool, and can be confusing for beginners.
- You are responsible for your own safety and behaviour.
- I can give you a demo in the app, to help you get started.
- Please participate in group chats, and give feedback.
- You can support us on Patreon if you like the app.

$patreon_links
END
	done

	mkdir -p rooms/"$user"
	chmod g-w,o-rwx rooms/"$user"
	mkdir -p static/users/"$user"
	touch static/users/"$user"/styles.css
	touch static/users/"$user"/script.js
	ln -sf ../../themes/dark.css static/users/"$user"/theme.css

	ln -sf ../../rooms.dist/help.bb.base rooms/"$user"/.help.bb.base
	if ((nsfw)); then
		cp ../rooms.dist/mission.m.nsfw rooms/"$user"/mission.m
		cp ../rooms.dist/access_nsfw.yml rooms/"$user"/.access.yml
	else
		cp ../rooms.dist/mission.m.sfw rooms/"$user"/mission.m
	fi
	cp ../rooms.dist/.gitignore rooms/"$user"/.gitignore

	if ((!nsfw)); then
		ln -sf ../../doc/guide.md rooms/"$user"/.help.m
	fi

	# echo "- $user" >> rooms/.access.yml

	if ((nsfw)); then
		echo "- $user" >> rooms/nsfw/.access.yml
		ln -sf ../../doc/nsfw/guide.md rooms/"$user"/.help.m
		ln -sf ../../rooms.dist/help.bb.base.nsfw rooms/"$user"/.help.bb.base
	else
		ln -sf ../../rooms.dist/help.bb.base rooms/"$user"/.help.bb.base
	fi

	if [ ! -e rooms/"$user"/help.bb ]; then
		# delay to avoid detecting the change twice, with the dir add and the file add
		(sleep 1; cp rooms/"$user"/.help.bb.base rooms/"$user"/help.bb && touch -t 197001010000 rooms/"$user"/help.bb && chmod o-rwx rooms/"$user"/help.bb) &
	fi

	# rooms git: ignore user's dir
	cd rooms
	echo "/$user" >> .gitignore

	# add git to user's dir with arcs
	cd "$user"
	yes n | arcs -i

	# run webchat/Makefile
	cd "$ALLYCHAT_HOME"; make
}

change-password() {
	local user=${1:-} pass=${2:-}
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
		pass=$(pwgen 6 -B -1 | head -n1 | tr -d '\n')
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
	sudo userdel -- "$user" || true

	printf -- "- %s\n" "$user"

	# run webchat/Makefile
	cd "$ALLYCHAT_HOME"; make
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

update-missions() {
	nsfw=0 list-users |
	while read user; do
		[ -e "$ALLEMANDE_ROOMS/$user/mission.m" ] || continue
		cp -v "$ALLEMANDE_HOME"/rooms.dist/mission.m.sfw "$ALLEMANDE_ROOMS/$user/mission.m"
	done

	nsfw=1 list-users |
	while read user; do
		[ -e "$ALLEMANDE_ROOMS/$user/mission.m" ] || continue
		cp -v "$ALLEMANDE_HOME"/rooms.dist/mission.m.nsfw "$ALLEMANDE_ROOMS/$user/mission.m"
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	webchat-user "$@"
fi
