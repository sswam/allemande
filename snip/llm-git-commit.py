#	llm process -m "$model" 'Please describe this possibly broken unified diff patch for a git commit message following the Conventional Commits spec. Describe actual changes only (lines beginning with - and +, respecting the format:
#
#```
#feat|fix|docs|style|refactor|test|chore|perf(short-module-name): a short summary line around 50-70 chars
#
#- concise info about first change, indented if wrapped
#- concise info about second change, if any
#
#IF THE PATCH DOES NOT FIX SOMETHING, PLEASE DO NOT SAY THAT IT DID!!!!  BE CAREFUL, TRIPLE CHECK etc.
#IF THE PATCH DOES NOT FIX SOMETHING, PLEASE DO NOT SAY THAT IT DID!!!!  BE CAREFUL, TRIPLE CHECK etc.
#IF THE PATCH DOES NOT FIX SOMETHING, PLEASE DO NOT SAY THAT IT DID!!!!  BE CAREFUL, TRIPLE CHECK etc.
#If a patch or the surrounding code is broken I want to know.
#
#Only one main line (feat/fix), then a blank line, then the list if needed.
#For simple commits, you can omit the list. Avoid redundancy and excessive detail.
#If there are any new or peripheral bugs, include `BUG: ` lines explaining them briefly. Do not mention fixed bugs. No extra commentary.
#```

