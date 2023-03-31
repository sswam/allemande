#!/usr/bin/env python3

import sys
import os
import io
import argh
from threading import Thread, Event
from queue import Queue
from pydub import AudioSegment
import sounddevice
import speech_recognition as sr
import whisper
import torch
import numpy as np

def record_speech(run_event, q_audio, energy, pause, dynamic_energy, save):
	""" Record audio from microphone and put it in the queue """
	r = sr.Recognizer()
	r.energy_threshold = energy
	r.pause_threshold = pause
	r.dynamic_energy_threshold = dynamic_energy
	i = 0
	with sr.Microphone(sample_rate=16000) as source:
		while run_event.is_set():
#			drop = os.path.isfile("/tmp/drop-the-mic")
			audio = r.listen(source)
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

def speech_to_text(run_event, q_audio, q_text, model, lang):
	""" Transcribe from the audio queue to the text queue """
	while run_event.is_set():
		torch_audio = q_audio.get()
		if torch_audio is None:
			break
		result = model.transcribe(torch_audio, language=lang)
		print(result, file=sys.stderr)
		text = result.get("text").strip()
		segs = result["segments"]
		no_speech_prob = sum(x["no_speech_prob"] for x in segs) / (len(segs) or 1)
		if text and no_speech_prob < 0.5:
			q_text.put_nowait(text)
	q_text.put_nowait(None)

def mike(model="medium.en", lang="en", energy=1200, dynamic_energy=False, pause=0.8, save=None):
	""" Transcribe speech to text using microphone input """
	run_event = Event()
	run_event.set()

	model = whisper.load_model(model)
	try:
		q_audio = Queue()
		q_text = Queue()
		Thread(
			target=record_speech,
			args=(run_event, q_audio, energy, pause, dynamic_energy, save)
			).start()
		Thread(
			target=speech_to_text,
			args=(run_event, q_audio, q_text, model, lang)
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
		print("Interrupted!", file=sys.stderr)
		run_event.clear()
	finally:
		done = True

if __name__ == '__main__':
	argh.dispatch_command(mike)
