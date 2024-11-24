SERVER="allemande.ai"
SERVER_SSH="$SERVER"
SERVER_ROOMS_SSH="$SERVER_SSH:$ALLEMANDE_ROOMS"

ALLYCHAT_ADMINS="root"
ALLEMANDE_ROOMS_SERVER="$ALLEMANDE_HOME/rooms.server"
CHATPATH="$ALLEMANDE_ROOMS:$ALLEMANDE_ROOMS_SERVER"

user=${USER^}
bot=Ally
room="Ally Chat"
file=$ALLEMANDE_ROOMS/$room.bb
file_server=$ALLEMANDE_ROOMS_SERVER/$room.bb
mission=$'system:\tYou are friends and co-workers talking face to face and working enthusiastically together.'
add_prompts=1   # 1
rewind=2

TOKEN_LIMIT=131072  # 2000  100
LLM_MODEL="default.gguf"

DEAFEN="--deafen"
#speak="speak.py --model coqui:tts_models/en/ek1/tacotron2 --tempo 1.2 --pitch 4 $DEAFEN"
speak="speak.py --model coqui:tts_models/en/ljspeech/tacotron2-DDC_ph --tempo 1.3 --pitch 3 $DEAFEN"
#speak="speak.py --model coqui:tts_models/en/ljspeech/tacotron2-DDC --tempo 1.1 --pitch 3 $DEAFEN"
#speak="speak.py --model coqui:tts_models/en/ljspeech/glow-tts --tempo 1.2 --pitch 4 $DEAFEN"
#speak="speak.py --model gtts:en:co.uk --tempo 1.3 --pitch -1 $DEAFEN"
