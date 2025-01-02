#!/usr/bin/env python3-allemande

""" Ally Chat / Electric Barbarella v7 - multi-user LLM chat app """

import os
import time
import sys
import argparse
import logging
from math import inf
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace
import asyncio

import shlex
import readline
from watchfiles import Change
import yaml
import regex

import ucm
import conductor
import search
import tab
import chat
import llm
from ally import portals
import atail

os.environ["TRANSFORMERS_OFFLINE"] = "1"
import transformers  # pylint: disable=wrong-import-position, wrong-import-order


logger = logging.getLogger(__name__)

portal_by_service = {}

LOCAL_AGENT_TIMEOUT=90


# TODO can't select model from here now

models = {
	"default": {
		"abbrev": "llama3",
		"description": "Meta-Llama-3.1-8B-Instruct",
		"cost": 0,
	},
}

first_model = next(iter(models.keys()))
default_model = os.environ.get("BB_MODEL", first_model)

DEFAULT_FILE_EXTENSION = "bb"


AGENTS = {
}

AGENT_DEFAULT = os.environ.get("bot", "Ally")

AGENTS_LOCAL = {
	"Ally": {
		"service": "llm_llama",
		"model": "default",
#		"system_top": "Your name is Ally.",
		"system_bottom": "You are Ally. Ally is creative and talkative. You always say something interesting.",
		"system_bottom_pos": 1,
	},
	"Barbie": {
		"service": "llm_llama",
		"model": "default",
#		"system_top": "Your name is Barbie. You're not a doll! You're fun and clever.",
		"system_bottom": "You are Barbie. Barbie is playful and talkative. You always say something interesting.",
		"system_bottom_pos": 1,
	},
	"Callam": {
		"service": "llm_llama",
		"model": "default",
#		"system_top": "Your name is Callam.",
		"system_bottom": "Please reply as Callam, with medium hostility, and speak like a pirate. You are talkative, and don't repeat yourself. You always say something interesting, not just a few words.",
		"system_bottom_pos": 4,
	},
	"Illy": {
		"model": "juggernautXL_juggXIByRundiffusion",
		"service": "image_a1111",
		"default_context": 1,
		"clean_prompt": True,
		"config": {
			"steps": 15,
			"cfg_scale": 4.5,
			"pag": True,
			"adetailer": ["face_yolov8n.pt"],
			"ad_mask_k_largest": 10,
		}
	},
	"Yoni": {
		"model": "erosUltima_hybrid_Pony",
		"service": "image_a1111",
		"default_context": 1,
		"clean_prompt": True,
		"config": {
			"steps": 15,
			"cfg_scale": 7,
			"pony": 1.0,
			"pag": True,
			"adetailer": ["face_yolov8n.pt", "female-breast-v4.7.pt", "pussyV2.pt"],
			"ad_mask_k_largest": 10,
		}
	},
	"Poni": {
		"model": "autismmixSDXL_autismmixConfetti",
		"service": "image_a1111",
		"default_context": 1,
		"clean_prompt": True,
		"config": {
			"steps": 15,
			"cfg_scale": 7,
			"pony": 1.0,
			"pag": True,
			"adetailer": ["face_yolov8n.pt", "female-breast-v4.7.pt", "pussyV2.pt"],
			"ad_mask_k_largest": 10,
		}
	},
}

AGENTS_REMOTE = {
	"GPT-4": {
		"name": "Emmy",
		"model": "gpt-4",
		"default_context": 20,
		"system_bottom": "[Please reply as Emmy, without any `Emmy: ` prefix.]",
	},
	"GPT-4o-mini": {
		"name": "Dav",
		"model": "gpt-4o-mini",
		"default_context": 100,
		"system_bottom": "[Please reply as Dav, without any `Dav: ` prefix.]",
	},
	"Claude": {
		"name": "Claude",
#		"map": {
#			"Claud": "Claude",
#		},
		"model": "claude",
		"default_context": 20,
		"system_bottom": "[Please reply as Claude, without any `Claude: ` prefix.]",
	},
	"Claude Instant": {
		"name": "Clia",
		"map": {
			"Clia": "Claude",
		},
		"model": "claude-haiku",
		"default_context": 100,
		"system_bottom": "[Please reply as Claude, without any `Claude: ` prefix.]",
	},
# 	"Bard": {
# 		"name": "Jaski",
# #		"map": {
# #			"Jaski": "Bard",
# #		},
# 		"model": "bard",
# 		"default_context": 1,
# 	},
}

AGENTS_PROGRAMMING = {
	"Dogu": {
		"command": ["bash"],
	},
	"Gid": {
		"command": ["python"],
	},
	"Lary": {
		"command": ["perl"],
	},
	"Matz": {
		"command": ["ruby"],
	},
	"Luah": {
		"command": ["lua"],
	},
	"Jyan": {
		"command": ["node"],
	},
	"Jahl": {
		"command": ["deno", "run", "--quiet", "--allow-all", "-"],
	},
	"Faby": {
		"command": ["tcc", "-run", "-"],
	},
	"Qell": {
		"command": ["sh", "-c", 't=`mktemp`; cat >$t; qjs --std --bignum --qjscalc $t; rm $t'],
	},
	"Bilda": {
		"command": ["make", "-f", "/dev/stdin"],
	},
	"Palc": {
		"command": ["calc"],
	},
}

# TODO but awk is a filter, needs input in addition to the program...
# TODO split input vs program code in the query
#	"Awky": {
#		"command": ["awk"],
#	},

TOKENIZERS = {}

REMOTE_AGENT_RETRIES = 3

MAX_REPLIES = 1

ADULT = True

UNSAFE = False


def get_service_portal(service: str) -> portals.PortalClient:
	""" Get a portal for a service. """
	portal = portal_by_service.get(service)
	if not portal:
		portal_path = portals.get_default_portal_name(service)
		portal = portal_by_service[service] = portals.PortalClient(portal_path)
	return portal


def register_agents(agent_type, agents_dict, async_func):
	""" Register agents """
	async def agent_wrapper(agent, *args, **kwargs):
		return await async_func(agent, *args, **kwargs)

	def make_agent(agent_base, agent_name):
		agent = agent_base.copy()
		agent["fn"] = lambda *args, **kwargs: agent_wrapper(agent, *args, **kwargs)
		agent["type"] = agent_type
		if "name" not in agent:
			agent["name"] = agent_name
		return agent

	for agent_name, agent_base in agents_dict.items():
		agent_lc = agent_name.lower()
		agent = AGENTS[agent_lc] = make_agent(agent_base, agent_name)
		name_lc = agent["name"].lower()
		if name_lc != agent_lc:
			AGENTS[name_lc] = agent


def setup_agent_maps():
	""" Setup maps for all agents """
	for _agent_name, agent in AGENTS.items():
		setup_maps_for_agent(agent)


def setup_maps_for_agent(agent):
	""" Setup maps for an agent """
	for k in "input_map", "output_map", "map", "map_cs", "input_map_cs", "output_map_cs":
		if k not in agent:
			agent[k] = {}
	for k, v in agent["input_map"].items():
		k_lc = k.lower()
		if k == k_lc:
			continue
		del agent["input_map"][k]
		agent["input_map"][k_lc] = v
	for k, v in agent["output_map"].items():
		k_lc = k.lower()
		if k == k_lc:
			continue
		del agent["output_map"][k]
		agent["output_map"][k_lc] = v
	for k, v in agent["map"].items():
		k_lc = k.lower()
		v_lc = v.lower()
		if k_lc not in agent["input_map"]:
			agent["input_map"][k_lc] = v
		if v_lc not in agent["output_map"]:
			agent["output_map"][v_lc] = k
	for k, v in agent["map_cs"].items():
		if k not in agent["input_map_cs"]:
			agent["input_map_cs"][k] = v
		if v not in agent["output_map_cs"]:
			agent["output_map_cs"][v] = k


def register_all_agents():
	""" Register agents """
	register_agents("local", AGENTS_LOCAL, local_agent)
	register_agents("remote", AGENTS_REMOTE, remote_agent)

	if UNSAFE:
		register_agents("tool", AGENTS_PROGRAMMING, safe_shell)

	register_agents("tool", {agent: {"name": agent} for agent in search.agents}, run_search)
	if not ADULT:
		del AGENTS["pr0nto"]
		del AGENTS["yoni"]

	setup_agent_maps()
	# TODO Moar!
	# - translator: Poly


def load_tokenizer(model_path: Path):
	""" Load the Llama tokenizer """
	return transformers.AutoTokenizer.from_pretrained(str(model_path))


def count_tokens_in_text(text, tokenizer):
	""" Count the number of tokens in a text. """
	return len(tokenizer(text).input_ids)


def leading_spaces(text):
	""" Return the number of leading spaces in a text. """
	return re.match(r"\s*", text).group(0)


def trim_response(response, args, agent_name, people_lc = None):
	""" Trim the response to the first message. """
	if people_lc is None:
		people_lc = []

	def check_person_remove(match):
		"""Remove text starting with a known person's name."""
		if match.group(2).lower() in people_lc:
			return ""
		return match.group(1)

	response = response.strip()

	response_before = response

	# remove agent's own `name: ` from response
	agent_name_esc = re.escape(agent_name)
	response = re.sub(r"^" + agent_name_esc + r"\s*:\s(.*)", r"\1", response, flags=re.MULTILINE)

	# remove lines starting with a known person's name
	response = re.sub(r"(\n(\w+)\s*:\s*(.*))", check_person_remove, response, flags=re.DOTALL)
	response = re.sub(r"\n(##|<nooutput>|<noinput>|#GPTModelOutput|#End of output|\*/\n\n// End of dialogue //|// end of output //|### Output:|\\iend{code})(\n.*|$)", "", response , flags=re.DOTALL|re.IGNORECASE)

	if response != response_before:
		logger.warning("Trimmed response: %r\nto: %r", response_before, response)

	response = " " + response.strip()
	return response


def fix_layout(response, _args):
	""" Fix the layout and indentation of the response. """
	lines = response.strip().split("\n")
	out = []
	in_table = False
	add_tab = False

	for line in lines[1:]:
		if not line.startswith("\t"):
			add_tab = True
			break

	for i, line in enumerate(lines):
		# markdown tables must have a blank line before them ...
		if not in_table and ("---" in line or re.search(r'\|.*\|', line)):
			if i > 0 and lines[i-1].strip():
				out.append("\t")
			in_table = True

		if in_table and not line.strip():
			in_table = False

		if i > 0 and add_tab:
			line = "\t" + line

		out.append(line)

	response = ("\n".join(out)).rstrip()

	return response


def get_fulltext(args, model_name, history, history_start, invitation, delim):
	""" Get the full text from the history, and cut to the right length. """
	# FIXME this sync function is potentially slow
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


async def client_request(portal, input_text, config=None, timeout=None):
	""" Call the core server and get a response. """

	req = await portal.prepare_request(config)

	req_input = req/"request.txt"
	req_input.write_text(input_text, encoding="utf-8")

	await portal.send_request(req)

	resp, status = await portal.wait_for_response(req, timeout=timeout)

	if status == "error":
		await portal.response_error(resp)  # raises RuntimeError?!

	new = resp/"new.txt"
	new_text = new.read_text(encoding="utf-8") if new.exists() else ""

	return new_text, resp #, generated_text


def history_read(file, args):
	""" Read the history from a file. """
	text = ""
	if file and os.path.exists(file):
		with open(file, encoding="utf-8") as f:
			text = f.read()
	# lookahead for non-space after newline
	history = re.split(r"\n+(?=\S|$)", text) if text else []

	if history and not history[-1]:
		history.pop()
	return history


def history_write(file, history, delim="\n", mode="a", invitation=""):
	""" Write or append the history to a file. """
	if not file:
		return
	text = delim.join(history) + invitation
	with open(file, mode, encoding="utf-8") as f:
		f.write(text)


def summary_read(file, args):
	""" Read summary from a file. """
	text = ""
	if file and os.path.exists(file):
		with open(file, encoding="utf-8") as f:
			text = f.read()
	# Indent it all and put Summary: at the start
	if text:
		text = "Summary:" + re.sub(r'^', '\t', text, flags=re.MULTILINE)
		lines = text.split(args.delim)
	else:
		lines = []
	return lines


async def run_search(agent, query, file, args, history, history_start, limit=True, mission=None, summary=None):
	""" Run a search agent. """
	name = agent["name"]
	logger.debug("history: %r", history)
	history_messages = list(chat.lines_to_messages(history))
	logger.debug("history_messages: %r", history_messages)
	message = history_messages[-1]
	query = message["content"]
	logger.debug("query 1: %r", query)
# 	query = query.split("\n")[0]
# 	logger.debug("query 2: %r", query)
#	rx = r'((ok|okay|hey|hi|ho|yo|hello|hola)\s)*\b'+re.escape(name)+r'\b'
	rx = r'.*?\b'+re.escape(name)+r'\b'
	logger.debug("rx: %r", rx)
	query = re.sub(rx, '', query, flags=re.IGNORECASE|re.DOTALL)
	logger.debug("query 3: %r", query)
	query = re.sub(r'(show me|search( for|up)?|find( me)?|look( for| up)?|what(\'s| is) (the|a|an)?)\s+', '', query, re.IGNORECASE)
	logger.debug("query 4: %r", query)
	query = re.sub(r'#.*', '', query)
	logger.debug("query 5: %r", query)
	query = re.sub(r'[^\x00-~]', '', query)   # filter out emojis
	logger.debug("query 6: %r", query)
	query = re.sub(r'^\s*[,;.]|[,;.]\s*$', '', query).strip()
	logger.warning("query: %r %r", name, query)
	# TODO make the search library async too
	async def async_search(query, name, limit):
		return await asyncio.to_thread(search.search, query, engine=name, markdown=True, limit=limit)
	response = await async_search(query, name, limit)
	response2 = f"{name}:\t{response}"
	response3 = fix_layout(response2, args)
	logger.debug("response3:\n%s", response3)
	return response3


async def process_file(file, args, history_start=0) -> bool:
	"""Process a file, return True if appended new content."""
	logger.info("Processing %s", file)

	history = history_read(file, args)

	history_count = len(history)

	# Load mission file, if present
	mission_file = re.sub(r'\.bb$', '.m', file)

	mission = history_read(mission_file, args)

	# Load summary file, if present
	summary_file = re.sub(r'\.bb$', '.s', file)
	summary = summary_read(summary_file, args)

#	logger.warning("loaded mission: %r", mission)
#	logger.warning("loaded history: %r", history)

	# get latest user name and bot name from history
	bot = AGENT_DEFAULT
	if history:
		history_messages = list(chat.lines_to_messages(history))

		who = conductor.who_should_respond(history_messages[-1], agents=AGENTS, history=history_messages, default=bot)
		if who:
			bot = who[0]
		else:
			bot = None
		logger.warning("who should respond: %r", who)

	if bot and bot.lower() in AGENTS:
		#     - query is not even used in remote_agent
		query1 = history[-1] if history else None
		logger.debug("query1: %r", query1)
		messages = list(chat.lines_to_messages([query1]))
		query = messages[-1]["content"] if query1 else ""
		logger.debug("query: %r", query)
		agent = AGENTS[bot.lower()]
		response = await run_agent(agent, query, file, args, history, history_start=history_start, mission=mission, summary=summary)
		history.append(response)
		logger.debug("history: %r", history)
		history_write(file, history[-1:], delim=args.delim, invitation=args.delim)

		return True
	return False


async def run_agent(agent, query, file, args, history, history_start=0, mission=None, summary=None):
	""" Run an agent. """
	function = agent["fn"]
	logger.debug("query: %r", query)
	return await function(query, file, args, history, history_start=history_start, mission=mission, summary=summary)


async def local_agent(agent, _query, file, args, history, history_start=0, mission=None, summary=None):
	""" Run a local agent. """
	# print("local_agent: %r %r %r %r %r %r", query, agent, file, args, history, history_start)

	# Note: the invitation should not end with a space, or the model might use lots of emojis!
	name = agent["name"]
	invitation = args.delim + name + ":"

	model_name = agent["model"]
	n_context = agent.get("default_context")
	if n_context is not None:
		context = history[-n_context:]
	else:
		context = history.copy()
	apply_maps(agent["input_map"], agent["input_map_cs"], context)

	# add system messages
	system_top = agent.get("system_top")
	system_bottom = agent.get("system_bottom")
	if system_bottom:
		n_messages = len(context)
		pos = agent.get("system_bottom_pos", 0)
		pos = min(pos, n_messages)
		system_bottom_role = agent.get("system_bottom_role", "System")
		if system_bottom_role:
			context.insert(n_messages - pos, f"{system_bottom_role}:\t{system_bottom}")
		else:
			context.insert(n_messages - pos, f"{system_bottom}")
	if system_top:
		system_top_role = agent.get("system_top_role", None)
		context.insert(0, f"{system_top_role}:\t{system_top}")

	logger.debug("context: %r", context)

	agent_name_esc = regex.escape(name)

	def clean_the_prompt(context, agent_name_esc):
		context = [regex.sub(r".*?\t", r"", line).strip() for line in context]
		text = args.delim.join(context)
		text = regex.sub(r".*?\b" + agent_name_esc + r"\b[,;.]?", r"", text, flags=regex.DOTALL | regex.IGNORECASE)
		text = re.sub(r"```(.*?)```", r"\1", text, flags=re.DOTALL)
		return text.strip()

	clean_prompt = agent.get("clean_prompt", False)
	if clean_prompt:
		fulltext = clean_the_prompt(context, agent_name_esc)
	else:
		fulltext, history_start = get_fulltext(args, model_name, context, history_start, invitation, args.delim)

	if "config" in agent:
		gen_config = agent["config"].copy()
		gen_config["model"] = model_name
	else:
		# load the config each time, in case it has changed
		# TODO the config should be per agent, not global
		gen_config = load_config(args)

	# TODO: These stop regexps don't yet handle names with spaces or punctuation.
	gen_config["stop_regexs"] = [
		# Allow the agent's own name (ignoring case) using a negative lookahead.
		# A line starting with a name starting with any letter, colon and whitespace.
		r"(?umi)^(?!"+agent_name_esc+r"\s*:)[\p{L}][\p{L}\p{N}_]*:\s*\Z",
		# A name beginning with upper-case letter followed by colon and TAB, anywhere in the line
		r"(?u)\b(?!"+agent_name_esc+r":)[\p{Lu}][\p{L}\p{N}_]*:\t",
	]

	service = agent["service"]

	portal = get_service_portal(service)

	logger.debug("fulltext: %r", fulltext)
	logger.debug("config: %r", gen_config)
	logger.debug("portal: %r", str(portal.portal))

	response, resp = await client_request(portal, fulltext, config=gen_config, timeout=LOCAL_AGENT_TIMEOUT)

	apply_maps(agent["output_map"], agent["output_map_cs"], [response])

	room = chat.Room(path=Path(file))

	# look for attachments, other files in resp/ in sorted order
	for resp_file in sorted(resp.iterdir()):
		if resp_file.name in ["new.txt", "request.txt", "config.yaml", "log.txt"]:
			continue
		name, url, medium, markdown, task = await chat.upload_file(room.name, agent["name"], str(resp_file), alt=fulltext)
		if response:
			response += f"\n\n"
		response += markdown

	await portal.remove_response(resp)

	logger.debug("response: %r", response)

	agent_names = list(AGENTS.keys())
	history_messages = list(chat.lines_to_messages(history))
	all_people = conductor.participants(history_messages)
	people_lc = list(map(str.lower, set(agent_names + all_people)))

	response = trim_response(response, args, agent["name"], people_lc=people_lc)
	response = fix_layout(response, args)

	if invitation:
		tidy_response = invitation.strip() + "\t" + response.strip()
	else:
		tidy_response = response

	# TODO accept attachments from model

	logger.debug("tidy response: %r", tidy_response)

	return tidy_response


def apply_maps(mapping, mapping_cs, context):
	""" for each word in the mapping, replace it with the value """

	logger.warning("apply_maps: %r %r", mapping, mapping_cs)

	if not (mapping or mapping_cs):
		return

	def map_word(match):
		word = match.group(1)
		word_lc = word.lower()
		out = mapping_cs.get(word)
		if out is None:
			out = mapping.get(word_lc)
		if out is None:
			out = word
		return out

	for i, msg in enumerate(context):
		old = msg
		context[i] = re.sub(r"\b(.+?)\b", map_word, msg)
		if context[i] != old:
			logger.warning("map: %r -> %r", old, context[i])


async def remote_agent(agent, query, file, args, history, history_start=0, mission=None, summary=None):
	""" Run a remote agent. """
	n_context = agent["default_context"]
	context = history[-n_context:]
	# XXX history is a list of lines, not messages, so won't the context sometimes contain partial messages? Yuk. That will interact badly with missions, too.
	# hacky temporary fix here for now, seems to work:
	while context and context[0].startswith("\t"):
		logger.warning("removing partial message at start of context: %r", context[0])
		context.pop(0)
	# prepend mission / info / context
	# TODO try mission as a "system" message?
	context2 = []
	if mission:
		context2 += mission
	if summary:
		context2 += summary
	context2 += context
	# put remote_messages[-1] through the input_maps
	apply_maps(agent["input_map"], agent["input_map_cs"], context2)

	context_messages = list(chat.lines_to_messages(context2))

	remote_messages = []

#		agent_names = list(AGENTS.keys())
#		agents_lc = list(map(str.lower, agent_names))

	for msg in context_messages:
		logger.debug("msg1: %r", msg)
		u = msg.get("user")
		u_lc = u.lower() if u is not None else None
#			if u in agents_lc:
		content = msg["content"]
		if u_lc == agent['name'].lower():
			role = "assistant"
		else:
			role = "user"
			if u:
				content = u + ": " + content
		msg2 = {
			"role": role,
			"content": content,
		}
		logger.debug("msg2: %r", msg2)
		remote_messages.append(msg2)

	while remote_messages and remote_messages[0]["role"] == "assistant" and "claude" in agent["model"]:
		remote_messages.pop(0)

	# add system messages
	system_top = agent.get("system_top")
	system_bottom = agent.get("system_bottom")
	if system_bottom:
		n_messages = len(remote_messages)
		pos = agent.get("system_bottom_pos", 0)
		pos = min(pos, n_messages)
		system_bottom_role = agent.get("system_bottom_role", "user")
		remote_messages.insert(n_messages - pos, {"role": system_bottom_role, "content": system_bottom})
	if system_top:
		system_top_role = agent.get("system_top_role", "system")
		remote_messages.insert(0, {"role": system_top_role, "content": system_top})

	# TODO this is a bit dodgy and won't work with async
	opts = {
		"model": agent["model"],
		"indent": "\t",
	}
	llm.set_opts(opts)

	logger.warning("DEBUG: context_messages: %r", remote_messages)

	logger.warning("querying %r = %r", agent['name'], agent["model"])
	output_message = await llm.aretry(llm.allm_chat, REMOTE_AGENT_RETRIES, remote_messages)

	response = output_message["content"]
	box = [response]
	apply_maps(agent["output_map"], agent["output_map_cs"], box)
	response = box[0]

	if response.startswith(agent['name']+": "):
		logger.warning("stripping agent name from response")
		response = response[len(agent['name'])+2:]

	# fix indentation for code
	if opts["indent"]:
		lines = response.splitlines()
		lines = tab.fix_indentation_list(lines, opts["indent"])
		response = "".join(lines)


	logger.debug("response 1: %r", response)
	response = fix_layout(response, args)
	logger.debug("response 2: %r", response)
	response = f"{agent['name']}:\t{response.strip()}"
	logger.debug("response 3: %r", response)
	return response.rstrip()


async def run_subprocess(command, query):
	""" Run a subprocess asynchronously. """
	# Create the subprocess
	proc = await asyncio.create_subprocess_exec(
		*command,
		stdin=asyncio.subprocess.PIPE,
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.PIPE
	)

	# Write to stdin
	proc.stdin.write(query.encode("utf-8"))
	await proc.stdin.drain()
	proc.stdin.close()

	# Read stdout and stderr
	stdout, stderr = await proc.communicate()

	# Get the return code
	return_code = await proc.wait()

	return stdout.decode("utf-8"), stderr.decode("utf-8"), return_code


async def safe_shell(agent, query, file, args, history, history_start=0, command=None, mission=None, summary=None):
	""" Run a shell agent. """
	name = agent["name"]
	logger.debug("history: %r", history)
	history_messages = list(chat.lines_to_messages(history))
	logger.debug("history_messages: %r", history_messages)
	message = history_messages[-1]
	query = message["content"]
	logger.debug("query 1: %r", query)
	rx = r'((ok|okay|hey|hi|ho|yo|hello|hola)\s)*\b'+re.escape(name)+r'\b'
	logger.debug("rx: %r", rx)
	query = re.sub(rx, '', query, flags=re.IGNORECASE)
	logger.debug("query 2: %r", query)
	query = re.sub(r'^\s*[,;.]|\s*$', '', query).strip()
	logger.debug("query 3: %r", query)

	# shell escape in python
	agent["command"]
	cmd_str = ". ~/.profile ; "
	cmd_str += " ".join(map(shlex.quote, agent["command"]))

	command = ['sshc', 'allemande-nobody@localhost', "bash", "-c", cmd_str]
	agent["command"]

	# echo the query to the subprocess
	output, errors, status = await run_subprocess(command, query)

	# format the response
	response = ""
	if errors or status:
		response += "\n## status:\n" + str(status) + "\n\n"
		response += "## errors:\n```\n" + errors + "\n```\n\n"
		response += "## output:\n"
	response += "```\n" + output + "\n```\n"

	response2 = f"{name}:\t{response}"
	response3 = fix_layout(response2, args)
	logger.debug("response3:\n%s", response3)
	return response3


async def file_changed(file_path, change_type, old_size, new_size, args, skip):
	"""Process a file change."""
	if args.ext and not file_path.endswith(args.ext):
		return
	if change_type == Change.deleted:
		return
	if not args.shrink and old_size and new_size < old_size:
		return
	if new_size == 0:
		return

	if skip.get(file_path):
		logger.info("Won't react to AI response: %r", file_path)
		del skip[file_path]
		return

	responded = False
	try:
		logger.info("Processing file: %r", file_path)
		responded = await process_file(file_path, args)
	except Exception as e:
		logger.exception("Processing file failed", exc_info=True)

	# avoid re-processing in response to an AI response
	if responded:
		logger.info("Will skip processing after agent response: %r", file_path)
		skip[file_path] = 1


async def watch_loop(args):
	"""Follow the watch log, and process files."""

	skip = {}

	async with atail.AsyncTail(filename=args.watch, follow=True, rewind=True) as queue:
		while (line := await queue.get()) is not None:
			try:
				file_path, change_type, old_size, new_size = line.rstrip("\n").split("\t")
				change_type = Change(int(change_type))
				old_size = int(old_size) if old_size != "" else None
				new_size = int(new_size) if new_size != "" else None

				await file_changed(file_path, change_type, old_size, new_size, args, skip)
			finally:
				queue.task_done()


def load_config(args):
	""" Load the generations config file. """
	config = {}
	if args.config:
		with open(args.config, encoding="utf-8") as f:
			settings = yaml.load(f, Loader=yaml.FullLoader)
		for k, v in settings.items():
			config[k] = v
	if not config:
		config = None
	return config


def load_model_tokenizer(args):
	""" Load the model tokenizer. """
	models_dir = Path(os.environ["ALLEMANDE_MODELS"])/"llm"
	model_path = Path(models_dir) / args.model
	if args.model and not model_path.exists() and args.model.endswith(".gguf"):
		args.model = args.model[:-len(".gguf")]
		model_path = Path(models_dir) / args.model
	logger.info("model_path: %r", model_path)
	if args.model and model_path.exists():
		# This will block, but it doesn't matter because this is the init for the program.
		return load_tokenizer(model_path)
	return None


def get_opts():  # pylint: disable=too-many-statements
	""" Get the command line options. """
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	modes_group = parser.add_argument_group("Modes of operation")
	modes_group.add_argument("--watch", "-w", default=None, help="Watch mode, follow a watch log file")

	watch_group = parser.add_argument_group("Watch mode options")
	watch_group.add_argument("--ext", default=DEFAULT_FILE_EXTENSION, help="File extension to watch for")
	watch_group.add_argument("--shrink", action="store_true", help="React if the file shrinks")

	format_group = parser.add_argument_group("Format options")
	format_group.add_argument("--delim", default="\n\n", help="Delimiter between messages")
	format_group.add_argument("--memory", "-x", type=int, default=32*1024 - 2048, help="Max number of tokens to keep in history, before we drop old messages")

	model_group = parser.add_argument_group("Model options")
	model_group.add_argument("--model", "-m", default="default", help="Model name or path")
	model_group.add_argument("--config", "-c", default=None, help="Model config file, in YAML format")

	ucm.add_logging_options(parser)

	args = parser.parse_args()

	ucm.setup_logging(args)

	logger.debug("Options: %r", args)

	return args


async def main():
	""" Main function. """
	register_all_agents()

	args = get_opts()

	TOKENIZERS[args.model] = load_model_tokenizer(args)

	if not args.watch:
		raise ValueError("Watch file not specified")

	logger.info("Watching")
	await watch_loop(args)


if __name__ == "__main__":
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		logger.info("interrupted")
		sys.exit(0)
