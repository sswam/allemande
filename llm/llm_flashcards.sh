#!/bin/bash
# llm-flashcards: a script to generate flashcards using GPT-4 or Claude

user=""
adj=""
topic=""
types="concepts, terms, and other topics"
m=
noref=	# no reference text

. opts

if [ -n "$adj" ]; then
  adj="$adj "
fi
if [ -n "$topic" ]; then
  topic=", about $topic"
fi
if [ -n "$user" ]; then
  user=", for $user"
fi
ref="Here is the reference material:"
if [ -n "$noref" ]; then
  ref=""
fi

prompt1="Can you please make me some ${adj}flashcards in the following format$topic$user?
Please list the main $types, with definitions suitable for flashcard study, in the form:

Prompt: the prompt
Answer: the bare answer, *not including the prompt*
Extra: extra extended info

Include a blank line between cards. Preferably make the notes suitable for reversible flashcards, i.e. they should still make sense if prompt and answer are swapped, so don't include the main words from the prompt in the answer. Note: Do not include key words from the prompt in the answer! Please include mathematical equations if needed (using TeX), code examples, command samples, links, and markdown images (linked from online) where appropriate. Please highlight the main terms in boldface.

Even if it doesn't seem a suitable topic for flashcard study, please have a go anyway. Please produce rich and detailed flashcards, with plenty of extra info.
"

prompt2="$prompt1
Only give the requested output."

if [ -n "$ref" ]; then
	prompt1="$prompt1
$ref
"
fi

v llm process -m "$m" "$prompt1" --prompt2 "$prompt2"

#PromptImage: a search query that should return relevant images for the prompt; include this only if the flashcard needs an image on the prompt side
#AnswerImage: a search query that should return relevant images for the answer; include this only if the flashcard needs an image on the answer side
