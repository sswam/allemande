#!/usr/bin/env python3

# electric barbarella v1

import os, json, itertools, bisect, gc

os.environ["TRANSFORMERS_OFFLINE"] = "1"

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
import transformers
import torch
from accelerate import Accelerator
import accelerate
import time
import sys
import argparse
import logging
import readline
import yaml
from math import inf
from pathlib import Path
from typing import Any, Dict

model_cache: Dict[str, Any]  = {}

logger = logging.getLogger(__name__)

models = {
	"point-alpaca-7B": {
		"abbrev": "alpaca",
		"description": "The Point Networks recreation of weights from Stanford Alpaca, derived from fine-tuning LLaMA on a synthetic dataset.",
		"cost": 0,
	},
}

first_model = next(iter(models.keys()))
default_model = os.environ.get("BB_MODEL", first_model)

config_default = {
	"max_new_tokens": 200,
	"use_cache": True,
	#	"pad_token_id": model.tokenizer.eos_token_id,
	"num_return_sequences": 1,
	"do_sample": True,
	"repetition_penalty": 1.1, # 1.0 means 'off'. unfortunately if we penalize it it will not output Sphynx:
#	"repetition_penalty": 1.2, # 1.0 means 'off'. unfortunately if we penalize it it will not output Sphynx:
	"penalty_alpha": 0.4, # default?  try also 0.6  # https://huggingface.co/blog/introducing-csearch
	"temperature": 0.5, # default: 1.0
	"top_k": 50, # default: 50
	"top_p": 1.0, # default: 1.0
	"early_stopping": True,
}

default_file_extension = "bb"

def load_model(model_path: Path, eight_bit=False, device_map="auto"):
	global model_cache

	logger.info("model_path %r", model_path)
	logger.info("model_path.name %r", model_path.name)

	model_name = model_path.name

	if model_name in model_cache:
		logger.info("Using "+model_name+" from cache...")
		return model_cache[model_name]

	logger.info("Loading "+model_name+"...")

	if device_map == "zero":
		device_map = "balanced_low_0"

	gpu_count = torch.cuda.device_count()
	logger.info('gpu_count %r', gpu_count)

	tokenizer = transformers.LlamaTokenizer.from_pretrained(str(model_path))
	model = transformers.LlamaForCausalLM.from_pretrained(
		str(model_path),
		device_map=device_map,
		#device_map="auto",
		torch_dtype=torch.float16,
		#max_memory = {0: "14GB", 1: "14GB", 2: "14GB", 3: "14GB",4: "14GB",5: "14GB",6: "14GB",7: "14GB"},
		max_memory = {0: "20GB"},
		load_in_8bit=eight_bit,
		# load_in_8bit_threshold=0.8,
		low_cpu_mem_usage=True,
		cache_dir="cache"
	).cuda()

	model.tokenizer = tokenizer

	model_cache[model_name] = model

	return model

def count_tokens_in_text(text, tokenizer):
	return len(tokenizer(text).input_ids)

def gen(model, fulltext, config=None):
	if config is None:
		config = config_default
	if model is None:
		return "", fulltext
	if "pad_token_id" not in config:
		config["pad_token_id"] = model.tokenizer.eos_token_id
	generated_text = ""
	gen_in = model.tokenizer(fulltext, return_tensors="pt").input_ids.cuda()
	in_tokens = gen_in.shape[1]
	logger.info(f"gen: {in_tokens=}")
	with torch.no_grad():
			generated_ids = model.generate(
				gen_in,
				**config,
			)
			generated_text = model.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0] # for some reason, batch_decode returns an array of one element?

			text_without_prompt = generated_text[len(fulltext):]  # this fails when we send too many tokens?

	return text_without_prompt, generated_text

def trim_response(response, args):
	if args.raw:
		response = response.split(args.delim)[0]
	else:
		human_invitation = args.user + ": "
		response = response.split(human_invitation)[0]
	response = response.strip()
	return response

def input_with_prefill(prompt, text):
	def hook():
		readline.insert_text(text)
		readline.redisplay()
	readline.set_pre_input_hook(hook)
	result = input(prompt)
	readline.set_pre_input_hook()
	return result

def get_fulltext_old(args, model, history, history_start, invitation2, delim):
	fulltext = delim.join(history[history_start:]) + delim + invitation2
	n_tokens = count_tokens_in_text(fulltext, model.tokenizer)
	logger.info(f"n_tokens is {n_tokens}")
	dropped = False
	while n_tokens > args.memory:
		d_tokens = count_tokens_in_text(history[history_start] + delim , model.tokenizer)
		history_start += 1
		n_tokens -= d_tokens
		dropped = True
		logger.info(f"dropped some history, history_start: {history_start}, n_tokens: {n_tokens}, d_tokens: {d_tokens}")
	if dropped:
		fulltext = delim.join(history[history_start:]) + delim + invitation2
	logger.info("fulltext: "+fulltext)
	return fulltext, history_start

def get_fulltext(args, model, history, history_start, invitation2, delim):
	fulltext = delim.join(history[history_start:]) + delim + invitation2
	n_tokens = count_tokens_in_text(fulltext, model.tokenizer)
	logger.info(f"n_tokens is {n_tokens}")
	dropped = False
	# TODO use a better search method
	last = False
	while n_tokens > args.memory:
		if len(history) - history_start < 10:
			guess = 1
		else:
			logger.info(f"guessing how many tokens to drop...")
			logger.info(f"  args.memory: {args.memory}")
			logger.info(f"  n_tokens: {n_tokens}")
			logger.info(f"  len(history): {len(history)}")
			logger.info(f"  history_start: {history_start}")
			guess = ((n_tokens - args.memory) / n_tokens) * (len(history) - history_start)
			guess =	int(guess * 0.7)
			logger.info(f"  guess: {guess}")
			if guess <= 0:
				guess = 1
			if guess >= len(history) - history_start:
				guess = len(history) - history_start - 1
				last = 1
		history_start += guess
		fulltext = delim.join(history[history_start:]) + delim + invitation2
		n_tokens = count_tokens_in_text(fulltext, model.tokenizer)
		dropped = True
		logger.info(f"dropped some history, history_start: {history_start}, n_tokens: {n_tokens}")
		if last:
			break
	if dropped:
		fulltext = delim.join(history[history_start:]) + delim + invitation2
	logger.info("fulltext: "+fulltext)
	return fulltext, history_start

def chat(model, args, history, history_start=0):
	invitation = args.bot + ": " if args.bot else ""
	human_invitation = args.user + ": " if args.user else ""
	delim = args.delim

	if args.edit:
		msg = input_with_prefill("", human_invitation)
	else:
		msg = human_invitation + input(human_invitation)

	if msg:
		print("")

		if ":" in msg:
			args.user = msg.split(":")[0]

		history.append(msg)
		history_write(args.file, history[-1:], delim=delim)

	if args.edit:
		invitation2 = input_with_prefill("", invitation)
	else:
		invitation2 = invitation

	if ":" in invitation2:
		args.bot = invitation2.split(":")[0]

	fulltext, history_start = get_fulltext(args, model, history, history_start, invitation2, delim)

	args.gen_config = load_config(args.config)

	response, _fulltext2 = gen(model, fulltext, args.gen_config)

	if args.trim:
		response = trim_response(response, args)

	print(invitation2 + response)
	print("")

	history.append(invitation2 + response)
	history_write(args.file, history[-1:], delim=args.delim)

	return history_start

def chat_loop(model, args, history, history_start=0):
	while True:
		history_start = chat(model, args, history, history_start=history_start)

def history_read(file, delim="\n"):
	text = ""
	if file and os.path.exists(file):
		with open(file) as f:
			text = f.read()
	history = text.rstrip().split(delim) if text else []
	while history and not history[-1]:
		history.pop()
	return history

def history_write(file, history, delim="\n", mode="a", invitation=""):
	if not file:
		return
	text = delim.join(history) + delim + invitation
	with open(file, mode) as f:
		f.write(text)

def get_roles_from_history(history, args):
	def get_role(history, i=None, not_equal_to=None):
		if i is None:
			i = len(history) - 1
		while i > 0:
			if ":" in history[i]:
				role = history[i].split(":")[0]
				if role and role != not_equal_to:
					return role, i - 1
			i -= 1
		return None, i

	hist_user, i = get_role(history, not_equal_to=args.bot)
	if hist_user:
		args.user = hist_user
	logger.info(f"user: {args.user}, i: {i}")
	hist_bot, i = get_role(history, i=i, not_equal_to=args.user)
	if hist_bot:
		args.bot = hist_bot
	logger.info(f"bot: {args.bot}, i: {i}")

	logger.info("user: "+args.user)
	logger.info("bot: "+args.bot)

def interactive(model, args):
	history = history_read(args.file, delim=args.delim)

	for message in history:
		print(message + args.delim, end="")

	# get latest user name and bot name from history
	if not args.raw:
		get_roles_from_history(history, args)

	try:
		chat_loop(model, args, history)
	except EOFError:
		pass

def process_file(model, file, args, history_start=0):
	logger.info("Processing %s", file)

	history = history_read(file, delim=args.delim)

	# get latest user name and bot name from history
	if not args.raw:
		get_roles_from_history(history, args)

	invitation = args.bot + ": " if args.bot else ""
	human_invitation = args.user + ": " if args.user else ""

	fulltext, history_start = get_fulltext(args, model, history, history_start, invitation, args.delim)

	logger.debug("fulltext: "+fulltext)

	args.gen_config = load_config(args.config)

	response, _fulltext2 = gen(model, fulltext, args.gen_config)

	if args.trim:
		response = trim_response(response, args)

	history.append(invitation + response)
	history_write(file, history[-1:], delim=args.delim, invitation=human_invitation)

def find_files(dir, ext=None, maxdepth=inf):
	try:
		for subdir in os.scandir(dir):
			if subdir.is_dir():
				if subdir.name.startswith("."):
					continue
				if maxdepth > 0:
					yield from find_files(subdir.path, ext, maxdepth - 1)
			elif subdir.is_file():
				if not ext or subdir.name.endswith(ext):
					yield subdir.path
	except PermissionError as e:
		logger.warning("find_files: "+str(e))
		pass

def watch_step(model, args, mtimes):
	files = find_files(args.watch, ext=args.ext, maxdepth=args.depth)

	first = False

	if mtimes is None:
		mtimes = {}
		first = True

	for file in files:
		# check if modified since last time
		mtime = os.path.getmtime(file)
		old_mtime = mtimes.get(file, -1)
		if first:
			mtimes[file] = mtime
			continue
		if mtime <= mtimes.get(file, -1):
			continue
		process_file(model, file, args)
		mtimes[file] = os.path.getmtime(file)
	
	return mtimes

def watch_loop(model, args):
	logger.info(f"Watching {args.watch} for files with extension {args.ext} and depth {args.depth}")

	mtimes = None
	while True:
		mtimes = watch_step(model, args, mtimes)
		time.sleep(args.interval)
		print(".", file=sys.stderr, end="", flush=True)

#def stream(model, args):
#	# TODO
#	pass

def default_user():
	""" Try to get the user's name from the environment, or fall back to "Human" """
	return os.environ.get("USER", "Human").title()

def default_bot():
	""" Try to get the bot's name from the script name, or fall back to "Assistant" """
	if os.path.islink(sys.argv[0]):
		realpath = os.path.realpath(sys.argv[0])
		basename = os.path.basename(realpath)
		return os.path.splitext(basename)[0].title()
	else:
		return "Assistant"

def load_config(config_file):
	config = config_default.copy()
	if not config_file:
		return config
	with open(config_file) as f:
		settings = yaml.load(f, Loader=yaml.FullLoader)
	for k, v in settings.items():
		config[k] = v
	return config

def prog_dir():
	return Path(sys.argv[0]).resolve().parent

def setup_logging(args):
	""" Set up logging. """

	# get basename of program in upper case
	prog_name_uc = os.path.basename(sys.argv[0]).upper()

	log_file = args.log or os.environ.get(f'{prog_name_uc}_LOG')
	fmt = "%(message)s"
	if args.log_level == logging.DEBUG:
		fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"

	# if a log_file was specified, use it
	log_file = log_file or os.environ.get('BB_LOG_FILE')
	logging.basicConfig(level=args.log_level, format=fmt, filename=log_file)

def add_logging_options(parser):
	""" Add logging options to an argument parser. """
	logging_group = parser.add_argument_group('Logging options')
	logging_group.set_defaults(log_level=logging.WARNING)
	logging_group.add_argument('-d', '--debug', dest='log_level', action='store_const', const=logging.DEBUG, help="Show debug messages")
	logging_group.add_argument('-v', '--verbose', dest='log_level', action='store_const', const=logging.INFO, help="Show verbose messages")
	logging_group.add_argument('-q', '--quiet', dest='log_level', action='store_const', const=logging.ERROR, help="Show only errors")
	logging_group.add_argument('-Q', '--silent', dest='log_level', action='store_const', const=logging.CRITICAL, help="Show nothing")
	logging_group.add_argument('--log', default=None, help="log file")

def get_opts():
	parser = argparse.ArgumentParser(description="Chat with a trained model, specifically Point Alpaca (fine-tuned LLaMA).", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	modes_group = parser.add_argument_group("Modes of operation")
	modes_group.add_argument("--interactive", "-i", action="store_true", help="Interactive mode, can use --file to load history")
	modes_group.add_argument("--file", "-f", default=None, help="Process and append to a file")
	modes_group.add_argument("--stream", "-s", action="store_true", help="Stream mode")
	modes_group.add_argument("--watch", "-w", default=None, help="Watch mode, watch for changes in a directory")

	interactive_group = parser.add_argument_group("Interactive mode options")
	interactive_group.add_argument("--edit", "-e", action="store_true", help="Edit the names during the session")

	watch_group = parser.add_argument_group("Watch mode options")
	watch_group.add_argument("--ext", default=default_file_extension, help="File extension to watch for")
	watch_group.add_argument("--depth", type=int, default=1, help="Maximum depth to search for and watch files")
	watch_group.add_argument("--interval", type=float, default=1.0, help="Interval between checks")

	names_group = parser.add_argument_group("User and bot names")
	names_group.add_argument("--user", "-u", default=default_user(), help="User name")
	names_group.add_argument("--bot", "-b", default=default_bot(), help="Bot name")
	names_group.add_argument("--raw", "-r", action="store_true", help="Don't auto-add names, free-form mode")

	format_group = parser.add_argument_group("Format options")
	format_group.add_argument("--delim", default="\n\n", help="Delimiter between messages")
	format_group.add_argument("--trim", action="store_true", default=True, help="Trim the bot's response (enabled by default)")
	format_group.add_argument("--no-trim", action="store_false", dest="trim", help="Don't trim the bot's response, i.e let it predict the user's speech")
	format_group.add_argument("--memory", "-x", type=int, default=512, help="Max number of tokens to keep in history, before we drop old messages")

	model_group = parser.add_argument_group("Model options")
	model_group.add_argument("--model", "-m", default="alpaca", help="Model name or path")
	model_group.add_argument("--config", "-c", default=None, help="Model config file, in YAML format")
	model_group.add_argument("--list-models", "-l", action="store_true", help="List available models")
	model_group.add_argument("--bytes", "-8", action="store_true", help="Load in 8-bit mode, to save GPU memory")

	model_group = parser.add_argument_group("Deluxe options")
	model_group.add_argument("--retry", default=3, help="Number of times to retry if the bot fails to respond")
	model_group.add_argument("--retry-temperature-boost", default=0.1, help="Temperature boost to apply when retrying")

	dev_group = parser.add_argument_group("Developer options")
	dev_group.add_argument("--no-model", "-M", action="store_false", dest="model", help="Don't load the model, for testing purposes")
	dev_group.add_argument("--dump-config", "-C", action="store_true", help="Dump the model config in YAML format, and exit")

	add_logging_options(parser)

	args = parser.parse_args()

	setup_logging(args)

	logger.debug("Options: %r", args)

	# prepend . to args.ext
	if not args.ext.startswith("."):
		args.ext = "." + args.ext

	if args.raw:
		args.user = ""
		args.bot = ""

	return args

def main():
	args = get_opts()

	if args.list_models:
		for model_name in models:
			model = models[model_name]
			print(f"{model_name} ({model['abbrev']}): {model['description']}")
		sys.exit(0)

	args.gen_config = load_config(args.config)

	logger.info(f"{args.gen_config=}")

	if args.dump_config:
		print(yaml.dump(args.gen_config, default_flow_style=False, sort_keys=False))
		sys.exit(0)

	# load model (or don't, for testing purposes)
	if args.model:
		abbrev_models = [k for k, v in models.items() if v.get("abbrev") == args.model]
		if len(abbrev_models) == 1:
			args.model = abbrev_models[0]

		model_dir = prog_dir()/"models"
		model_path = Path(args.model)
		if not model_path.is_absolute():
			model_path = Path(model_dir) / model_path
		model = load_model(model_path, args.bytes)
	else:
		model = None

	# check for mutually exclusive options
	mode_options = [args.interactive, args.file, args.stream, args.watch]
	if [args.file, args.stream, args.watch].count(True) > 1:
		logger.error("Only one of --file, --stream, --watch can be specified")
		sys.exit(1)

	if args.interactive and any([args.watch, args.stream]):
		logger.error("Interactive mode is not compatible with --watch or --stream")
		sys.exit(1)

	# run the model in the requested mode
	if args.interactive or not any(mode_options):
		logger.info("Interactive mode")
		interactive(model, args)
	elif args.watch:
		logger.info("Watch mode")
		watch_loop(model, args)
	elif args.file:
		logger.info("File mode")
		process_file(model, args.file, args)
	elif args.stream:
		logger.error("Stream mode, not implemented yet")
		stream(model, args)

if __name__ == "__main__":
	main()


# NOTE XXX

# Ideally I would prefer a generic solution not all this hackery and complexity...
# A better approach might be to implement the simplest possible generic client-server forking singleton thing for the command line, to accelerate loading.
# Let's get this working here and now, then switch to that method for modularity.

# BUGS

# - raw mode still adds spacing, if anything it should strip the spacing.

# TODO

# ✓ pass model as a parameter
# ✓ specify invitations, i.e. human and assistant names
# ✓ readline for interactive, and allow to edit prompts
# ✓ allow to specify a file to read history from, and append to it
# ✓ non-interactive mode on a single file
#   ✓ not very useful but a foundation for watching files
# ✓ watch multiple files
# ✓ use previous names in interactive edit mode
# ✓ use previous names in process_file mode
# ✓ raw mode, don't insert invitations
# ✓ option to forget old history so can continue chatting
# ✓ 8-bit quantization option
#   - not working?
# ✓ allow dynamic config, reload each time we run the model

# - options to insert a system message at the start of the chat, or just before the user's message
# - could do a virtual or real group chat I suppose
# - object oriented
# - use plugins
# - allow to go back in interactive
# - allow to edit history
# - allow to remove first lines when run out of space
# - try using it in a notebook
# - try running with aliases instead of standard invitations
# - system prompt or whatever
# - reload python code without quitting
# - or run a pure model service that I don't need to restart
# - what sort of API?
# - try it with llama.cpp
# - run it on my webservers?
