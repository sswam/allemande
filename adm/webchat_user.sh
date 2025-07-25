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

6. Press the 'E' button to visit the 'nsfw' zone. There will be NSFW images, of course. Say hi and have a chat if you like.
7. NSFW features work in private, but it's much easier to learn in a group chat.
"
		patreon_links=$'- https://www.patreon.com/allychat (SFW)\n- https://www.patreon.com/allychatx (NSFW)'
	else
		patreon_links="- https://www.patreon.com/allychat"
	fi

	change-password "$@" |
	while read -r _ user pass; do
		cat <<END
=== WARNING: Ally Chat is a Power Tool ===

Please be sure to read this whole message before logging in, for your own safety! If it becomes apparent to me that you haven't read this message, I might disable your account.


=== Cautionary Tales ===

Wally joined Ally Chat, but he didn't press the ? button for the Intro and AI Help! Wally expected the app to be simple like ChatGPT, but Ally Chat is a power tool. Wally got confused right away, and gave up before he even got started. Don't be a chuckle-monkey like Wally!

Sally joined Ally Chat, and read the whole user guide! She was having so much fun in private chat, that she forgot to give any feedback. I contacted her, but she didn't reply. So I disabled her account. I could have restored it, but she never asked. Don't be a fraidy-bunny like Sally!


=== Welcome to Ally Chat! ===

This is an indie AI chat app, developed by one person with a lot of help from Claude.

Login at https://$ALLEMANDE_DOMAIN
Username: $user
Password: $pass


=== Getting Started ===

The following steps are required, not a suggestion!

1. Say hi and have a quick chat in the main 'Ally Chat' room
2. Press the '?' button and read the Intro
3. Open the 'help' tab and ask the AI some questions
  - This is the place to get help about the app
  - Close it with the X at top-right

These steps are strongly recommended:

4. Stay in group chat for a start, not private chat
  - Meet me (Sam) and some other friendly users
  - You'll learn how the app works
5. Please contact me for a demo in the app. You can also watch a demo video: https://allemande.ai/demo
  - If you skip the demo, you will have a hard time getting started, and you won't be very useful for the beta programme
  - I'll give you some good tips, and we'll make a custom character for you
$start_nsfw
I like chatting with users and helping out, so hit me up for a chat any time.


=== Content Rules ===

We don't believe in censorship or 'AI safety'. You are responsible for your own behaviour and safety.

1. No sexualisation of minors in text or media
2. No sexualised images of real people without consent

I have no problem with any other sort of content, so don't be afraid to talk with me about anything.


=== Beta Program ===

In return for the free and unlimited AI service, I am asking all users to give back in some way. For example:

1. Participate in group chat from time to time:
  - just chat in a public room... don't be scared, it's fun
  - share funny stories, your best art, new characters, etc
  - this will help you and others to learn about the app
  - it will help build the community
2. Ask me for support. Don't be shy! This helps me improve the app
3. Give feedback to me, preferably in a group chat
4. Come up with your own way to give back
5. Support us on Patreon if you like

If you don't want to do any of that, this service isn't for you. If you do contribute, barring calamity you will continue to enjoy unlimited AI services from Ally Chat.

Do you have any questions or concerns about the beta programme? Please let me know.


=== Unlimited Service ===

Usage is currently not limited even for free users, because the costs are very low, and users aren't abusing it. The AI art and most of the AI chat costs us almost nothing. Other AI chat options typically cost only a fraction of a cent per request, which is fine.

I cannot guarantee literally unlimited service for free, that would be impossible for a small business. But in practice, I have not had to limit anyone at all yet. Some users have generated many thousands of AI art images. Not a problem!

If your usage starts to be too costly, I will let you know, and we can figure out what to do about it. For example, if you talk to an expensive model like Claude all day and night, or get him to review your thesis over and over again, it could be a problem!


=== Patreon ===

This project has no investors, just me. I can develop it better with a bit of financial support and encouragement! So, please consider supporting on Patreon:

$patreon_links

Free-tier users have access to all models and features, but subscribers get some good perks too.

Subscriptions start at \$5 per month. You can also join as a free member, to follow our updates.
END
	done

	mkdir -p rooms/"$user"
	chmod o-rwx rooms/"$user"
	mkdir -p static/users/"$user"
	touch static/users/"$user"/styles.css
	touch static/users/"$user"/script.js
	ln -sf ../../themes/dark.css static/users/"$user"/theme.css

	ln -sf ../../rooms.dist/help.bb.base rooms/"$user"/.help.bb.base
	if ((nsfw)); then
		cp ../rooms.dist/mission.m.nsfw rooms/"$user"/mission.m
		cp ../rooms.dist/deny_image_gen_nsfw.yml rooms/"$user"/.access.yml
	else
		cp ../rooms.dist/mission.m.sfw rooms/"$user"/mission.m
		cp ../rooms.dist/deny_image_gen_sfw.yml rooms/"$user"/.access.yml
	fi
	cp ../rooms.dist/.gitignore rooms/"$user"/.gitignore

	if ((!nsfw)); then
		ln -sf ../../doc/guide.md rooms/"$user"/.help.m
	fi

	echo "- $user" >> rooms/.access.yml

	if ((nsfw)); then
		echo "- $user" >> rooms/nsfw/.access.yml
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
	sudo userdel -- "$user" || true

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

# version: 0.1.0
