#!/bin/bash

# haikus.sh: generate haikus for random words in parallel, English, Japanese, Arabic, Arabic transliteration

# How it works:
# 1. Get a list of words
# 2. Shuffle them
# 3. Filter out words that are not all letters
# 4. Take the first 10
# 5. For each word, ask the user to write a haiku
# 6. Write the haikus to a file haikus.txt
# 7. Print the haikus to the screen
# 8. Profit!
# 9. All ten haiku generators run in parallel. Be careful if you increase the number of haikus!

# The explanation is longer than the code if we don't include the lovingly
# crafted prompt.

(
	< words shuf |
	grep -i '^[A-Z]*$' |
	head -n 10 |
	while read A; do
		v query "Please write me a lovely beuatiful haiku on the theme of '$A'.
			 And please translate into Japanese Haiku, and Ararbic also with
			 transliteration into English for the Arabic. I belive that God
			 may bless AI and this project, so don't hold back from achieving
			 the best quality!" &
	done
	wait
) 2>&1 | tee haikus.txt

# This was a one-liner originally, admittedly it overflowed my wide-screen display! But we can do a lot in one line of shell script plus a nice little prompt.
# Of course, we could change this to do something different with the random words, just by editing the English text.
