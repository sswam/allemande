#!/bin/bash -e
# speak: speak text using a text-to-speech engine

# Usage: speak [options] [text]

# Option defaults

h=
play="ffplay"
q=0
in=/dev/stdin
out=
v=
# engine="coqui"
engine="gtts"
model="tts_models/en/ljspeech/glow-tts"
tempo=0
pitch=0
rate=0
format=wav
hideout=hideout
lang=en
accent=co.uk

# Example usage, with a variety of interesting sentences:

# speak "Hello world"
# speak -engine=gtts "The quick brown fox jumps over the lazy dog"
# speak -engine=coqui -model=tts_models/en/ljspeech/glow-tts "Once upon a time, the princess Gracelynn was kidnapped by an evil king."
# speak -engine=coqui --tempo=1.5 "Hello world"
# speak -engine=coqui "Hello world" -out=hello.wav -format wav

. opts

text="$*"

# Usage

if [ "$h" ]; then
	cat <<EOF
EOF
	# print the options from the script itself
	sed -n '/\. opts/q; 1d; s/^# //; s/=/\t/; p' "$0"
	exit 0
fi

# Function to load tool templates

load() {
	local fn args
	while read -r fn args; do
		eval "$fn() { command $args; }"
	done
}

# engine templates

load <<'EOF'
coqui	$hideout tts	--model_name $model --out_path "$out" --text "$text"
gtts	$hideout gtts-cli -t $accent -l $lang -o "$out" "$text"
EOF

# player templates

#load <<'EOF'
#ffplay	q ffplay	-nodisp -autoexit -af atempo=$tempo "$in"
#play	play	-q "$in" tempo $tempo
#mpv	mpv	--speed=$tempo "$in"
#mplayer	mplayer	-speed $tempo -af scaletempo "$in"
#vlc	cvlc	--play-and-exit --rate=$tempo "$in"
#EOF

load <<'EOF'
ffplay	q ffplay	-nodisp -autoexit "$in"
play	play	-q "$in"
mpv	mpv	 "$in"
mplayer	mplayer	 "$in"
vlc	cvlc	--play-and-exit "$in"
EOF


# Function to remove the temporary file

function cleanup {
    rm -f "$audio"
}

# if an output file is specified, use it, otherwise create a temporary file

out_or_temp() {
	if [ -z "$out" ]; then
		out=$(mktemp --suffix=".$format" --tmpdir $(basename $0).XXXX)
		trap cleanup EXIT
	fi
}

out_or_temp

# if text is specified, use it, otherwise read from stdin

if [ -n "$text" ]; then
	exec </dev/null
else
	text=$(<"$in")
fi

# generate speech with the specified engine and save it to the output file

$engine

# modify the output file with the specified audio filters

if [ "$pitch" != 0 -o "$rate" != 0 -o "$tempo" != 0 ]; then
	# At this point "$out" is actually an mp3
	# even if we requested wav.
	tmp=$(mktemp --suffix=".wav" --tmpdir $(basename $0).XXXX)
	tmp2=$(mktemp --suffix=".wav" --tmpdir $(basename $0).XXXX)
	ffmpeg -y -loglevel error -i "$out" "$tmp"
	sox "$tmp" "$tmp2"
	rm -f "$out"
	hideerr soundstretch "$tmp2" "$out" -tempo="$tempo" -pitch="$pitch" -rate="$rate"
	rm "$tmp" "$tmp2"
fi

# play the output file with the specified audio player

if [ -n "$play" ]; then
	in=$out $play
fi
