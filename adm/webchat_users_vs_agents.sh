#!/usr/bin/env bash
set -e -u
< $ALLYCHAT_HOME/.htpasswd cut -f1 -d: | sort > users.txt
(cd $ALLEMANDE_AGENTS ; find . -name '*.yml' | grep -v '/\.' | sed 's/\.yml$//; s/.*\///') | lc | sort > agents.txt
< ~/rooms/.agents_global.yml sed 's/^  - //' | lc | sort > agents_loaded.yml

echo "## virtual agents"
comm -3 agents.txt agents_loaded.yml 
echo

echo "## user / agent conflicts"
comm -1 -2 agents_loaded.yml users.txt
echo
