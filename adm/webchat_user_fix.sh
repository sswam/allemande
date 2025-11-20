#!/usr/bin/env bash
# sam
# webchat user fix - ensure each user has necessary files:
# - script.js - empty user script
# - styles.css - empty user styles
# - theme.css - symlink to default theme if missing
# - info.rec - user info record with default values if missing

webchat_user_fix() {
	eval "$(ally)"

	cd "$ALLEMANDE_USERS"
	< "$ALLYCHAT_HOME/.htpasswd" cut -f1 -d: |
	while read -r user; do
		mkdir -p "$user"
		touch "$user/script.js"
		touch "$user/styles.css"
		if [ ! -e "$user/theme.css" ]; then
			ln -s "../../themes/dark.css" "$user/theme.css"
		fi
		if [ ! -e "$user/info.rec" ]; then
			btime=$(stat -c %w "$ALLEMANDE_ROOMS/$user")
			btime=${btime%%.*}
			(
			techo name status btime email reddit discord facebook agents contact notes
			techo "$user" active "$btime"
			) | tsv2recs -a > "$user/info.rec"
			chmod o-rwx "$user/info.rec"
		fi
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	webchat_user_fix "$@"
fi
