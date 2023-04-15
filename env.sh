ALLEMANDE_ENV=$(realpath "${BASH_SOURCE[0]}")
ALLEMANDE=$(dirname "$ALLEMANDE_ENV")

PYTHONPATH=$PYTHONPATH:$ALLEMANDE/py

for dir in adm core tools text data image audio video code gpt web voice-chat eg; do
	PATH=$PATH:$ALLEMANDE/$dir
done

: ${CHATPATH:=$HOME/chat}
