#!/bin/bash -eu

room=$1
base=${room%.bb}
mission=$base.m
summary=$base.s
summary2=$base.s.new

(
	printf '# Context\n\n'
	cat "$mission"
	printf '\n# Summary of Chat\n\n'
	cat "$summary"
	if [ -s "$summary" ]; then
		cat "$summary"
	else
		echo "[nothing yet]"
	fi
	printf '\n# New Chat\n\n'
	cat "$room"    # TODO XXX this is the whole chat history, should be just the new messages
) | process -m=i 'Please revise the Summary to include info from the New Chat that relates to the Context. Use a markdown bullet list, only return this list please. Try to include as much relevant info as possible while keeping the summary very concise. It is okay to remove or compact less important info in the existing summary, and group related info together in a logical order, we do not necessarily need to keep it in chronological order.' > "$summary2"


# Old experimental summary commands:

#process -m=c 'Please summarize info from the input chat in a markdown bullet list.' < test.bb > test.s
#time process -m=i 'Please summarize info from the input chat in a markdown bullet list.' < test.bb > test.s.i
#time process -m=i 'Please summarize info from the input chat in a markdown bullet list. Try to include as much info as possible while keeping the summary very concise. You can group related info together, no need to keep chronological order.' < test.bb > test.s.i.2
#vi -O test.s.i.2 test.s.i test.s

#time (printf '# Context\n\n' ; cat test.m ; printf '\n# Summary of Chat\n\n'; cat test.s; printf '\n# New Chat\n\n'; cat test.bb.2 ) | process -m=i 'Please revise the Summary to include info from the New Chat that relates to the Mission. Use a markdown bullet list. Try to include as much relevant info as possible while keeping the summary very concise. Group related info together in a logical order, no need for chronological order.' > test.s.2

#time (printf '# Context\n\n' ; cat t2.m ; printf '\n# Summary of Chat\n\n'; cat t2.s; if [ ! -s t2.s ]; then echo "[nothing yet]"; fi; printf '\n# New Chat\n\n'; cat t2.bb ) | process -m=i 'Please revise the Summary to include info from the New Chat that relates to the Context. Use a markdown bullet list, only return this list please. Try to include as much relevant info as possible while keeping the summary very concise. Group related info together in a logical order, no need for chronological order.' > t2.s
