#!/usr/bin/env bash
set -e -u
cd
< $ALLYCHAT_HOME/.htpasswd cut -f1 -d: | sort > users.txt
(cd $ALLEMANDE_AGENTS ; find . -name '*.yml' | grep -v '/\.' | sed 's/\.yml$//; s/.*\///') | lc | sort > agents.txt
< ~/rooms/.agents_global.yml sed 's/^  - //' | lc | sort > agents_loaded.txt

echo "## virtual agents"
comm -3 agents.txt agents_loaded.txt 
echo

echo "## user / agent conflicts"
comm -1 -2 agents_loaded.txt users.txt
echo
