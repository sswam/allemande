#!/usr/bin/env bash

# [add|passwd|rm|off|on|list]
# Manage users in the Allemande webchat

webchat-user() {
	local nsfw= n=   # include nsfw intro text

	eval "$(ally)"

	local command=${1:-}
	shift || true

	echo "args: @_"

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
https://allemande.ai

Getting Started with Ally Chat:

1. Log in and select "Ally Chat"
- The default "Ally Chat" room is public.
- Here you can interact with AI helpers like Flashi, Emmy, and Claude to learn about the app.

2. Talking to AI Characters
- Simply mention their name in your message.
- Available AIs: Flashi, Emmy, Claude, Ally, and many others.

3. Creating Images
- Illy is the main image generation model.
- Illu is an AI art expert who can:
	• create images using Illy
	• guide you through the image creation process

4. Continuing AI Conversations
- When AIs are talking to each other...
- Leave the message box empty.
- Click "Poke" to let them continue.
- Example: When Illu writes a prompt for Illy, click "Poke" to generate the image.
- Alternatively, you could copy the prompt, edit it and send that message.

5. Switching Rooms
- Click the room name at the top.
- Type a new room name (e.g. "$user/chat").
- Press Enter to switch.
END
		done
	if ((nsfw)); then
		echo "- $user" >> rooms/nsfw/.access.yml
		cat <<END

6. NSFW Features
- Ally Chat supports NSFW chat and image generation.
- To use NSFW features, please go to the "nsfw/nsfw" room.
- In this room, Flashi can help you learn about the app, including NSFW features.
- Xilu is an AI art expert similar to Illu, with more knowledge around NSFW art.
- To get started with NSFW images, talk to Xilu, then press "poke" when she writes an AI art prompt.
- You cannot talk to Anthropic, OpenAI, Perplexity or xAI models in the NSFW zone.
- Please do not talk to Anthropic, OpenAI, Perplexity or xAI models on NSFW topics in private chat.
- There is a section for more extreme adult content, available on request.
END
	fi
	mkdir -p rooms/"$user"
	chmod o-rwx rooms/"$user"
	mkdir -p users/"$user"
	ln -s ../../static/themes/forest.css users/"$user"/theme.css
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
