#!/usr/bin/env bash
# Get the Ally Chat front-end version from static/service_worker.js
sed -n '/^const VERSION = / { s/.*"\([^"]*\)".*/\1/; p; }' < "$ALLEMANDE_HOME/webchat/static/service_worker.js"
