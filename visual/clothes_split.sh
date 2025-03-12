#!/bin/bash -eu
# Agent.yml ...
# Split clothes into clothes_upper and clothes_lower

PARALLEL_MAX=4

process_agent() {
	local agent="$1"
	pyq -F yaml -i "$agent" -- "{ visual: {clothes: .visual.clothes }}" |
	proc "Please output similar YAML with clothes_upper and clothes_lower for upper and lower body. If it spans both, put in clothes_upper. Anything around the waist would go in lower. Omit the original clothes key. Output only correct YAML please, nothing else." |
	pyq -F yaml -i "$agent" - | tee "$agent.new"
	mv "$agent.new" "$agent"
	echo "$agent"
}

for agent; do
	. parallel process_agent "$agent"
done
wait
