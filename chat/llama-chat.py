#!/usr/bin/env python3

""" electric barbarella v4 - chat app """

import os
import time
import sys
import argparse
import logging
from math import inf
from pathlib import Path
import re
import readline
from types import SimpleNamespace

import yaml
import regex

import ucm
import ports
import conductor
import search
import chat
import llm
import tab

os.environ["TRANSFORMERS_OFFLINE"] = "1"
import transformers  # pylint: disable=wrong-import-position, wrong-import-order


logger = logging.getLogger(__name__)

server = "llm_llama"
default_port = ports.get_default_port(server)


# TODO can't select model from here now

models = {
	"point-alpaca-7B": {
		"abbrev": "alpaca",
		"description": "The Point Networks recreation of weights from Stanford Alpaca, derived from fine-tuning LLaMA on a synthetic dataset.",
		"cost": 0,
	},
}

first_model = next(iter(models.keys()))
default_model = os.environ.get("BB_MODEL", first_model)

default_file_extension = "bb"


AGENTS = {
}

AGENT_DEFAULT = "Ally"

AGENTS_LOCAL = {
	"Ally": {
		"model": "point-alpaca-7B",
	},
	"Callum": {
		"model": "point-alpaca-7B",
	},
}

AGENTS_REMOTE = {
	"GPT-4": {
		"name": "Emmy",
		"model": "gpt-4",
		"default_context": 5,
	},
	"GPT-3.5": {
		"name": "Leo",
		"model": "gpt-3.5-turbo",
		"default_context": 10,
	},
	"Claude": {
		"model": "claude-v1",
		"default_context": 20,
	},
	"Claude Instant": {
		"name": "Claudia",
		"model": "claude-instant-v1",
		"default_context": 40,
	},
	"Bard": {
		"name": "Jaskier",
		"model": "bard",
		"default_context": 1,
	},
}

AGENTS_PROGLANG = {
	"Doug": {
		"command": [],
	},
	"Guido": {
		"command": ["python"],
	},
	"Larry": {
		"command": ["perl"],
	},
	"Matz": {
		"command": ["ruby"],
	},
	"Lua": {
		"command": ["lua"],
	},
	"Ryan": {
		"command": ["node"],
	},
	"Dahl": {
		"command": ["deno"],
	},
	"Fabrice": {
		"command": ["tcc", "-run", "-"],
	},
	"Bellard": {
		"command": ["qjs"],
	},
	"Calc": {
		"command": ["calc"],
	},
}

TOKENIZERS = {}

REMOTE_AGENT_RETRIES = 3

ADULT = False

UNSAFE = False


def register_agents_local():
	""" Register LLM local agents """
	def make_agent(agent_base):
		agent = agent_base.copy()
		agent["fn"] = lambda *args, **kwargs: local_agent(agent, *args, **kwargs)
		agent["type"] = "local"
		if "name" not in agent:
			agent["name"] = agent_name
		return agent

	for agent_name in AGENTS_LOCAL:
		agent_base = AGENTS_LOCAL[agent_name]
		agent_lc = agent_name.lower()
		agent = AGENTS[agent_lc] = make_agent(agent_base)
		name_lc = agent["name"].lower()
		if name_lc != agent_lc:
			AGENTS[name_lc] = agent


def register_agents_search():
	""" Register search engines """
	def make_agent(agent_base):
		agent = agent_base.copy()
		agent["fn"] = lambda *args, **kwargs: run_search(agent, *args, **kwargs)
		agent["type"] = "tool"
		if "name" not in agent:
			agent["name"] = agent_name
		return agent

	for agent_name in search.engines:
		agent_lc = agent_name.lower()
		agent_base = { "name": agent_name }
		AGENTS[agent_lc] = make_agent(agent_base)
	if not ADULT:
		del AGENTS["pornhub"]
#	AGENTS["duck"] = AGENTS["duckduckgo"]


def register_agents_remote():
	""" Register LLM API agents """
	def make_agent(agent_base):
		agent = agent_base.copy()
		agent["fn"] = lambda *args, **kwargs: remote_agent(agent, *args, **kwargs)
		agent["type"] = "remote"
		if "name" not in agent:
			agent["name"] = agent_name
		return agent

	for agent_name in AGENTS_REMOTE:
		agent_base = AGENTS_REMOTE[agent_name]
		agent_lc = agent_name.lower()
		agent = AGENTS[agent_lc] = make_agent(agent_base)
		name_lc = agent["name"].lower()
		if name_lc != agent_lc:
			AGENTS[name_lc] = agent


def register_agents_proglang():
	""" Register programming language agents """
	def make_agent(agent_base):
		agent = agent_base.copy()
		agent["fn"] = lambda *args, **kwargs: safe_shell(agent, *args, **kwargs)
		agent["type"] = "tool"
		if "name" not in agent:
			agent["name"] = agent_name
		return agent

	for agent_name in AGENTS_PROGLANG:
		agent_base = AGENTS_PROGLANG[agent_name]
		agent_lc = agent_name.lower()
		agent = AGENTS[agent_lc] = make_agent(agent_base)
		name_lc = agent["name"].lower()
		if name_lc != agent_lc:
			AGENTS[name_lc] = agent


def register_agents():
	""" Register agents """
	register_agents_local()
	register_agents_search()
	register_agents_remote()
	if UNSAFE:
		register_agents_proglang()
	# TODO Moar!
	# - calculator: Calc
	# - translator: Poly


def load_tokenizer(model_path: Path):
	""" Load the Llama tokenizer """
	return transformers.LlamaTokenizer.from_pretrained(str(model_path))


def count_tokens_in_text(text, tokenizer):
	""" Count the number of tokens in a text. """
	return len(tokenizer(text).input_ids)


def leading_spaces(text):
	""" Return the number of leading spaces in a text. """
	return re.match(r"\s*", text).group(0)


def trim_response(response, args):
	""" Trim the response to the first message. """
	if args.raw:
		messages = response.split(args.delim)
		if messages and not re.search(r'\S', messages[0]):
			messages = messages[1:]
		response = messages[0] if messages else ""
	else:
#		human_invitation = args.user + ":"
#		response = response.split(human_invitation)[0]
		response = response.strip()
		response = re.sub(r"\n\w+:.*", "", response, flags=re.DOTALL)
		response = " " + response.strip()
	return response


def fix_layout(response, _args):
	""" Fix the layout and indentation of the response. """
	lines = response.split("\n")
	out = []
	in_table = False
	for i in range(0, len(lines)):
		# markdown tables must have a blank line before them ...
		line = lines[i]
		if not in_table and ("---" in line or re.search(r'\|.*\|', line)):
			if i > 0 and lines[i-1].strip():
				out.append("\t")
			in_table = True

		# ... and after them too, but we'll see what's needed later...
		# TODO detect end of table somehow

#		done = False

		if i == 0:
			out.append(line)
		else:
			line = "\t" + lines[i]
			out.append(line)

#			done = True

#		if i > 0 and ":" in lines[i]:
#			role = lines[i].split(":")[0]
#			if role and regex.match(conductor.regex_name, role):
#				line = re.sub(r':\s*', ':\t', lines[i])
#				out.append(line)
#				done = True
#
#		if not done:

	response = "\n".join(out) + "\n"

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


def get_fulltext(args, model_name, history, history_start, invitation, delim):
	""" Get the full text from the history, and cut to the right length. """
	tokenizer = TOKENIZERS[model_name]
	fulltext = delim.join(history[history_start:]) + invitation
	n_tokens = count_tokens_in_text(fulltext, tokenizer)
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
		n_tokens = count_tokens_in_text(fulltext, tokenizer)
#		dropped = True
		logger.info("dropped some history, history_start: %r, n_tokens: %r", history_start, n_tokens)
		if last:
			break
#	if dropped:
#		fulltext = delim.join(history[history_start:]) + invitation
	logger.info("fulltext: %r", fulltext)
	return fulltext, history_start


def client_request(port, input_text, config=None):
	""" Call the core server and get a response. """

	req = ports.prepare_request(port, config=config)

	req_input = req/"request.txt"
	req_input.write_text(input_text, encoding="utf-8")

	ports.send_request(port, req)

	resp, status = ports.wait_for_response(port, req)

	if status == "error":
		ports.response_error(resp)

	new_text = (resp/"new.txt").read_text(encoding="utf-8")
	generated_text = (resp/"full.txt").read_text(encoding="utf-8")

	ports.remove_response(port, resp)

	return new_text, generated_text


def chat_to_user(model, args, history, history_start=0):
	""" Chat with the model. """
	invitation = args.bot + ":" if args.bot else ""
	human_invitation = args.user + ":" if args.user else ""
	if args.emo and invitation:
		invitation += " "
	# if args.emo and human_invitation:
	if human_invitation:
		human_invitation += " "
	delim = args.delim

	if args.edit:
		msg = input_with_prefill("", human_invitation)
	else:
		msg = human_invitation + input(human_invitation)

#	logger.debug(f"{history=}")
#	logger.debug(f"{history_start=}")

	if msg:
		print("")

		if ":" in msg:
			args.user = msg.split(":")[0]

		history.append(msg)
		history_write(args.file, history[-1:], delim=delim, invitation=delim)

#	logger.debug(f"{history=}")

	if args.edit:
		invitation2 = input_with_prefill("", invitation)
	else:
		invitation2 = invitation

	if ":" in invitation2:
		args.bot = invitation2.split(":")[0]

	model_name = args.model
	fulltext, history_start = get_fulltext(args, model_name, history, history_start, delim+invitation2, delim)

	args.gen_config = load_config(args)

#	logger.debug(f"{history=}")
#	logger.debug(f"{history_start=}")
#	logger.debug("fulltext: %r", fulltext)
#	logger.debug("model: %r", model)
#	logger.debug("invitation: %r", invitation)
#	logger.debug("invitation2: %r", invitation2)
#	logger.debug("delim: %r", delim)

	response, _fulltext2 = client_request(args.port, fulltext, config=args.gen_config)

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
		history_start = chat_to_user(model, args, history, history_start=history_start)


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


def interactive(model, args):
	""" Interactive chat with the model. """
	history = history_read(args.file, args)

	if history and not history[-1]:
		history.pop()

	for message in history:
		print(message + args.delim, end="")

	# get latest user name and bot name from history
	# XXX this is unreliable!
	if args.raw:
		pass
	elif args.get_roles_from_history:
		args.user, args.bot = conductor.get_roles_from_history(history, args.user, args.bot)
	else:
		# use conductor
		# TODO !!!!!!!!
		pass

	try:
		chat_loop(model, args, history)
	except EOFError:
		pass


def run_search(agent, query, file, args, history, history_start):
	""" Run a search agent. """
	name = agent["name"]
	logger.debug("history: %r", history)
	history_messages = list(chat.lines_to_messages(history))
	logger.debug("history_messages: %r", history_messages)
	message = history_messages[-1]
	query = message["content"]
	logger.debug("query 1: %r", query)
	query = query.split("\n")[0]
	logger.debug("query 2: %r", query)
	rx = r'((ok|okay|hey|hi|ho|yo|hello|hola)\s)*\b'+re.escape(name)+r'\b'
	logger.debug("rx: %r", rx)
	query = re.sub(rx, '', query, flags=re.IGNORECASE)
	logger.debug("query 3: %r", query)
	query = re.sub(r'(show me|search( for|up)?|find( me)?|look( for| up)?|what(\'s| is) (the|a|an)?)\s+', '', query, re.IGNORECASE)
	logger.debug("query 4: %r", query)
	query = re.sub(r'#.*', '', query)
	logger.debug("query 5: %r", query)
	query = re.sub(r'[^\x00-~]', '', query)   # filter out emojis
	logger.debug("query 6: %r", query)
	query = re.sub(r'^\s*[,;.]|[,;.]\s*$', '', query).strip()
	logger.debug("query 7: %r", query)
	response = search.search(query, engine=name, markdown=True)
	response2 = f"{name}:\t{response}"
	response3 = fix_layout(response2, args)
	logger.debug("response3:\n%s", response3)
	return response3


def process_file(model, file, args, history_start=0, count=0, max_count=4):
	""" Process a file. """
	# TODO don't need model any longer
	logger.info("Processing %s", file)

	history = history_read(file, args)

	while history and history[-1] == "":
		history.pop()

	history_count = len(history)

	if args.ignore and history and history[-1].rstrip().endswith(args.ignore):
		return
	if args.require and history and history[-1].rstrip().endswith(args.require):
		return

	# get latest user name and bot name from history
	# XXX this is unreliable!
	if args.raw:
		pass
	elif args.get_roles_from_history:
		args.user, args.bot = conductor.get_roles_from_history(history, args.user, args.bot)
	else:
		default = AGENT_DEFAULT
		if history:
			history_messages = list(chat.lines_to_messages(history))

			who = conductor.who_should_respond(history_messages[-1], agents=AGENTS, history=history_messages, default=default)
			if who:
				args.bot = who[0]
			else:
				args.bot = None
			logger.warning("who should respond: %r", who)

	if args.bot and args.bot.lower() in AGENTS:
		logger.debug("history: %r", history)
		query1 = history[-1] if history else None
		logger.debug("query1: %r", query1)
		query = list(chat.lines_to_messages([query1]))[-1]["content"] if query1 else ""
		logger.debug("query: %r", query)
		agent = AGENTS[args.bot.lower()]
		response = run_agent(agent, query, file, args, history, history_start=history_start)
		history.append(response)
		history_write(file, history[-1:], delim=args.delim, invitation=args.delim)

	count += 1
	if count >= max_count:
		return

	if len(history) == history_count:
		return

	logger.debug("len(history), history_count: %r %r", len(history), history_count)
	logger.debug("history[-1]: %r", history[-1])
	logger.debug("running process_file again")

	process_file(model, file, args, history_start=history_start, count=count, max_count=max_count)


def run_agent(agent, query, file, args, history, history_start=0):
	""" Run an agent. """
	fn = agent["fn"]
	logger.debug("query: %r", query)
	return fn(query, file, args, history, history_start=history_start)


def local_agent(agent, query, file, args, history, history_start=0):
	""" Run a local agent. """
	print("local_agent: %r %r %r %r %r %r", query, agent, file, args, history, history_start)
	invitation = args.delim + agent["name"] + ":" if args.bot else ""
	human_invitation = args.delim + args.user + ":" if args.user else ""
	if args.emo and invitation:
		invitation += " "
	# if args.emo and human_invitation:
	if human_invitation:
		human_invitation += " "

	if not args.raw and history and history[-1] != "":
		history.append("")
		history_write(file, ['', ''], delim=args.delim)

	model_name = agent["model"]
	fulltext, history_start = get_fulltext(args, model_name, history, history_start, invitation, args.delim)

	args.gen_config = load_config(args)

	logger.debug("fulltext: %r", fulltext)
	logger.debug("config: %r", args.gen_config)
	logger.debug("port: %r", args.port)

	response, _fulltext2 = client_request(args.port, fulltext, config=args.gen_config)

	logger.debug("response: %r", response)

	logger.debug("response: %r", response)
	logger.debug("_fulltext2: %r", _fulltext2)

	if args.trim:
		response = trim_response(response, args)
	if not args.narrative:
		response = fix_layout(response, args)

	if invitation:
		tidy_response = invitation.strip() + "\t" + response.strip()
	else:
		tidy_response = response

	logger.debug("tidy response: %r", tidy_response)

	return tidy_response


def remote_agent(agent, query, file, args, history, history_start=0):
	# for now do just query, not the full chat
	if agent["default_context"] == 1:
		logger.debug("history: %r", history)
		logger.debug("query: %r", query)
		response = llm.query(query, out=None, model=agent["model"])
	else:
		query = query.rstrip() + "\n"

		# todo use a system message?

		context_proc = []

		n_context = agent["default_context"]
		context = history[-n_context:]
		context_messages = list(chat.lines_to_messages(context))

		remote_messages = []

		agent_names = list(AGENTS.keys())
		agents_lc = list(map(str.lower, agent_names))

		for msg in context_messages:
			logger.warning(msg)
			u = msg.get("user")
			u = u.lower() if u is not None else None
#			if u in agents_lc:
			if u == agent['name'].lower()
				role = "assistant"
			else:
				role = "user"
			msg2 = {
				"role": role,
				"content": msg["content"],
			}
			logger.warning("msg: %r", msg2)
			remote_messages.append(msg2)

		# TODO this is a bit dodgy and won't work with async
		opts = {
			"model": agent["model"],
			"indent": "\t",
		}
		llm.set_opts(opts)
		output_message = llm.retry(llm.llm_chat, REMOTE_AGENT_RETRIES, remote_messages)
		response = output_message["content"]

		# fix indentation for code
		if opts["indent"]:
			lines = response.splitlines()
			lines = tab.fix_indentation_list(lines, opts["indent"])
			response = "".join(lines)


	logger.debug("response 1: %r", response)
	if args.trim:
		response = trim_response(response, args)
	logger.debug("response 2: %r", response)
	if not args.narrative:
		response = fix_layout(response, args)
	logger.debug("response 3: %r", response)
	response = f"{agent['name']}:\t{response.strip()}"
	logger.debug("response 4: %r", response)
	return response


def safe_shell(agent, query, file, args, history, history_start=0, command=None):
	""" Run a shell agent. """
	name = agent["name"]
	logger.debug("history: %r", history)
	history_messages = list(chat.lines_to_messages(history))
	logger.debug("history_messages: %r", history_messages)
	message = history_messages[-1]
	query = message["content"]
	logger.debug("query 1: %r", query)
#	query = query.split("\n")[0]
#	logger.debug("query 2: %r", query)
	rx = r'((ok|okay|hey|hi|ho|yo|hello|hola)\s)*\b'+re.escape(name)+r'\b'
	logger.debug("rx: %r", rx)
	query = re.sub(rx, '', query, flags=re.IGNORECASE)
	logger.debug("query 3: %r", query)
#	query = re.sub(r'(show me|search( for|up)?|find( me)?|look( for| up)?|what(\'s| is) (the|a|an)?)\s+', '', query, re.IGNORECASE)
#	logger.debug("query 4: %r", query)
#	query = re.sub(r'#.*', '', query)
#	logger.debug("query 5: %r", query)
#	query = re.sub(r'[^\x00-~]', '', query)   # filter out emojis
#	logger.debug("query 6: %r", query)
	query = re.sub(r'^\s*[,;.]|\s*$', '', query).strip()
	logger.debug("query 7: %r", query)


	command = ['ssh', '-T', 'allemande-nobody@localhost'] + agent["command"]

	# echo the query to the subprocess
	import subprocess
	proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	proc.stdin.write(query.encode("utf-8"))
	proc.stdin.close()
	# read the output and stderr
	response = ""
	output = proc.stdout.read().decode("utf-8")
	errors = proc.stderr.read().decode("utf-8")
	status = proc.wait()
	if errors or status:
		response += "\n## status:\n" + str(status) + "\n\n"
		response += "## errors:\n```\n" + errors + "\n```\n\n"
		response += "## output:\n"
	response += "```\n" + output + "\n```\n"

	response2 = f"{name}:\t{response}"
	response3 = fix_layout(response2, args)
	logger.debug("response3:\n%s", response3)
	return response3


def find_files(folder, ext=None, maxdepth=inf):
	""" Find chat files under a directory. """
	if not os.path.isdir(folder):
		print("?", file=sys.stderr, end="", flush=True)
		return
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
	except (PermissionError, FileNotFoundError) as e:
		logger.warning("find_files: %r", e)


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

	now = time.time()

	# If a file is newly added, we want to respond if it's a newly created file, let's say newer than now - args.interval * 2
	# but we don't want to respond if it's an old file that was renamed or moved in.
	# This isn't 100% reliable, but it's better than nothing
	stats_null = type("stats_null", (object,), {"st_mtime": now - args.interval * 5, "st_size": 0})

	for file in files:
		# check if modified since last time
		stats1 = os.stat(file)
		try:
			stats0 = stats.get(file, stats_null)

			if first:
				stats[file] = stats1
				continue
			if stats1.st_mtime <= stats0.st_mtime:
				pass
			elif args.ignore_shrink and stats1.st_size < stats0.st_size:
				pass
			elif stats1.st_size > 0:
				process_file(model, file, args)
				stats1 = os.stat(file)
		except Exception as e:
			logger.exception("watch_step: %r", e)
			stats1 = os.stat(file)
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
	""" Try to get the user's name from $user in the environment, or fall back to $USER """
	user_id = os.environ["USER"]
	return os.environ.get("user", user_id).title()


def default_bot():
	""" Try to get the bot's name from the environment, or fall back to "Assistant" """
	return os.environ.get("bot", "Assistant").title()


def load_config(args):
	""" Load the generations config file. """
	config = {}
	if args.config:
		with open(args.config, encoding="utf-8") as f:
			settings = yaml.load(f, Loader=yaml.FullLoader)
		for k, v in settings.items():
			config[k] = v
	if args.max_tokens:
		config["max_new_tokens"] = args.max_tokens
	if not config:
		config = None
	return config


def prog_dir():
	""" Get the directory of the program. """
	return Path(sys.argv[0]).resolve().parent


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
	watch_group.add_argument("--depth", type=int, default=2, help="Maximum depth to search for and watch files")
	watch_group.add_argument("--interval", type=float, default=1.0, help="Interval between checks")
	watch_group.add_argument("--ignore-shrink", action="store_true", help="Don't react if the file shrinks")
	watch_group.add_argument("--ignore", default=None, help="Ignore if this string occurs at the end")
	watch_group.add_argument("--require", default=None, help="Ignore unless this string occurs at the end")

	names_group = parser.add_argument_group("User and bot names")
	names_group.add_argument("--user", "-u", default=default_user(), help="User name")
	names_group.add_argument("--bot", "-b", default=default_bot(), help="Bot name")
	names_group.add_argument("--raw", "-r", action="store_true", help="Don't auto-add names, free-form mode")
	names_group.add_argument("--get-roles-from-history", "-H", action="store_true", help="Get user and bot names from history file")

	format_group = parser.add_argument_group("Format options")
	format_group.add_argument("--delim", default="\n\n", help="Delimiter between messages")
	format_group.add_argument("--trim", action="store_true", default=True, help="Trim the bot's response (enabled by default)")
	format_group.add_argument("--no-trim", action="store_false", dest="trim", help="Don't trim the bot's response, i.e let it predict the user's speech")
	format_group.add_argument("--memory", "-x", type=int, default=512, help="Max number of tokens to keep in history, before we drop old messages")
	format_group.add_argument("--strip-final-newline", type=bool, default=True, help="Strip final newline from input, allows to continue lines")
	format_group.add_argument("--emo", type=bool, default=False, help="End the bot invitation with a space, which causes the bot to respond with an emoji first!")
	format_group.add_argument("--narrative", type=bool, default=False, help="Allow non-indented narrative text")

	model_group = parser.add_argument_group("Model options")
	model_group.add_argument("--port", "-p", default=default_port, help="Path to port directory")
	model_group.add_argument("--model", "-m", default="default", help="Model name or path")
	model_group.add_argument("--config", "-c", default=None, help="Model config file, in YAML format")
	model_group.add_argument("--list-models", "-l", action="store_true", help="List available models")
	model_group.add_argument("--bytes", "-8", action="store_true", help="Load in 8-bit mode, to save GPU memory")
	model_group.add_argument("--max-tokens", "-n", type=int, help="Maximum number of new tokens to generate")

	agent_group = parser.add_argument_group("Agent options")
	agent_group.add_argument("--agents", "-a", default=["all"], nargs="*", help="Enable listed or all agents")
	agent_group.add_argument("--no-agents", "-A", dest="agents", action="store_const", const=[], help="Disable all agents")
	agent_group.add_argument("--no-ai", action="store_true", help="Disable all AI agents")  # TODO
	agent_group.add_argument("--no-tools", action="store_true", help="Disable all software tool agents")  # TODO

#	model_group = parser.add_argument_group("Deluxe options")
#	model_group.add_argument("--retry", default=3, help="Number of times to retry if the bot fails to respond")
#	model_group.add_argument("--retry-temperature-boost", default=0.1, help="Temperature boost to apply when retrying")

	dev_group = parser.add_argument_group("Developer options")
	dev_group.add_argument("--no-model", "-M", action="store_false", dest="model", help="Don't load the model, for testing purposes")
	dev_group.add_argument("--dump-config", "-C", action="store_true", help="Dump the model config in YAML format, and exit")

	ucm.add_logging_options(parser)

	args = parser.parse_args()

	ucm.setup_logging(args)

	logger.debug("Options: %r", args)

	# prepend . to args.ext
	if not args.ext.startswith("."):
		args.ext = "." + args.ext

	if args.raw:
		args.user = ""
		args.bot = ""

	if isinstance(args.port, str):
		args.port = Path(args.port)

	# check agents are valid
	if args.agents == ["all"]:
		args.agents = AGENTS.keys()
	else:
		for a in set(args.agents) - set(AGENTS):
			logger.warning("Unknown agent: %s", a)
		args.agents = set(args.agents) & set(AGENTS)

	return args


def main():
	""" Main function. """
	register_agents()

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
	# create an empty object, so that we can add attributes to it
	model = SimpleNamespace()
	if args.model:
		abbrev_models = [k for k, v in models.items() if v.get("abbrev") == args.model]
		if len(abbrev_models) == 1:
			args.model = abbrev_models[0]

		models_dir = Path(os.environ["ALLEMANDE_MODELS"])/"llm"
		# model_dirs = prog_dir()/".."/"models"/"llm"
		model_path = Path(models_dir) / args.model
		model.tokenizer = load_tokenizer(model_path)
		TOKENIZERS[args.model] = model.tokenizer
	else:
		model.tokenizer = None

	# check for mutually exclusive options
	mode_options = [args.interactive, args.file, args.stream, args.watch]
	if [args.file, args.stream, args.watch].count(True) > 1:
		logger.error("Only one of --file, --stream, --watch can be specified")
		sys.exit(1)

	if args.interactive and any([args.watch, args.stream]):
		logger.error("Interactive mode is not compatible with --watch or --stream")
		sys.exit(1)

	# run in the requested mode
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
	try:
		main()
	except KeyboardInterrupt:
		logger.info("interrupted")
		sys.exit(0)


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
