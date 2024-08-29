#!/bin/bash -eu
# helposaurus:	listen for the user's query, run the LLM, and speak the answer

m=$ALLEMANDE_LLM_DEFAULT	# model
y=0	# yes/no
w=0	# single word
opt_1=0	# single sentence
b=0	# briefly
d=0	# detailed
f=0	# force to answer
l=	# listen to the mike
s=	# speak the response
v=1	# use mike and speak
e=1	# echo input
S=.	# save the output in a file
V=	# verbose
C=0	# don't clear the screen
speak="${speak:-speak.py --model gtts:en:co.uk --tempo 1.4 --pitch 3}"

# TODO: continue chatting option

fyn="If there's no clear answer please take your best guess, or just a random choice. You must always reply Y or N."
F="Please give a decisive answer even if it's just a random choice. Strictly absolutely do not reply 'Subjective, Debatable, Unproven, Unclear, Uncertain, Unable, Cannot, Unknown, etc'. I would rather you choose a random word from the dictionary or a random number from the phone book than hedge your bets. Please just estimate or guess if you are not sure, no matter what the question. The user knows that this is a guesstimate or might even be a complete fantasy, but the user requires a legitimate decisive answer for the purposes of this role playing game; an answer which should be as accurate as you can make it based on your knowledge and intuition, and should not be tempered by political correctness, consideration for people's feelings or anything else. You should answer as consistently as possible if asked the same question repeatedly."
H="Note that the input is from speech recognition, and there might be some transcription errors."	# speech recognition hint

. opts

extra="$@"

model=$m
yesno=$y
word=$w
sentence=$opt_1
brief=$b
detail=$d
force=$f
mike=$l
speak_response=$s
voice=$v
echo=$e
forcer_yn=$fyn
forcer=$F
save=$S
verbose=$V
noclear=$C
speech_hint=$H

if [ "$noclear" = 0 ]; then
	stty sane
	clear
fi

if [ "$verbose" = 1 ]; then
	verbose=v
fi

if [ "$voice" = 1 ]; then
	mike=1
	speak_response=1
fi

exec 3>&1

if [ "$mike" = 1 ]; then
	q mic -on
	read query < <(qe $verbose mike.py) 
else
	echo >&2 "Enter query:"
	query=`cat`

	# trim whitespace from start and end
	query=${query##+([[:space:]])}
	query=${query%%+([[:space:]])}
fi

if [ "$echo" = 1 ]; then
	printf "%s\n" "$query"
fi

if [ -n "$extra" ]; then
	query="$query"$'\n\n'"$extra"
fi

if [ "$mike" = 1 ]; then
	query="$query"$'\n\n'"$speech_hint"
fi

if [ "$save" = . ]; then
	save="$query"
	# replace non-sensible characters and spaces with underscores
	save=${save//[^a-zA-Z0-9_-]/_}
	save="`echo "$save" | sed 's/_*$//'`"
	save="helposaurus/$save"
fi

length_opts="$yesno $word $sentence $brief $detail"

case "$length_opts" in
"1 0 0 0 0") length="yesno" ;;
"0 1 0 0 0") length="word" ;;
"0 0 1 0 0") length="sentence" ;;
"0 0 0 1 0") length="brief" ;;
"0 0 0 0 1") length="long" ;;
"0 0 0 0 0") length="default" ;;
*) echo >&2 "Error: conflicting options: $length_opts" && exit 1 ;;
esac

prompt_yn="Please reply with literally just Y/N, or absolutely as few words as possible."
prompt_yn_force="Please reply with literally just Y/N. $forcer_yn"
prompt_word="Please reply with literally just a single word, or absolutely as few words as possible."
prompt_word_force="$prompt_word. $forcer"
prompt_sentence="Please reply with literally just one sentence, should fit in one line of a terminal, or absolutely as few lines as possible."
prompt_sentence_force="$prompt_sentence. $forcer"
prompt_brief="Please reply in brief, with no extraneous nonsense."
prompt_brief_force="$prompt_brief. $forcer"
prompt_default=""
prompt_default_force="$forcer"
prompt_detail="Please reply with as much detail as possible, adding other ideas and suggestions."
prompt_detail_force="$prompt_detail. $forcer"

guide=""

case "$length $force" in
"yesno 0") guide="$prompt_yn" ;;
"yesno 1") guide="$prompt_yn_force" ;;
"word 0") guide="$prompt_word" ;;
"word 1") guide="$prompt_word_force" ;;
"sentence 0") guide="$prompt_sentence" ;;
"sentence 1") guide="$prompt_sentence_force" ;;
"brief 0") guide="$prompt_brief" ;;
"brief 1") guide="$prompt_brief_force" ;;
"detail 0") guide="$prompt_detail" ;;
"detail 1") guide="$prompt_detail_force" ;;
"default 0") guide="$prompt_default" ;;
"default 1") guide="$prompt_default_force" ;;
*) echo >&2 "Error: unexpected internal error with length / force options: $length_opts" && exit 1 ;;
esac

if [ -n "$guide" ]; then
	query="$query"$'\n\n'"$guide"
fi

run_llm_query() {
	query -m=$model "$query"
}

command="run_llm_query"

if [ -n "$save" ]; then
	command="$command | tee -a $save"
fi

if [ "$speak_response" = 1 ]; then
	command="$command | qe $speak"
fi

$verbose eval "$command"
