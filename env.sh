# set environment variables and paths for Allemande AI toolkit

set -a

ALLEMANDE_GITHUB=git@github.com:sswam/allemande.git
BARBARELLA_GITHUB=git@github.com:sswam/barbarella.git
ALLEMANDE_ENV=$(realpath "${BASH_SOURCE[0]}")
ALLEMANDE_HOME=$(dirname "$ALLEMANDE_ENV")
ALLYCHAT_HOME="$ALLEMANDE_HOME/webchat"
ALLYCHAT_THEMES="$ALLYCHAT_HOME/static/themes"

ALLEMANDE_MODELS="$ALLEMANDE_HOME/models"

ALLEMANDE_USER="allemande"
ALLEMANDE_UID="777"
ALLEMANDE_GID="$ALLEMANDE_UID"
ALLEMANDE_PORTS="/var/spool/allemande"
ALLEMANDE_MODULES="llm_llama stt_whisper"
ALLEMANDE_BOXES="prep todo doing done error history"

ALLEMANDE_SCREEN="allemande"

ALLEMANDE_ROOMS="$ALLEMANDE_HOME/rooms"

ALLEMANDE_AUDIO_LOCK="/var/lock/allemande-audio.lock"

ALLEMANDE_LLM_DEFAULT="c"  # Claude
ALLEMANDE_LLM_DEFAULT_CHEAP="i"  # Claude Haiku

ALLEMANDE_VENV=
if [ -e "$ALLEMANDE_HOME/venv" ]; then
	ALLEMANDE_VENV="$ALLEMANDE_HOME/venv"
	. "$ALLEMANDE_VENV/bin/activate"
fi

PYTHON=$(which python3)
PYTHONPATH=${PYTHONPATH:-}:$ALLEMANDE_HOME

for dir in python text www chat anthropic google llm scrape tools files tty; do
	PYTHONPATH=${PYTHONPATH:-}:$ALLEMANDE_HOME/$dir
done

PERL5LIB=${PERL5LIB:-}:$ALLEMANDE_HOME

for dir in perl; do
	PERL5LIB=${PERL5LIB:-}:$ALLEMANDE_HOME/$dir
done

for dir in adm core sys tools text data image audio video code llm anthropic chat voice-chat eg www html markup i3 git gradio wordpress python perl scrape misc youtube email prompt unprompted geo subs files bash tty ally; do
	PATH=$PATH:$ALLEMANDE_HOME/$dir
done

for appdir in "$ALLEMANDE_HOME/apps"/*; do
	if [ ! -d "$appdir" ]; then
		continue
	fi
	app=$(basename "$appdir")
	PATH=$PATH:$ALLEMANDE_HOME/apps/$app
done

: ${CONFIG:=$ALLEMANDE_HOME/config.sh}

if [ ! -e "$CONFIG" ]; then
	echo "Creating config.sh: $CONFIG"

	v ln -s "$ALLEMANDE_HOME/config/config-dist.sh" "$CONFIG"
fi

. "$CONFIG"

GRADIO_ANALYTICS_ENABLED=False
