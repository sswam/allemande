#!/usr/bin/env bash
modify perl -pe '
	s/^^const VERSION = "(\d+)\.(\d+)\.(\d+)";$/qq{const VERSION = "$1.$2.} . ($3 + 1) . qq{";}/e
' : static/service_worker.js
