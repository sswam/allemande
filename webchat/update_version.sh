#!/usr/bin/env bash
# Update the Ally Chat front-end version in static/service_worker.js
# so that files will be refreshed.
modify perl -pe '
	s/^^const VERSION = "(\d+)\.(\d+)\.(\d+)";$/qq{const VERSION = "$1.$2.} . ($3 + 1) . qq{";}/e
' : static/service_worker.js
