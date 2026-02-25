#!/usr/bin/env bash

# [add|passwd|rm|off|on|list|restore]
# Manage users in the Allemande webchat

# shellcheck disable=SC2164	# Disable warnings about 'cd' without checking

webchat-user() {
	local nsfw= n=        # enable nsfw for a user; list nsfw users only; 0 to list sfw users only
	local preference= p=  # preferred assistant gender (m/f/o/a)
	local language= l=    # preferred language (code)

	eval "$(ally)"

	local command=${1:-}
	shift || true

	cd "$ALLEMANDE_HOME"
	# shellcheck disable=SC1091
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
	restore)
		restore-user "$@"
		;;
	show)
		show-user "$@"
		;;
	*)
		die "Usage: webchat-user {add|passwd|rm|off|on|list|missions|restore|show} [args...]"
		;;
	esac
}

add-user() {
	local user=${1-}
	local contact=${2-}

	if [ -z "$user" ]; then
		read -r -p "Username: " user
	fi
	if [ -z "$contact" ]; then
		read -r -p "Contact info: " contact
	fi
	# if [[ "$user" != "${user,,}" ]]; then
	# 	die "Username must be lower-case"
	# fi
	# can't start with -, a safety feature for me not typing -n in the wrong place!
	if [[ "$user" == -* ]]; then
		die "Username cannot start with a dash"
	fi

	while true; do
		case "$preference" in
			m|f|o|a) break;;
		esac
		read -r -p "Preferred assistant gender (m/f/o/a): " preference
		if [ ! -t 0 ]; then
			break
		fi
	done

	if [ -z "$language" ]; then
		read -r -p "Preferred language (code) [en]: " language
	fi
	if [ -z "$language" ]; then
		language="en"
	fi

	if [ -n "$user" ]; then
		if nsfw='' list-users | grep -q "^$user$"; then
			die "User $user already exists"
		fi
	fi

	local patreon_links
	local generated_pass
	patreon_links="- https://www.patreon.com/allychat"
	if ((nsfw)); then
		patreon_links+=$'\n- https://www.patreon.com/allychatx (NSFW)'
	fi

	change-password "$user" |
	while read -r _ generated_pass; do
		cat <<END
=== Welcome to Ally Chat! ===

https://$ALLEMANDE_DOMAIN
User: $user
Pass: $generated_pass

=== Getting Started ===

- There's one content rule: Keep it legal, specifically no NCII or CSAM images.
- Please explore private chat with your first AI. Then press ? and read the intro
- Try joining a group chat too. We're friendly and we like to help new users!

=== Please Contribute! ===

- You can help: join group chats, share your work, give feedback, join our Patreon.
- If you're willing and able, you can help with development, marketing, etc.

=== Patreon ===

$patreon_links

=== Terms of Use ===

You are responsible for your own safety and behaviour in Ally Chat.

The only content rule is to keep it legal:

- No NCII (real people without consent).
- No CSAM (underage NSFW images).
- Literally anything else is okay.

We have a uniquely friendly and respectful international community,
including men, women, non-binary, LGBTQIA+ users, and people with disabilities.

Our group chats are good fun! This is the best way to learn the app properly and to get support.

We like to have fun, including playful banter, but we don't allow unwanted bullying or abuse in the main group chats.

Note that I may remove inactive accounts after a month or so. Please log in and try the app within 2 weeks. I can restore accounts on request, but your username might be different.

You can read more formal and detailed Terms of Use at https://allemande.ai/terms.html

Please confirm that you agree!
END
	done

	mkdir -p rooms/"$user"
	chmod g-w,o-rwx rooms/"$user"
	mkdir -p static/users/"$user"
	touch static/users/"$user"/styles.css
	touch static/users/"$user"/script.js
	ln -sf ../../themes/night.css static/users/"$user"/theme.css

	ln -sf ../../rooms.dist/help.bb.base rooms/"$user"/.help.bb.base
	if ((nsfw)); then
		cp ../rooms.dist/access_nsfw.yml rooms/"$user"/.access.yml
		_set_user_mission_file "$user" nsfw "$preference" "$language"
	else
		_set_user_mission_file "$user" sfw "$preference" "$language"
	fi
	cp ../rooms.dist/.gitignore rooms/"$user"/.gitignore

	if ((!nsfw)); then
		ln -sf ../../doc/help.md rooms/"$user"/.help.m
	fi

	if ((nsfw)); then
		echo "- $user" >> rooms/nsfw/.access.yml
		ln -sf ../../doc/nsfw/help.md rooms/"$user"/.help.m
		ln -sf ../../rooms.dist/help.bb.base.nsfw rooms/"$user"/.help.bb.base
	else
		ln -sf ../../rooms.dist/help.bb.base rooms/"$user"/.help.bb.base
	fi

	if [ ! -e rooms/"$user"/help.bb ]; then
		# delay to avoid detecting the change twice, with the dir add and the file add
		(sleep 1; cp rooms/"$user"/.help.bb.base rooms/"$user"/help.bb && touch -t 197001010000 rooms/"$user"/help.bb && chmod o-rwx rooms/"$user"/help.bb) &
	fi

	# Set up info.rec file
	local btime
	btime=$(date '+%Y-%m-%d %H:%M:%S')

	# Parse contact info
	local email='' reddit='' discord='' facebook='' contact_other=''

	if [[ "$contact" == email:* ]]; then
		email="${contact#email:}"
	elif [[ "$contact" == *@* ]]; then
		email="$contact"
	elif [[ "$contact" == reddit:* ]]; then
		reddit="${contact#reddit:}"
	elif [[ "$contact" == u/* ]]; then
		reddit="${contact#u/}"
	elif [[ "$contact" == discord:* ]]; then
		discord="${contact#discord:}"
	elif [[ "$contact" == facebook:* ]]; then
		facebook="${contact#facebook:}"
	else
		contact_other=$contact
	fi

	# Create info.rec file
	cat > static/users/"$user"/info.rec <<-END
		name:	$user
		status:	active
		btime:	$btime
		is_nsfw:	${nsfw:-0}
		preference:	$preference
		language:	$language
		email:	$email
		reddit:	$reddit
		discord:	$discord
		facebook:	$facebook
		agents:
		contact:	$contact_other
		notes:

END
	chmod o-rwx static/users/"$user"/info.rec

	# rooms git: ignore user's dir
	cd rooms
	echo "/$user" >> .gitignore

	# add git to user's dir with arcs
	cd "$user"
	yes n | qos arcs -i
	mkdir -p "$ALLEMANDE_HOME/ally-git/$user"
	mv -T .git "$ALLEMANDE_HOME/ally-git/$user/.git"
	ln -s "$ALLEMANDE_HOME/ally-git/$user/.git" .git

	# run webchat/Makefile
	cd "$ALLYCHAT_HOME"; qos make
}

change-password() {
	local user=${1:-} pass=${2:-}
	local gen
	if [ "$pass" = "-i" ]; then
		gen=0
		while true; do
			read -r -s -p "Enter password: " pass1
			echo
			read -r -s -p "Confirm password: " pass2
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
	echo "$user:$pass" | sudo chpasswd 2>/dev/null || true

	if [ "$gen" = 1 ]; then
		printf "+ %s\n" "$pass"
	fi
}

remove-user() {
	local user=${1:-}
	if [ -z "$user" ]; then
		read -r -p "Username: " user
	fi

	# Store htpasswd entry for potential restore
	local removed_dir
	removed_dir=$(get-available-name --dir ~/users-removed/"$user")

	grep "^$user:" .htpasswd > "$removed_dir/htpasswd.entry"

	htpasswd -D .htpasswd "$user"

	# remove from any .access.yml lists
	find rooms/ -name .access.yml | xa sed -i "/^- $user\$/d"

	# remove style and user directory
	mv rooms/"$user" "$removed_dir"/rooms
	mv static/users/"$user" "$removed_dir"/user
	mv "$ALLEMANDE_HOME/ally-git/$user" "$removed_dir"/git

	sudo userdel -- "$user" || true

	printf -- "- %s\n" "$user"

	# run webchat/Makefile
	cd "$ALLYCHAT_HOME"; make
}

restore-user() {
	local user=${1:-}
	local new_user=${2:-}  # Optional: new username to restore to

	if [ -z "$user" ]; then
		read -r -p "Username: " user
	fi

	# If new_user is provided, use it; otherwise restore to original name
	local target_user="${new_user:-$user}"

	# Check if target user already exists
	if grep -q "^$target_user:" .htpasswd; then
		die "User $target_user already exists in htpasswd"
	fi

	# Find the most recent removed user directory
	local removed_dir
	removed_dir=$(find ~/users-removed -maxdepth 1 -type d \( -name "$user" -o -name "$user-*" \) 2>/dev/null | sort -V | tail -n1)

	if [ -z "$removed_dir" ]; then
		die "No removed user directory found for $user"
	fi

	# Restore htpasswd entry if available, changing username if needed
	if [ -s "$removed_dir/htpasswd.entry" ]; then
		if [ "$user" != "$target_user" ]; then
			# Change username in htpasswd entry
			sed "s/^$user:/$target_user:/" "$removed_dir/htpasswd.entry" >> .htpasswd
			echo >&2 "Restored htpasswd entry for $target_user (from $user)"
		else
			cat "$removed_dir/htpasswd.entry" >> .htpasswd
			echo >&2 "Restored htpasswd entry from backup"
		fi
	else
		echo >&2 "No htpasswd entry found to restore for user $user"
	fi

	# Restore directories
	mv -T "$removed_dir"/rooms rooms/"$target_user"  || true
	mv -T "$removed_dir"/user static/users/"$target_user" || true
	mv -T "$removed_dir"/git "$ALLEMANDE_HOME/ally-git/$target_user" || true

	# Update info.rec if username changed
	if [ "$user" != "$target_user" ]; then
		local user_info_file="static/users/$target_user/info.rec"
		if [ -f "$user_info_file" ]; then
			sed -i "s/^name:	$user$/name:	$target_user/" "$user_info_file"
		fi
	fi

	# Restore NSFW access if user info indicates NSFW
	local user_info_file="static/users/$target_user/info.rec"
	local is_nsfw
	is_nsfw=$(awk '/^is_nsfw:/ {print $2}' "$user_info_file")
	if [ "$is_nsfw" = "1" ]; then
		if ! grep -q "^- $target_user$" rooms/nsfw/.access.yml; then
			echo "- $target_user" >> rooms/nsfw/.access.yml
			echo >&2 "Restored NSFW access for user $target_user"
		fi
	fi

	printf "+ %s\n" "$target_user"

	# Remove the removed directory if empty
	rmdir "$removed_dir" 2>/dev/null || true

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

show-user() {
	local user=${1:-}
	if [ -z "$user" ]; then
		read -r -p "Username: " user
	fi
	cat static/users/"$user"/info.rec
}

_set_user_mission_file() {
	local user=$1
	local type=$2 # sfw or nsfw
	local preference=$3
	local language=$4
	local verbose=${5:-} # pass "-v" for verbose

	local preference_suffix
	case "$preference" in
	m) preference_suffix="male" ;;
	f) preference_suffix="female" ;;
	o) preference_suffix="other" ;;
	a) preference_suffix="all" ;;
	*)
		echo >&2 "Warning: invalid gender preference '$preference' for user $user. Using female assistant."
		preference_suffix="female"
		;;
	esac

	language_suffix=""
	if [ "$language" != en ]; then
		language_suffix=".$language"
	fi

	local mission_file_basename="mission.m.$type.$preference_suffix$language_suffix"
	local mission_file="$ALLEMANDE_HOME/rooms.dist/$mission_file_basename"
	local mission_path="$ALLEMANDE_ROOMS/$user/mission.m"

	(cd "$ALLEMANDE_HOME/rooms.dist" || exit; translate-mission "$mission_file_basename")

	# shellcheck disable=SC2086
	cp $verbose "$mission_file" "$mission_path"
}

_update_user_mission() {
	local user=$1
	local type=$2 # sfw or nsfw

	local preference=f # default to female
	local language=en
	local user_info_file="$ALLEMANDE_USERS/$user/info.rec"
	if [ -f "$user_info_file" ]; then
		local pref_from_file lang_from_file
		pref_from_file=$(awk '/^preference:/ {print $2}' "$user_info_file")
		if [ -n "$pref_from_file" ]; then
			preference="$pref_from_file"
		fi
		lang_from_file=$(awk '/^language:/ {print $2}' "$user_info_file")
		if [ -n "$lang_from_file" ]; then
			language="$lang_from_file"
		fi
	else
		echo >&2 "Warning: $user_info_file not found for user $user. Using default settings."
	fi

	_set_user_mission_file "$user" "$type" "$preference" "$language" -v
}

update-missions() {
	nsfw=0 list-users |
	while read -r user; do
		[ -e "$ALLEMANDE_ROOMS/$user/mission.m" ] || continue
		_update_user_mission "$user" sfw
	done

	nsfw=1 list-users |
	while read -r user; do
		[ -e "$ALLEMANDE_ROOMS/$user/mission.m" ] || continue
		_update_user_mission "$user" nsfw
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	webchat-user "$@"
fi

# version: 0.1.60
