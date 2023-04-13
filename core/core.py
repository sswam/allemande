#!/usr/bin/env python3

""" electric barbarella v3 - core """

import os
import logging
from pathlib import Path
from functools import partial

import argh
import inotify.adapters
import torch
import yaml

os.environ["TRANSFORMERS_OFFLINE"] = "1"

import transformers

logger = logging.getLogger(__name__)

prog_dir = Path(__file__).parent


def load_model(model_path, device_map="auto"):
	""" Load a model """
	model_path = str(model_path)
	model = transformers.AutoModelForCausalLM.from_pretrained(
		model_path,
		device_map=device_map,
		torch_dtype=torch.float16,
		max_memory = { 0: "24GB" },
		low_cpu_mem_usage=True,
		cache_dir="cache"
	).cuda()
	model.tokenizer = transformers.AutoTokenizer.from_pretrained(model_path)
	return model


def gen(config, input_text, *_args, model=None, **_kwargs):
	""" Generate text from a model. """
	if model is None:
		return {
			"new.txt": "",
			"full.txt": input_text,
		}
	if config is None:
		config = {}

	if _args:
		logger.warning("gen: ignoring args: %s", _args)
	if _kwargs:
		logger.warning("gen: ignoring kwargs: %s", _kwargs)

	tokenizer = model.tokenizer
	if "pad_token_id" not in config:
		config["pad_token_id"] = tokenizer.eos_token_id

	full_text = ""
	in_tokens = model.tokenizer(input_text, return_tensors="pt").input_ids.cuda()
	n_in_tokens = in_tokens.shape[1]
	with torch.no_grad():
		gen_tokens = model.generate(
			in_tokens,
			**config,
		)
		if gen_tokens[0][-1] == tokenizer.eos_token_id:
			gen_tokens = gen_tokens[:,:-1]
		if torch.equal(in_tokens, gen_tokens[:,:n_in_tokens]):
			new_tokens = gen_tokens[:,n_in_tokens:]
			error = ""
		else:
			logger.warning("gen: gen_tokens does not start with in_tokens. Will append entire generation.")
			new_tokens = gen_tokens
			error = "<ERROR>"

		# tokens often begin with spaces, but we don't want to double up on spaces
		new_text = tokenizer.batch_decode(new_tokens, skip_special_tokens=True)[0]
		if new_text.startswith(" ") and input_text[-1:].isspace():
			new_text = new_text[1:]
		elif new_text[:2] == " \n":
			new_text = new_text[1:]
		elif new_text == " ":   # e.g. 2, 1
			new_text = ""
		new_text = error + new_text

		full_text = tokenizer.batch_decode(gen_tokens, skip_special_tokens=True)[0]

	response = {
		"new.txt": new_text,
		"full.txt": full_text,
	}

	return response


def load(ports, d, filename):
	""" Load a file from a directory or above """
	while True:
		f = d/filename
		if f.exists():
			return f.read_text()
		if d == ports:
			break
		p = d.parent
		if p == d:
			break
		d = p
	f = prog_dir/filename
	if f.exists():
		return f.read_text()
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
		request = load(ports, d, "request.txt")
		response = fn(config, request, *args, **kwargs)
		for k, v in response.items():
			(d/k).write_text(v)
		os.rename(d, port/"done"/req)
		logger.info("%s:%s - done", port, req)
	except Exception as e:
		logger.exception("%s:%s - error: %s", port, req, e)
		try:
			os.rename(d, port/"err"/req)
		except Exception as e2:
			logger.exception("%s:%s - error: %s", port, req, e2)
	finally:
		if log_handler:
			logger.removeHandler(log_handler)


def port_setup(port):
	""" Set up a port """
	for box in ("todo", "doing", "done", "err"):
		(port/box).mkdir(exist_ok=True)


def serve_requests(ports, fn):
	""" Serve requests from a directory of directories """
	logger.info("serving requests from %s", ports)
	i = inotify.adapters.Inotify()
	for port in Path(ports).iterdir():
		if not port.is_dir():
			continue
		port_setup(port)
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


def main(ports=".", model_path=None, verbose=False, debug=False):
	""" main function """
	setup_logging(verbose, debug)
	model = load_model(model_path) if model_path else None
	fn = partial(gen, model=model)
	serve_requests(ports, fn)


if __name__ == "__main__":
	argh.dispatch_command(main)
