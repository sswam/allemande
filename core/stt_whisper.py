#!/usr/bin/env python3-allemande

""" allemande - core whisper module """

import sys
import os
import logging
from pathlib import Path
from functools import partial
from types import SimpleNamespace

import argh
import inotify.adapters
import torch
import yaml
import whisper

os.environ["TRANSFORMERS_OFFLINE"] = "1"

import transformers

logger = logging.getLogger(__name__)

def prog_info():
	""" Get info about the program """
	prog = SimpleNamespace()
	prog.path = Path(__file__)
	prog.dir = prog.path.parent
	prog.filename = prog.path.name
	prog.name = prog.path.stem
	return prog

prog = prog_info()

ports_dir = Path(os.environ["ALLEMANDE_PORTS"])/prog.name

def gen(config, audio_file, *_args, model=None, **_kwargs):
	""" Transcribe text from an audio file. """

	language = config.get("language", "en")

#	np_audio = np.frombuffer(audio.get_raw_data(), np.int16)
#	np_audio = np_audio.flatten().astype(np.float32) / 32768.0
#	torch_audio = torch.from_numpy(np_audio)

	result = model.transcribe(str(audio_file), language=language)

	response = {
		"text.txt": result["text"],
		"result.yaml": yaml.safe_dump(result),
	}

	return response


def load(ports, d, filename):
	""" Load a file from a directory or above """
	while True:
		f = d/filename
		if f.exists():
			return f.read_text(encoding="utf-8")
		if d == ports:
			break
		p = d.parent
		if p == d:
			break
		d = p
	f = prog.dir/filename
	if f.exists():
		return f.read_text(encoding="utf-8")
	raise FileNotFoundError(f"load: could not find {filename} in {d} or above")


def process_request(ports, port, req, fn, *args, **kwargs):
	""" Process a request on a port """
	port = Path(port)
	logger.info("%s:%s - processing", port, req)
	log_handler = None
	try:
		d = port/"doing"/req
		os.rename(port/"todo"/req, d)
		log_handler = logging.FileHandler(d/"log.txt")
		logger.addHandler(log_handler)

		config = yaml.safe_load(load(ports, d, "config.yaml"))
		request = d/"request.aud"
		response = fn(config, request, *args, **kwargs)
		for k, v in response.items():
			(d/k).write_text(v, encoding="utf-8")
		os.rename(d, port/"done"/req)
		logger.info("%s:%s - done", port, req)
	except Exception as e:
		logger.exception("%s:%s - error: %s", port, req, e)
		try:
			os.rename(d, port/"error"/req)
		except Exception as e2:
			logger.exception("%s:%s - error: %s", port, req, e2)
		if 'CUDA error' in str(e):
			raise
	finally:
		if log_handler:
			logger.removeHandler(log_handler)


#def port_setup(port):
#	""" Set up a port """
#	for box in ("prep", "todo", "doing", "done", "error", "history"):
#		(port/box).mkdir(exist_ok=True)


def serve_requests(ports, fn):
	""" Serve requests from a directory of directories """
	logger.info("serving requests from %s", ports)
	i = inotify.adapters.Inotify()
	for port in Path(ports).iterdir():
		if not port.is_dir():
			continue
		# port_setup(port)
		todo = port/"todo"
		logger.info("watching %s", todo)
		i.add_watch(str(todo), mask=inotify.constants.IN_CREATE | inotify.constants.IN_MOVED_TO)
	for port in Path(ports).iterdir():
		if not port.is_dir():
			continue
		todo = port/"todo"
		for req in todo.iterdir():
			if not req.is_dir():
				continue
			process_request(ports, port, req.name, fn)
	for event in i.event_gen(yield_nones=False):
		(_, type_names, path, filename) = event
		logger.debug("PATH=[%r] FILENAME=[%r] EVENT_TYPES=%r", path, filename, type_names)
		port = Path(path).parent
		process_request(ports, port, filename, fn)


def setup_logging(verbose, debug):
	""" Setup logging """
	log_level = logging.WARNING
	fmt = "%(message)s"
	if debug:
		log_level = logging.DEBUG
		fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
	elif verbose:
		log_level = logging.INFO
	logging.basicConfig(level=log_level, format=fmt)


def main(ports=str(ports_dir), model="medium.en", verbose=False, debug=False):
	""" main function """
	setup_logging(verbose, debug)
	the_model = whisper.load_model(model) if model else None
	fn = partial(gen, model=the_model)
	serve_requests(ports, fn)


if __name__ == "__main__":
	try:
		argh.dispatch_command(main)
	except KeyboardInterrupt:
		logger.info("interrupted")
		sys.exit(1)
