#!/usr/bin/env python3

""" electric barbarella v2 """

import os
import time
import sys
import argparse
import logging
import re, regex
from math import inf
from pathlib import Path
from typing import Any, Dict
import readline

import torch
import yaml

os.environ["TRANSFORMERS_OFFLINE"] = "1"

import transformers

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
	"num_return_sequences": 1,
	"do_sample": True,
	"repetition_penalty": 1.1, # 1.0 means 'off'
	"penalty_alpha": 0.4, # default?  try also 0.6  # https://huggingface.co/blog/introducing-csearch
	"temperature": 0.5, # default: 1.0
	"top_k": 50, # default: 50
	"top_p": 1.0, # default: 1.0
	"early_stopping": True,
}

default_file_extension = "bb"

def load_model(model_path: Path, eight_bit=False, device_map="auto"):
	""" Load a model from cache or disk. """
	# global model_cache

	logger.info("model_path %r", model_path)
	logger.info("model_path.name %r", model_path.name)

	model_name = model_path.name

	model = model_cache.get(model_name, None)
	if model:
		logger.info("Using %r from cache...", model_name)
		return model

	logger.info("Loading %s ...", model_name)

	if device_map == "zero":
		device_map = "balanced_low_0"

	gpu_count = torch.cuda.device_count()
	logger.info('gpu_count %r', gpu_count)

	tokenizer = transformers.AutoTokenizer.from_pretrained(str(model_path))
	model = transformers.AutoModelForCausalLM.from_pretrained(
		str(model_path),
		device_map=device_map,
		#device_map="auto",
		torch_dtype=torch.float16,
		#max_memory = {0: "14GB", 1: "14GB", 2: "14GB", 3: "14GB",4: "14GB",5: "14GB",6: "14GB",7: "14GB"},
		max_memory = {0: "20GB"},
		load_in_8bit=eight_bit,
#		load_in_8bit_threshold=0.8,  # TODO needed to avoid crash with inf / double check this.
		low_cpu_mem_usage=True,
		cache_dir="cache"
	).cuda()

	model.tokenizer = tokenizer

	model_cache[model_name] = model

	return model

def count_tokens_in_text(text, tokenizer):
	""" Count the number of tokens in a text. """
	return len(tokenizer(text).input_ids)

def leading_spaces(text):
	""" Return the number of leading spaces in a text. """
	return re.match(r"\s*", text).group(0)

def gen(model, input_text, config=None):
	""" Generate text from a model. """
	tokenizer = model.tokenizer
	if config is None:
		config = config_default
	if model is None:
		return "", input_text
	if "pad_token_id" not in config:
		config["pad_token_id"] = tokenizer.eos_token_id
	generated_text = ""
	in_tokens = model.tokenizer(input_text, return_tensors="pt").input_ids.cuda()
	n_in_tokens = in_tokens.shape[1]
#	logger.info(f"gen: {in_tokens=}")
#	print("in_tokens")
#	for i in range(5):
#		print(i, in_tokens[0][i], repr(tokenizer.decode(in_tokens[0][i], skip_special_tokens=False)))
	with torch.no_grad():
		gen_tokens = model.generate(
			in_tokens,
			**config,
		)
		# gen_tokens should start with in_tokens, is that right?
#		print(in_tokens[:,:5])
#		print(gen_tokens[:,:5])

		if gen_tokens[0][-1] == tokenizer.eos_token_id:
#			print("gen: removing eos")
			gen_tokens = gen_tokens[:,:-1]

#		while gen_tokens[0][-1] in (1, 2):
#			print("gen: removing eos")
#			gen_tokens = gen_tokens[:,:-1]

		if torch.equal(in_tokens, gen_tokens[:,:n_in_tokens]):
			new_tokens = gen_tokens[:,n_in_tokens:]
			error = ""
		else:
			logger.warning("gen: gen_tokens does not start with in_tokens. Will append entire generation.")
			new_tokens = gen_tokens
			error = "<ERROR>"

		# TODO it's messy that it's all wrapped, can be good if we run multiple batches at once though
#		print(f"gen: {new_tokens.shape=} {new_tokens[0]=!r}")

		# tokens often begin with spaces, but we don't want to double up on spaces
		new_text = tokenizer.batch_decode(new_tokens, skip_special_tokens=True)[0]
		if new_text.startswith(' ') and input_text[-1:].isspace():
			new_text = new_text[1:]
		elif new_text[:2] == " \n":
			new_text = new_text[1:]
		elif new_text == " ":   # e.g. 2, 1
			new_text = ""

		new_text = error + new_text

		# TODO remove this?
		generated_text = tokenizer.batch_decode(gen_tokens, skip_special_tokens=True)[0]

	return new_text, generated_text

def trim_response(response, args):
	""" Trim the response to the first message. """
	if args.raw:
		messages = response.split(args.delim)
		if messages and not re.search(r'\S', messages[0]):
			messages = messages[1:]
		response = messages[0] if messages else ""
	else:
		human_invitation = args.user + ": "
		response = response.split(human_invitation)[0]
		response = response.strip()
	return response

def input_with_prefill(prompt, text):
	""" Input with a prefill. """
	def hook():
		readline.insert_text(text)
		readline.redisplay()
	readline.set_pre_input_hook(hook)
	result = input(prompt)
	readline.set_pre_input_hook()
	return result

def get_fulltext(args, model, history, history_start, invitation, delim):
	""" Get the full text from the history, and cut to the right length. """
	fulltext = delim.join(history[history_start:]) + invitation
	n_tokens = count_tokens_in_text(fulltext, model.tokenizer)
	logger.info("n_tokens is %r", n_tokens)
#	dropped = False
	# TODO use a better search method
	last = False
	while n_tokens > args.memory:
		if len(history) - history_start < 10:
			guess = 1
		else:
			logger.info("guessing how many tokens to drop...")
			logger.info("  args.memory: %r", args.memory)
			logger.info("  n_tokens: %r", n_tokens)
			logger.info("  len(history): %r", len(history))
			logger.info("  history_start: %r", history_start)
			guess = ((n_tokens - args.memory) / n_tokens) * (len(history) - history_start)
			guess =	int(guess * 0.7)
			logger.info("  guess: %r", guess)
			if guess <= 0:
				guess = 1
			if guess >= len(history) - history_start:
				guess = len(history) - history_start - 1
				last = 1
		history_start += guess
		fulltext = delim.join(history[history_start:]) + invitation
		n_tokens = count_tokens_in_text(fulltext, model.tokenizer)
#		dropped = True
		logger.info("dropped some history, history_start: %r, n_tokens: %r", history_start, n_tokens)
		if last:
			break
#	if dropped:
#		fulltext = delim.join(history[history_start:]) + invitation
	logger.info("fulltext: %r", fulltext)
	return fulltext, history_start

def chat(model, args, history, history_start=0):
	""" Chat with the model. """
	invitation = args.bot + ": " if args.bot else ""   # accidental emoji mode!
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
		history_write(args.file, history[-1:], delim=delim, invitation=delim)

	if args.edit:
		invitation2 = input_with_prefill("", invitation)
	else:
		invitation2 = invitation

	if ":" in invitation2:
		args.bot = invitation2.split(":")[0]

	fulltext, history_start = get_fulltext(args, model, history, history_start, invitation2, delim)

	args.gen_config = load_config(args)

	response, _fulltext2 = gen(model, fulltext, args.gen_config)

	if args.trim:
		response = trim_response(response, args)

	print(invitation2 + response)
	print("")

	history.append(invitation2 + response)
	history_write(args.file, history[-1:], delim=args.delim, invitation=delim)

	return history_start

def chat_loop(model, args, history, history_start=0):
	""" Chat with the model in a loop. """
	while True:
		history_start = chat(model, args, history, history_start=history_start)

def history_read(file, args):
	""" Read the history from a file. """
	text = ""
	if file and os.path.exists(file):
		with open(file, encoding="utf-8") as f:
			text = f.read()
	history = text.split(args.delim) if text else []

	# remove up to one blank line from the end, allows to continue same line or not
	# using a normal editor that always ends the file with a newline
#	if args.strip_final_newline and history and not history[-1]:
#		history.pop()
	return history

def history_write(file, history, delim="\n", mode="a", invitation=""):
	""" Write or append the history to a file. """
	if not file:
		return
	text = delim.join(history) + invitation
	with open(file, mode, encoding="utf-8") as f:
		f.write(text)

regex_name = r"^[\p{L}\p{M}']+([\p{Zs}\-][\p{L}\p{M}']+)*$"

def get_roles_from_history(history, args):
	""" Get the roles from the history. """
	def get_role(history, i=None, not_equal_to=None):
		if i is None:
			i = len(history) - 1
		while i > 0:
			if ":" in history[i]:
				role = history[i].split(":")[0]
				if role and regex.match(regex_name, role) and role != not_equal_to:
					return role, i - 1
			i -= 1
		return None, i

	hist_user, i = get_role(history, not_equal_to=args.bot)
	if hist_user:
		args.user = hist_user
	logger.info("user: %r, i: %r", args.user, i)
	hist_bot, i = get_role(history, i=i, not_equal_to=args.user)
	if hist_bot:
		args.bot = hist_bot
	logger.info("bot: %r, i: %r", args.bot, i)

	logger.info("user: %r", args.user)
	logger.info("bot: %r", args.bot)

def interactive(model, args):
	""" Interactive chat with the model. """
	history = history_read(args.file, args)

	if history and not history[-1]:
		history.pop()

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
	""" Process a file. """
	logger.info("Processing %s", file)

	history = history_read(file, args)

	print("history:", history)

	if args.ignore and history and history[-1].rstrip().endswith(args.ignore):
		return
	if args.require and history and history[-1].rstrip().endswith(args.require):
		return

	# get latest user name and bot name from history
	if not args.raw:
		get_roles_from_history(history, args)

	invitation = args.delim + args.bot + ": " if args.bot else ""
	human_invitation = args.delim + args.user + ": " if args.user else ""

	if not args.raw and history and history[-1] != "":
		history.append("")
		history_write(file, ['', ''], delim=args.delim)

	fulltext, history_start = get_fulltext(args, model, history, history_start, invitation, args.delim)

	logger.debug("fulltext: %r", fulltext)

	args.gen_config = load_config(args)

	response, _fulltext2 = gen(model, fulltext, args.gen_config)

#	logger.debug("response: ["+response+"]")
#	logger.debug("_fulltext2: ["+_fulltext2+"]")

	if args.trim:
		response = trim_response(response, args)

	history.append(invitation.lstrip() + response)
	history_write(file, history[-1:], delim=args.delim, invitation=human_invitation)

def find_files(folder, ext=None, maxdepth=inf):
	""" Find chat files under a directory. """
	try:
		for subdir in os.scandir(folder):
			if subdir.is_dir():
				if subdir.name.startswith("."):
					continue
				if maxdepth > 0:
					yield from find_files(subdir.path, ext, maxdepth - 1)
			elif subdir.is_file():
				if not ext or subdir.name.endswith(ext):
					yield subdir.path
	except PermissionError as e:
		logger.warning("find_files: %r", e)

stats_null = type("stats_null", (object,), {"st_mtime": -1, "st_size": 0})

def watch_step(model, args, stats):
	""" Watch a directory for changes, one step. """
	files = []
	dirs = args.watch.split(":")
	dirs = list(set(dirs))
	for folder in dirs:
		files += find_files(folder, ext=args.ext, maxdepth=args.depth)

	first = False

	if stats is None:
		stats = {}
		first = True

	for file in files:
		# check if modified since last time
		stats0 = stats.get(file, stats_null)
		stats1 = os.stat(file)

		if first:
			stats[file] = stats1
			continue
		if stats1.st_mtime <= stats0.st_mtime:
			pass
		elif args.ignore_shrink and stats1.st_size < stats0.st_size:
			pass
		elif stats1.st_size > 0:
			process_file(model, file, args)
		stats[file] = stats1

	return stats

def watch_loop(model, args):
	""" Watch a directory for changes, and process files as they change. """
	logger.info("Watching %r for files with extension %r and depth %r", args.watch, args.ext, args.depth)

	stats = None
	while True:
		stats = watch_step(model, args, stats)
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
	return "Assistant"

def load_config(args):
	""" Load the generations config file. """
	config = config_default.copy()
	if args.config:
		with open(args.config, encoding="utf-8") as f:
			settings = yaml.load(f, Loader=yaml.FullLoader)
		for k, v in settings.items():
			config[k] = v
	if args.max_tokens:
		config["max_new_tokens"] = args.max_tokens
	return config

def prog_dir():
	""" Get the directory of the program. """
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
	""" Get the command line options. """
	parser = argparse.ArgumentParser(description="Chat with a trained model, specifically Point Alpaca (fine-tuned LLaMA).", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	modes_group = parser.add_argument_group("Modes of operation")
	modes_group.add_argument("--interactive", "-i", action="store_true", help="Interactive mode, can use --file to load history")
	modes_group.add_argument("--file", "-f", default=None, help="Process and append to a file")
	modes_group.add_argument("--stream", "-s", action="store_true", help="Stream mode")
	modes_group.add_argument("--watch", "-w", default=None, help="Watch mode, watch for changes in directories, colon separated")

	interactive_group = parser.add_argument_group("Interactive mode options")
	interactive_group.add_argument("--edit", "-e", action="store_true", help="Edit the names during the session")

	watch_group = parser.add_argument_group("Watch mode options")
	watch_group.add_argument("--ext", default=default_file_extension, help="File extension to watch for")
	watch_group.add_argument("--depth", type=int, default=1, help="Maximum depth to search for and watch files")
	watch_group.add_argument("--interval", type=float, default=1.0, help="Interval between checks")
	watch_group.add_argument("--ignore-shrink", action="store_true", help="Don't react if the file shrinks")
	watch_group.add_argument("--ignore", default=None, help="Ignore if this string occurs at the end")
	watch_group.add_argument("--require", default=None, help="Ignore unless this string occurs at the end")

	names_group = parser.add_argument_group("User and bot names")
	names_group.add_argument("--user", "-u", default=default_user(), help="User name")
	names_group.add_argument("--bot", "-b", default=default_bot(), help="Bot name")
	names_group.add_argument("--raw", "-r", action="store_true", help="Don't auto-add names, free-form mode")

	format_group = parser.add_argument_group("Format options")
	format_group.add_argument("--delim", default="\n\n", help="Delimiter between messages")
	format_group.add_argument("--trim", action="store_true", default=True, help="Trim the bot's response (enabled by default)")
	format_group.add_argument("--no-trim", action="store_false", dest="trim", help="Don't trim the bot's response, i.e let it predict the user's speech")
	format_group.add_argument("--memory", "-x", type=int, default=512, help="Max number of tokens to keep in history, before we drop old messages")
	format_group.add_argument("--strip-final-newline", type=bool, default=True, help="Strip final newline from input, allows to continue lines")

	model_group = parser.add_argument_group("Model options")
	model_group.add_argument("--model", "-m", default="alpaca", help="Model name or path")
	model_group.add_argument("--config", "-c", default=None, help="Model config file, in YAML format")
	model_group.add_argument("--list-models", "-l", action="store_true", help="List available models")
	model_group.add_argument("--bytes", "-8", action="store_true", help="Load in 8-bit mode, to save GPU memory")
	model_group.add_argument("--max-tokens", "-n", type=int, help="Maximum number of new tokens to generate")

#	model_group = parser.add_argument_group("Deluxe options")
#	model_group.add_argument("--retry", default=3, help="Number of times to retry if the bot fails to respond")
#	model_group.add_argument("--retry-temperature-boost", default=0.1, help="Temperature boost to apply when retrying")

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
	""" Main function. """
	args = get_opts()

	if args.list_models:
		for model_name, model in models.items():
			print(f"{model_name} ({model['abbrev']}): {model['description']}")
		sys.exit(0)

	args.gen_config = load_config(args)

	logger.info("args.gen_config=%r", args.gen_config)

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
		# stream(model, args)

if __name__ == "__main__":
	main()


# NOTE XXX

# json, itertools, bisect, gc
# from accelerate import Accelerator
# import accelerate

# TODO use functools.cache or functools.lru_cache decorator?  https://docs.python.org/3/library/functools.html

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
