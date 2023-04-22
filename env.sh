# set environment variables and paths for Allemande AI toolkit

ALLEMANDE_ENV=$(realpath "${BASH_SOURCE[0]}")
ALLEMANDE_HOME=$(dirname "$ALLEMANDE_ENV")

ALLEMANDE_MODELS="/opt/models"

ALLEMANDE_USER="allemande"
ALLEMANDE_PORTS="/var/spool/allemande"
ALLEMANDE_MODULES="llm_llama stt_whisper"
ALLEMANDE_BOXES="prep todo doing done error history"

ALLEMANDE_ROOMS="$ALLEMANDE_HOME/rooms"

PYTHON=$(which python3)

PYTHONPATH=$PYTHONPATH:$ALLEMANDE_HOME/py:$ALLEMANDE_HOME/text

for dir in adm core sys tools text data image audio video code openai anthropic web chat voice-chat eg; do
	PATH=$PATH:$ALLEMANDE_HOME/$dir
done

: ${CONFIG:=$ALLEMANDE_HOME/config.sh}

if [ ! -e "$CONFIG" ]; then
	ln -s "$ALLEMANDE_HOME/config/config-dist.sh" "$CONFIG"
fi

. "$CONFIG"
