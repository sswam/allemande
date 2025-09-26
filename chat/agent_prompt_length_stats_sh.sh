find "$ALLEMANDE_AGENTS" "$ALLEMANDE_ROOMS/agents" "$ALLEMANDE_ROOMS/nsfw/agents" -name '*.yml' | while read A; do <"$A" agent-prompts | wc | k 1 2 3; done
