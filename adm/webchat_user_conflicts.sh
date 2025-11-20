#!/usr/bin/env bash
#
# webchat-user-conflicts: Check for conflicts between webchat users and virtual agents
# output to ~/conficts.txt

webchat_user_conflicts() {
	eval "$(ally)"

	cd ~/users

	< "$ALLYCHAT_HOME"/.htpasswd cut -f1 -d: | sort > users.txt
	(cd "$ALLEMANDE_AGENTS" ; find . -name '*.yml' | grep -v '/\.' | sed 's/\.yml$//; s/.*\///') | lc | sort > agents.txt
	< ~/rooms/.agents_global.yml sed 's/^  - //' | lc | sort > agents_loaded.txt

	printf '## virtual agents\n'
	comm -3 agents.txt agents_loaded.txt | tee virtual_agent_conflicts.txt
	printf '\n'

	printf '## user / agent conflicts\n'
	comm -1 -2 agents_loaded.txt users.txt | tee user_agent_conflicts.txt
	printf '\n'
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	webchat_user_conflicts "$@"
fi
