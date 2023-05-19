# set environment variables and paths for Allemande AI toolkit

set -a

ALLEMANDE_ENV=$(realpath "${BASH_SOURCE[0]}")
ALLEMANDE_HOME=$(dirname "$ALLEMANDE_ENV")
ALLYCHAT_HOME="$ALLEMANDE_HOME/webchat"
ALLYCHAT_THEMES="$ALLYCHAT_HOME/static/themes"

ALLEMANDE_MODELS="$ALLEMANDE_HOME/models"

ALLEMANDE_USER="allemande"
ALLEMANDE_PORTS="/var/spool/allemande"
ALLEMANDE_MODULES="llm_llama stt_whisper"
ALLEMANDE_BOXES="prep todo doing done error history"

ALLEMANDE_SCREEN="allemande"

ALLEMANDE_ROOMS="$ALLEMANDE_HOME/rooms"

ALLEMANDE_AUDIO_LOCK="/var/lock/allemande-audio.lock"

if [ -e "$ALLEMANDE_HOME/venv" ]; then
	. "$ALLEMANDE_HOME/venv/bin/activate"
fi

PYTHON=$(which python3)

for dir in py text www chat anthropic google; do
	PYTHONPATH=${PYTHONPATH:-}:$ALLEMANDE_HOME/$dir
done

for dir in adm core sys tools text data image audio video code llm openai anthropic web chat voice-chat eg www html table i3 git gradio apps; do
	PATH=$PATH:$ALLEMANDE_HOME/$dir
done

: ${CONFIG:=$ALLEMANDE_HOME/config.sh}

if [ ! -e "$CONFIG" ]; then
	ln -s "$ALLEMANDE_HOME/config/config-dist.sh" "$CONFIG"
fi

. "$CONFIG"

GRADIO_ANALYTICS_ENABLED=False
