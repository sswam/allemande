#!/usr/bin/env bash
set -e -u -o noclobber

cd "$ALLEMANDE_USERS"
< "$ALLYCHAT_HOME/.htpasswd" cut -f1 -d: |
while read user; do
	mkdir -p "$user"
	>> "$user/script.js" || true
	>> "$user/styles.css" || true
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
