#!/usr/bin/env bash
# Update the Ally Chat front-end version in static/service_worker_in.js
# so that files will be refreshed.
set -e -u -o pipefail
cd "$ALLEMANDE_HOME/webchat/static"

modify perl -pe '
	s/^const VERSION = "(\d+)\.(\d+)\.(\d+)";$/qq{const VERSION = "$1.$2.} . ($3 + 1) . qq{";}/e
' : service_worker_in.js

chmod +w service_worker_gen.js || true
perl -pe '
	use File::Slurp;
	if (m{^// CONFIG$}) {
		$_ = read_file("config.js");
	}
' <service_worker_in.js >service_worker_gen.js
chmod -w service_worker_gen.js

find . -name '*_in.*' |
while read file; do
	if [ "$file" = "./service_worker_in.js" ]; then
		continue
	fi
	out="${file/_in\./_gen\.}"
	echo "$file -> $out" >&2
	envsubst '$ALLEMANDE_DOMAIN,$ALLYCHAT_CHAT_DOMAIN,$ALLYCHAT_ROOMS_DOMAIN' < "$file" > "$out"
done
