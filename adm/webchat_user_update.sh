#!/usr/bin/env bash
#
# Update user records for webchat system. Runs several maintenance tasks:
# - Fix user records - corrects data inconsistencies.
# - Audit user records - checks for missing or invalid data.
# - Resolve conflicts - identifies conflicting records, esp user vs agent names.
# - Nag users - apply nag messages to users based on usage and support.

# shellcheck disable=SC1007,SC2034  # Disable certain shellcheck rules that conflict with ally options parser syntax

webchat-user-update() {
	eval "$(ally)"

	cd ~/users

	(
		time v webchat-user-fix
		time v webchat-user-audit
		time v webchat-user-conflicts
		time v webchat-user-nag < ~/users.rec
	) 2>&1 | tee users.log
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	webchat-user-update "$@"
fi

# version: 0.1.0
