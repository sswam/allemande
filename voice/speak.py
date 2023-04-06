#!/usr/bin/env python3
""" Text-to-speech """

import sys
from sys import stdin
import os
import tempfile
import logging
from functools import partial
import multiprocessing
import torch

from argh import arg, dispatch_command
import sounddevice as sd
import numpy as np
from TTS.api import TTS
from TTS.utils.manage import ModelManager
from TTS.utils.synthesizer import Synthesizer
import soundfile
from gtts import gTTS
# from soundstretch import SoundStretch

from sh import amixer, soundstretch

logger = logging.getLogger(__name__)
logger_fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
logging.basicConfig(level=logging.DEBUG, format=logger_fmt)

DEFAULT_MODELS = {
	'coqui': 'tts_models/en/ek1/tacotron2',
	'gtts': 'en:co.uk',
}

DEFAULT_MODEL = "coqui:" + DEFAULT_MODELS['coqui']
# DEFAULT_MODEL = "gtts:" + DEFAULT_MODELS['gtts']


use_cuda = torch.cuda.is_available()


def get_synth_coqui(model=DEFAULT_MODELS["coqui"]):
	""" Get a Coqui TTS speak function for the given model """
	global use_cuda

	# download and load the TTS model
	model_manager = ModelManager()
	model_path, config_path, _model_item = model_manager.download_model(model)

	# create a TTS synthesizer
	synth = Synthesizer(
		tts_checkpoint=model_path,
		tts_config_path=config_path,
		vocoder_checkpoint=None,
		use_cuda=use_cuda,
	)

	def speak_fn(text, out, **_kwargs):
		audio = synth.tts(text)
		stem, ext = os.path.splitext(out)
		if ext != '.wav':
			out = stem + '.wav'
		synth.save_wav(audio, out)
		rate = synth.tts_config.audio['sample_rate']
		return out, audio, rate
	return speak_fn

def get_synth_gtts(model=DEFAULT_MODELS["gtts"]):
	""" Get a Google TTS speak function for the given model """
	lang, *rest = model.split(':', 1)
	tld = rest[0] if rest else None
	kwargs = { 'lang': lang }
	if tld:
		kwargs['tld'] = tld

	def speak_fn(text, out, **_kwargs):
		tts = gTTS(text=text, **kwargs)
		stem, ext = os.path.splitext(out)
		outmp3 = out
		if ext != '.mp3':
			outmp3 = stem + '.mp3'
		tts.save(outmp3)
		audio, rate = soundfile.read(outmp3)
		if ext == '.wav':
			soundfile.write(out, audio, rate, subtype='PCM_16')
		else:
			out = outmp3
		return out, audio, rate

	return speak_fn

engines = {
	'coqui': get_synth_coqui,
	'gtts': get_synth_gtts,
}

gtts_models = [
	{ "id": "en:com.au", "accent": "English (Australia)" },
	{ "id": "en:co.uk", "accent": "English (United Kingdom)" },
	{ "id": "en:us", "accent": "English (United States)" },
	{ "id": "en:ca", "accent": "English (Canada)" },
	{ "id": "en:co.in", "accent": "English (India)" },
	{ "id": "en:ie", "accent": "English (Ireland)" },
	{ "id": "en:co.za", "accent": "English (South Africa)" },
	{ "id": "fr:ca", "accent": "French (Canada)" },
	{ "id": "fr:fr", "accent": "French (France)" },
	{ "id": "zh-CN:any", "accent": "Mandarin (China Mainland)" },
	{ "id": "zh-TW:any", "accent": "Mandarin (Taiwan)" },
	{ "id": "pt:com.br", "accent": "Portuguese (Brazil)" },
	{ "id": "pt:pt", "accent": "Portuguese (Portugal)" },
	{ "id": "es:com.mx", "accent": "Spanish (Mexico)" },
	{ "id": "es:es", "accent": "Spanish (Spain)" },
	{ "id": "es:us", "accent": "Spanish (United States)" },
]

models = {}

def add_coqui_models():
	""" Add Coqui TTS models to the models dict """
	for mid in TTS.list_models():
		full_id = "coqui:" + mid
		lang = mid.split("/")[1]
		models[full_id] = {
			"engine": "coqui",
			"id": mid,
			"lang": lang,
		}

def add_gtts_models():
	""" Add Google TTS models to the models dict """
	for model in gtts_models:
		mid = model['id']
		full_id = "gtts:" + mid
		lang, tld = mid.split(':')
		models[full_id] = {
			"engine": "gtts",
			"id": mid,
			"lang": lang,
			"tld": tld,
			"accent": model['accent'],
		}

def download_all_coqui_models():
	""" Download all Coqui TTS models """
	# TODO this is not called anywhere, should be an option
	for model_name in TTS.list_models():
		_tts = TTS(model_name)

# TODO coqui speaker selection

def get_synth(model=DEFAULT_MODEL):
	""" Get a TTS speak function for the given model """
	model_type, *rest = model.split(':', 1)
	model = rest[0] if rest else DEFAULT_MODELS[model_type]
	try:
		engine = engines[model_type]
	except KeyError as e:
		raise ValueError(f'Unknown engine: {model_type}') from e
	return engine(model)

def speak_line(text, out=None, model=DEFAULT_MODEL, play=True, wait=True, synth=None, mute_capture_device=True, postproc=None):
	""" Speak a line of text """

	if not synth:
		synth = get_synth(model)

	logger.info("speak_line: text: %r", text)

	# create a temporary file to store the audio output
	out_is_temp = not out
	if out_is_temp:
		with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
			out = f.name
	try:
		# generate speech from the input text
		file, audio, rate = synth(text, out=out)

		rate_pp = rate
		if postproc:
			audio, rate_pp = postproc(file, audio, rate)

		# TODO process the audio with:
		# - soundstretch
		# - a vocoder?

		if mute_capture_device:
			sd.wait()
			amixer.sset("Capture", "nocap")
			logger.info("Mic off")

		# play the audio
		if play:
			sd.wait()
			sd.play(audio, samplerate=rate_pp)

		if mute_capture_device:
			sd.wait()
			amixer.sset("Capture", "cap")
			logger.info("Mic on")
	except ZeroDivisionError as e:
		logger.error("speak_line: ignoring ZeroDivisionError: %r", e)
		pass
	finally:
		# delete the temporary file
		if out_is_temp:
			os.remove(out)

	if play and wait:
		sd.wait()

def speak_lines(inp=stdin, out=None, model=DEFAULT_MODEL, play=True, wait=True, synth=None, mute_capture_device=True, postproc=None):
	""" Speak lines of text """
	if not synth:
		synth = get_synth(model)
	if out:
		stem, ext = os.path.splitext(out)

	for i, line in enumerate(inp):
		logger.info("speak_lines: line: %r", line)
		if out:
			out = f'{stem}_{i:06d}{ext}'
		speak_line(text=line, out=out, model=model, play=play, wait=wait, synth=synth, mute_capture_device=mute_capture_device, postproc=postproc)

	if play and wait:
		sd.wait()

def postproc_soundstretch(file, audio, rate, tempo=1, pitch=0):
	""" Post-process audio with soundstretch """

	# TODO use a python module instead of shelling out?
	# - soundstretch module is not based on libsoundtouch
	# - pysoundtouch is based on libsoundtouch but it's not in pypi, maybe not maintained?
	stem, ext = os.path.splitext(file)

	if ext != '.wav':
		file = stem + '.wav'
		soundfile.write(file, audio, rate, subtype='PCM_16')

	pp_out = stem + '_pp.wav'
	tempo_percent = round((tempo - 1) * 100)

	soundstretch(file, pp_out, f'-tempo={tempo_percent}', f'-pitch={pitch}', '-speech')

#	# move the processed audio to the original output file
#	os.rename(pp_out, out)

	# load the audio data from the wav file
	audio, rate = soundfile.read(pp_out)
	return audio, rate

def do_list_models():
	""" List available models """
	for k, v in models.items():
		_mid = v['id']
		lang = v['lang']
		tld = v.get('tld', '')
		accent = v.get('accent', '')
		print("\t".join([k, lang, tld, accent]))

@arg('--model', '-m')
def speak(inp=stdin, out=None, text=None, model=DEFAULT_MODEL, silence=0.1, play=True, wait=True, mute_capture_device=True, tempo=1.0, pitch=0.0, list_models=False):
	""" Speak text """
	add_gtts_models()
	add_coqui_models()
	if list_models:
		do_list_models()
		sys.exit(0)

	synth = get_synth(model)

	# TODO put various options into a dict or something so we can pass them around more easily


	# Play an optional short silence to wake up the speakers
	if silence > 0 and play:
		sd.wait()
		rate = 44100
		silence_samples = int(silence * rate)
		silent_audio = np.zeros(silence_samples)
		sd.play(silent_audio, samplerate=rate)

	postproc = None
	if tempo != 1 or pitch != 0:
		postproc = partial(postproc_soundstretch, tempo=tempo, pitch=pitch)

	if text:
		speak_line(text=text, out=out, model=model, play=play, wait=wait, synth=synth, mute_capture_device=mute_capture_device, postproc=postproc)
	else:
		speak_lines(inp=inp, out=out, model=model, play=play, wait=wait, synth=synth, mute_capture_device=mute_capture_device, postproc=postproc)

if __name__ == "__main__":
	dispatch_command(speak)
	sd.wait()


# TODO:

# - check out https://github.com/nateshmbhat/pyttsx3
# - try other Coqui TTS models and options
# - maybe use an OO approach
# - maybe port to Mac, Windows (mixer stuff)


# alt idea for controlling the Linux mixer:
#
# import alsaaudio
#
# def mute_capture_device(device_name='Capture'):
#     mixer = alsaaudio.Mixer(device_name)
#     mixer.setrec(0)
#
# def unmute_capture_device(device_name='Capture'):
#     mixer = alsaaudio.Mixer(device_name)
#     mixer.setrec(1)
#
# if __name__ == '__main__':
#     mute_capture_device()
#     time.sleep(5)  # Example: Sleep for 5 seconds while the microphone is muted
#     unmute_capture_device()

# Ideally, it would be better just to tell the mike app not to record during this time.
