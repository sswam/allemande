# The `env.sh` script sets various environment variables and paths for my AI toolkit, Allemande. It initializes the 'bot' variable with the value 'Barbie', updates the Python path, and sets the PATH environment variable to include several directories within the Allemande framework. Lastly, it initializes the CHATPATH variable with the user's home directory followed by '/chat'.

ALLEMANDE_ENV=$(realpath "${BASH_SOURCE[0]}")
ALLEMANDE_HOME=$(dirname "$ALLEMANDE_ENV")

ALLEMANDE_MODELS="/opt/models"

ALLEMANDE_USER="allemande"
ALLEMANDE_PORTS="/var/spool/allemande"
ALLEMANDE_MODULES="llm_llama stt_whisper"
ALLEMANDE_BOXES="prep todo doing done error history"

PYTHON=$(which python3)

. "$ALLEMANDE_HOME/voice-chat/env.sh"

PYTHONPATH=$PYTHONPATH:$ALLEMANDE_HOME/py

for dir in adm core tools text data image audio video code openai anthropic web chat voice-chat eg; do
	PATH=$PATH:$ALLEMANDE_HOME/$dir
done

: ${CHATPATH:=$HOME/chat}
