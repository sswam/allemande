#!/usr/bin/env bash
# Update the Ally Chat front-end version in static/service_worker.js
# so that files will be refreshed.
set -e
cd "$ALLEMANDE_HOME/webchat/static"
modify perl -pe '
	s/^const VERSION = "(\d+)\.(\d+)\.(\d+)";$/qq{const VERSION = "$1.$2.} . ($3 + 1) . qq{";}/e
' : service_worker_in.js
chmod +w service_worker.js || true
perl -pe '
	use File::Slurp;
	if (m{^// CONFIG$}) {
		$_ = read_file("config.js");
	}
' <service_worker_in.js >service_worker.js
chmod -w service_worker.js
