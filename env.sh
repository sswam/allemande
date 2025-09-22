# set environment variables and paths for Allemande AI toolkit

set -a

export HOSTNAME

ALLEMANDE_ENV=$(realpath "${BASH_SOURCE[0]}")
ALLEMANDE_HOME=$(dirname "$ALLEMANDE_ENV")
ALLEMANDE_GITHUB=git@github.com:sswam/allemande.git
BARBARELLA_GITHUB=git@github.com:sswam/barbarella.git
ALLYCHAT_HOME="$ALLEMANDE_HOME/webchat"
ALLYCHAT_PASSWD="$ALLYCHAT_HOME/.htpasswd"
ALLYCHAT_THEMES="$ALLYCHAT_HOME/static/themes"
ALLEMANDE_USERS="$ALLEMANDE_HOME/webchat/static/users"

ALLEMANDE_MODELS="$ALLEMANDE_HOME/models"
ALLEMANDE_LORA="$ALLEMANDE_HOME/lora"

ALLEMANDE_USER="allemande"
ALLEMANDE_UID="777"
ALLEMANDE_GID="$ALLEMANDE_UID"
CHATUSER_GID="60000"
ALLEMANDE_PORTALS="/var/spool/allemande"
ALLEMANDE_MODULES="llm_llama stt_whisper image_a1111"
ALLEMANDE_BOXES="prep todo doing done error history"

ALLEMANDE_SCREEN="allemande"

ALLEMANDE_ROOMS="$ALLEMANDE_HOME/rooms"
ALLEMANDE_AGENTS="$ALLEMANDE_HOME/agents"
ALLEMANDE_VISUAL="$ALLEMANDE_HOME/visual"
ALLEMANDE_WEBCACHE="$ALLEMANDE_HOME/webcache"

ALLEMANDE_AUDIO_LOCK="/var/lock/allemande-audio.lock"

ALLEMANDE_LLM_DEFAULT="claude"
ALLEMANDE_LLM_DEFAULT_SMALL="flashi"

ALLY_DISABLE_DEPRECATION_WARNINGS="0"

ALLEMANDE_VENV=
if [ -e "$ALLEMANDE_HOME/venv" ]; then
	ALLEMANDE_VENV="$ALLEMANDE_HOME/venv"
	if [ -z "${VIRTUAL_ENV:-}" ]; then
		. "$ALLEMANDE_VENV/bin/activate"
	fi
fi

PYTHON=$(which python3)
PYTHONPATH=${PYTHONPATH:+$PYTHONPATH:}$ALLEMANDE_HOME
MYPY_CACHE_DIR="$HOME/.cache/mypy"

for dir in python text www chat audio speech anthropic google llm scrape tools files tty data video image js markdown; do
	PYTHONPATH=${PYTHONPATH:-}:$ALLEMANDE_HOME/$dir
done

PERL5LIB=${PERL5LIB:+$PERL5LIB}:$ALLEMANDE_HOME

for dir in perl; do
	PERL5LIB=${PERL5LIB:-}:$ALLEMANDE_HOME/$dir
done

ALLEMANDE_PATH="adm core sys tools text data image audio speech video code llm anthropic chat voice-chat eg www html markup i3 git gradio wordpress python perl scrape misc youtube email prompt unprompted geo subs files bash tty ally pdev time bash/tests python/tests perl/tests c markdown x11 apps/story debian richtext refactor math vpn wasm linux css arcs amps safety net"

# TODO only use canon and alias
# for dir in canon alias; do

PATHS=""
for dir in ally canon alias; do
	PATHS=${PATHS:+$PATHS:}$ALLEMANDE_HOME/$dir
done

# for appdir in "$ALLEMANDE_HOME/apps"/*; do
# 	if [ ! -d "$appdir" ]; then
# 		continue
# 	fi
# 	app=$(basename "$appdir")
# 	PATHS=${PATHS#:}:$ALLEMANDE_HOME/apps/$app
# done

PATH="$PATHS:$PATH:$ALLEMANDE_HOME/node_modules/.bin"

: ${CONFIG:=$ALLEMANDE_HOME/config.sh}

if [ ! -e "$CONFIG" ]; then
	echo "Creating config.sh: $CONFIG"

	cp "$ALLEMANDE_HOME/config/config.sh.dist" "$CONFIG"
fi

NVCC_PREPEND_FLAGS="-ccbin /usr/bin/gcc-13"
CUDACXX="/usr/local/cuda/bin/nvcc"
PATH="$PATH:/usr/local/cuda/bin"

. "$CONFIG"

ALLEMANDE_SITE_URL="https://$ALLEMANDE_DOMAIN"
ALLYCHAT_CHAT_DOMAIN="chat.$ALLEMANDE_DOMAIN"
ALLYCHAT_ROOMS_DOMAIN="rooms.$ALLEMANDE_DOMAIN"
ALLYCHAT_CHAT_URL="https://$ALLYCHAT_CHAT_DOMAIN"
ALLYCHAT_ROOMS_URL="https://$ALLYCHAT_ROOMS_DOMAIN"

SERVER_SSH="$SERVER"
SERVER_ROOMS_SSH="$SERVER_SSH:$ALLEMANDE_ROOMS"
SERVER_PERSON_SSH="$SERVER_SSH:$ALLEMANDE_VISUAL/person"

GRADIO_ANALYTICS_ENABLED=False
JUPYTER_PLATFORM_DIRS=1	# get rid of spurious warnings in pytest

if [ -r "$ALLEMANDE_HOME/secrets.sh" ]; then
	. "$ALLEMANDE_HOME/secrets.sh"
fi
