BARBARELLA=$HOME/barbarella
CHATPATH=$HOME/chat
PATH=$PATH:$BARBARELLA:$BARBARELLA/tools:$BARBARELLA/voice
user=${USER^}
bot=Sarah
file=$HOME/chat/$user-$bot.bb
mission="system: You are good friends talking face to face in real life."
add_prompts=   # 1
rewind=2

speak="speak.py --model coqui:tts_models/en/ek1/tacotron2 --tempo 1.2 --pitch 2"
#speak="speak.py --model coqui:tts_models/en/ljspeech/tacotron2-DDC_ph --tempo 1.2 --pitch 1"
#speak="speak.py --model coqui:tts_models/en/ljspeech/tacotron2-DDC --tempo 1.0 --pitch 4"
#speak="speak.py --model coqui:tts_models/en/ljspeech/glow-tts --tempo 1.2 --pitch 4"
#speak="speak.py --model gtts:en:co.uk --tempo 1.3 --pitch -1"
