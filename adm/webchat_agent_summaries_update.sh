#!/usr/bin/env bash
mkdir -p "$ALLEMANDE_HOME/doc/summary"
find "$ALLEMANDE_AGENTS" -name '.?*' -prune -o -name '*.yml' -type f -print |
while read file; do
	name=$(basename "$file")
	name=${name%.yml}
	summary_file="$ALLEMANDE_HOME/doc/summary/$name.txt"
	if [ "$summary_file" -nt "$file" ]; then
		continue
	fi
	echo -n "$name: "
	< "$file" process -m=gf "Please summarise this character or agent '$name' in a single line, including their occupation, function, and visual appearance; if given (esp. gender, hair, eyes, ethnicity). Vary the form of the expression while sticking to the basic format shown.
Example: 
  **Zozzi**: A practical and observant young French woman, known for her keen insights, striking blue eyes and long wavy blonde hair
If the fullname is given or known and differs from the main name, note it like so:
  **Zozzi*: Zozzi Jones, a practical ...
If any info is not given, just omit it, don't use any placeholder. The output should be 'finished' where possible.
Some characters are well-known people or fictional characters, if so please note how they are known, e.g. from a TV show or movie, etc.
Some are AI agents, AI art models (mostly based on SDXL or PonyXL), or software tools rather than people. Please summarise whatever is known about them.
If a character has a visual description, describe them as a person not an AI; also mention any functionality or what they work on (the context is a multi-AI group chat app). If an AI agents lacks personality prompting, mention them as an AI model.
Some have a 'base' agent. If the derived agent lacks detail, please describe any differences e.g.:
  **Zoz**: A concise variant of Zozzi
  **Cozzi**: A variant of Zozzi, using the Anthropic Claude model
" | tee "$summary_file"
done
