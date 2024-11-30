#!/bin/bash -eu

# TODO in addition to the context / mission we need a short "topic", which we can use in the summary prompts to help direct them.

room=$1
base=${room%.bb}
room=$base.bb
new=$base.new
mission=$base.m
summary=$base.s
summary2=$base.s.new
summary3=$base.s.all
model1=i	# Anthropic Claude Instant LLM, aka "Clia"; this model is fast, cheap, and seems to be adequate to maintain a good summary of chat.
model2=c	# Anthropic "Claude" LLM
# model2=4	# GPT-4, aka "Emmy"

(
	printf '# Context\n\n'
	cat "$mission"
	printf '\n# Previous Summary\n\n'
	cat "$summary"
	if [ -s "$summary" ]; then
		cat "$summary"
	else
		echo "[nothing yet]"
	fi
	printf '\n# New Chat\n\n'
#	< "$room" tail -n "$tail"   # TODO this is messy, better use a message count or something
	cat "$new"
) |
tee /dev/stderr |
process -m=$model1 'Please summarize the New Chat in a markdown list, without any preamble / heading / intro. Use the Context and Previous Summary for background info. Please keep anything that seems important from the new chat.' > "$summary2"

echo
echo -----------------
echo

cat "$summary2"

(
	printf '# Context\n\n'
	cat "$mission"
	printf '\n# Chat Summary 1\n\n'
	cat "$summary"
	printf '\n# Chat Summary 2\n\n'
	cat "$summary2"
) |
tee /dev/stderr |
process -m=$model2 'Please combine the two Chat Summaries. Improve, condense and reorganize the combined summary, keeping the format of nested markdown lists. Use the Context for background info only. Remove duplicate info but keep anything that seems important. There is no need to keep the final summary in the same order or in chronological order. Please do not use generic headings such as "Discussion", rather organize the summary by topic.' > "$summary3"

echo
echo -----------------
echo

cat "$summary3"



# Old experimental summary commands:

# process -m=$model 'Please copy the Previous Summary, and revise it to add info from the New Chat that relates to the Context. Output the Modified Summary as a markdown bullet list, including most or all info from the Previous Summary, and summary info from the New Chat. Include all relevant info while keeping the Summary concise. It is okay to remove some less important info, but please keep anything important. If in doubt, copy the entire previous summary then add new entries at the end. Please group related info together in a logical order: we do not necessarily need to keep it in chronological order. The Summary will grow over time.' > "$summary2"

#process -m=c 'Please summarize info from the input chat in a markdown bullet list.' < test.bb > test.s
#time process -m=i 'Please summarize info from the input chat in a markdown bullet list.' < test.bb > test.s.i
#time process -m=i 'Please summarize info from the input chat in a markdown bullet list. Try to include as much info as possible while keeping the summary very concise. You can group related info together, no need to keep chronological order.' < test.bb > test.s.i.2
#vi -O test.s.i.2 test.s.i test.s

#time (printf '# Context\n\n' ; cat test.m ; printf '\n# Summary of Chat\n\n'; cat test.s; printf '\n# New Chat\n\n'; cat test.bb.2 ) | process -m=i 'Please revise the Summary to include info from the New Chat that relates to the Mission. Use a markdown bullet list. Try to include as much relevant info as possible while keeping the summary very concise. Group related info together in a logical order, no need for chronological order.' > test.s.2

#time (printf '# Context\n\n' ; cat t2.m ; printf '\n# Summary of Chat\n\n'; cat t2.s; if [ ! -s t2.s ]; then echo "[nothing yet]"; fi; printf '\n# New Chat\n\n'; cat t2.bb ) | process -m=i 'Please revise the Summary to include info from the New Chat that relates to the Context. Use a markdown bullet list, only return this list please. Try to include as much relevant info as possible while keeping the summary very concise. Group related info together in a logical order, no need for chronological order.' > t2.s
