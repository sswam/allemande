#!/usr/bin/env python3
""" Transcribe speech to text using microphone input and whisper """

import sys
import os
import io
from threading import Thread, Event
from queue import Queue
import logging
from contextlib import contextmanager
from functools import partial

import argh
from pydub import AudioSegment
import speech_recognition as sr
import whisper
import torch
import numpy as np

logger = logging.getLogger(__name__)


# TODO move to a library

@contextmanager
def redirect(fileno, target):
	""" Redirect a file descriptor temporarily """
	target_fd = os.open(target, os.O_WRONLY)
	saved_fd = os.dup(fileno)
	os.dup2(target_fd, fileno)
	try:
		yield
	finally:
		os.dup2(saved_fd, fileno)
		os.close(saved_fd)
		os.close(target_fd)

redirect_stderr_to_dev_null = partial(redirect, sys.stderr.fileno(), "/dev/null")

@contextmanager
def open_microphone_spamfree(*args, **kwargs):
	""" Open microphone without spamming stderr """
	with redirect_stderr_to_dev_null():
		with sr.Microphone(*args, **kwargs) as source:
			yield source

def record_speech(run_event, q_audio, energy, pause, dynamic_energy, save, device_index, adjust_for_ambient_noise=False, debug=False):
	""" Record audio from microphone and put it in the queue """
	r = sr.Recognizer()
	r.energy_threshold = energy
	r.pause_threshold = pause
	r.dynamic_energy_threshold = dynamic_energy
	i = 0

	open_microphone = sr.Microphone if debug else open_microphone_spamfree

	with open_microphone(sample_rate=16000, device_index=device_index) as source:
		while run_event.is_set():
#			drop = os.path.isfile("/tmp/drop-the-mic")
			if adjust_for_ambient_noise:
				logger.debug("Adjusting for ambient noise")
				r.adjust_for_ambient_noise(source)
			logger.debug("Listening")
			audio = r.listen(source)
			logger.debug("Got audio")
			if save:
				data = io.BytesIO(audio.get_wav_data())
				audio_clip = AudioSegment.from_file(data)
				filename = os.path.join(save, f"temp{i:06d}.flac")
				audio_clip.export(filename, format="flac")
#			if not drop and not os.path.isfile("/tmp/drop-the-mic"):
			np_audio = np.frombuffer(audio.get_raw_data(), np.int16)
			np_audio = np_audio.flatten().astype(np.float32) / 32768.0
			torch_audio = torch.from_numpy(np_audio)
			q_audio.put_nowait(torch_audio)
			i += 1
	q_audio.put_nowait(None)

def speech_to_text(run_event, q_audio, q_text, whisp, lang):
	""" Transcribe from the audio queue to the text queue """
	while run_event.is_set():
		torch_audio = q_audio.get()
		if torch_audio is None:
			break
		result = whisp.transcribe(torch_audio, language=lang)
		logger.info(result)
		text = result.get("text").strip()
		segs = result["segments"]
		no_speech_prob = sum(x["no_speech_prob"] for x in segs) / (len(segs) or 1)
		if text and no_speech_prob < 0.5:
			q_text.put_nowait(text)
	q_text.put_nowait(None)

def do_list_devices():
	""" List available microphone devices """
	for index, name in enumerate(sr.Microphone.list_microphone_names()):
		print(f'{index}\t{name}')

def setup_logging(verbose, debug):
	""" Setup logging """
	logger_fmt = "%(message)s"
	if debug:
		log_level = logging.DEBUG
		logger_fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
	elif verbose:
		log_level = logging.INFO
	else:
		log_level = logging.WARNING
	logging.basicConfig(level=log_level, format=logger_fmt)

@argh.arg("-d", "--debug", help="Enable debug logging")
def mike(model="medium.en", lang="en", energy=1200, dynamic_energy=False, pause=0.8, save=None, device_index=None, list_devices=False, adjust_for_ambient_noise=False, verbose=False, debug=False):
	""" Transcribe speech to text using microphone input """
	setup_logging(verbose, debug)

	if list_devices:
		do_list_devices()
		sys.exit(0)

#	if device_index == -1:
#		for index, name in enumerate(sr.Microphone.list_microphone_names()):
#			print(name)
#			if name == "sysdefault":
#				device_index = index
#				break

	run_event = Event()
	run_event.set()

	whisp = whisper.load_model(model)
	try:
		q_audio = Queue()
		q_text = Queue()
		Thread(
			target=record_speech,
			args=(run_event, q_audio, energy, pause, dynamic_energy, save, device_index, adjust_for_ambient_noise, debug)
			).start()
		Thread(
			target=speech_to_text,
			args=(run_event, q_audio, q_text, whisp, lang)
			).start()
		if save:
			os.makedirs(save, exist_ok=True)
		while True:
			text = q_text.get()
			if text is None:
				break
			print(text)
			sys.stdout.flush()
	except KeyboardInterrupt:
		logger.exception("Interrupted!")
	finally:
		run_event.clear()

if __name__ == '__main__':
	argh.dispatch_command(mike)
