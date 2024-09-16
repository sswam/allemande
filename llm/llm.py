#!/usr/bin/env python3
""" llm.py: a simple wrapper for the OpenAI ChatGPT API and Anthropic's Claude API """

# TODO create compatible libraries for other APIs in future
# TODO consider splitting off the OpenAI specific stuff into a separate library
# TODO use cached responses if possible

import sys

from sys import stdin, stdout
import os
import logging
import re
from typing import Optional, IO
from math import inf
# import argparse
import time
import random
from pathlib import Path
import textwrap

import argh

import openai
from openai import OpenAI

openai_client = OpenAI()
import tiktoken

import tab
import anthropic
import claude
from bard import Bard
from slugify import slugify

# import json

logger = logging.getLogger(__name__)


# settngs

LOGDIR = Path(os.environ["HOME"])/"llm.log"
LOGFILE_NAME_MAX_LEN = 100
RETRIES = 20
exceptions_to_retry = (openai.RateLimitError, openai.APIConnectionError, openai.InternalServerError,
	anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError)

default_model = 'claude'

models = {
	"o1-preview": {
		"alias": ["op", "gertie"],
		"vendor": "openai",
		"description": "The o1 series of large language models are trained with reinforcement learning to perform complex reasoning. o1 models think before they answer, producing a long internal chain of thought before responding to the user.",
		"cost_in": 15,
		"cost_out": 60,
	},
	"o1-mini": {
		"alias": ["om", "feyn"],
		"vendor": "openai",
		"description": "The o1 series of large language models are trained with reinforcement learning to perform complex reasoning. o1 models think before they answer, producing a long internal chain of thought before responding to the user.",
		"cost_in": 3,
		"cost_out": 12,
	},
	"gpt-4": {
		"alias": ["4", "emmy"],
		"vendor": "openai",
		"id": "gpt-4o-2024-08-06",
		"description": "GPT-4o is our most advanced multimodal model that’s faster and cheaper than GPT-4 Turbo with stronger vision capabilities. The model has 128K context and an October 2023 knowledge cutoff.",
		"cost_in": 2.5,
		"cost_out": 10,
	},
	"gpt-4o-mini": {
		"alias": ["4m", "dav"],
		"vendor": "openai",
		"description": "GPT-4o mini is our most cost-efficient small model that’s smarter and cheaper than GPT-3.5 Turbo, and has vision capabilities. The model has 128K context and an October 2023 knowledge cutoff.",
		"cost_in": 0.15,
		"cost_out": 0.6,
	},

	"claude": {
		"alias": ["c", "claud"],
		"vendor": "anthropic",
		"id": "claude-3-5-sonnet-20240620",
		"description": "Claude 3.5 Sonnet is Anthropic's latest AI model, offering improved intelligence, speed, and cost-effectiveness compared to previous versions, with new capabilities in reasoning, coding, and vision.",
		"cost_in": 3,
		"cost_out": 15,
	},
	"claude-haiku": {
		"alias": ["i", "clia"],
		"vendor": "anthropic",
		"id": "claude-3-haiku-20240307",
		"description": "Claude 3 Haiku is Anthropic's fastest and most affordable large language model, offering high-speed processing, state-of-the-art vision capabilities, and strong benchmark performance for enterprise applications.",
		"cost_in": 0.25,
		"cost_out": 1.25,
	},
#	"bard": {
#		"alias": ["b", "jaski"],
#		"vendor": "google",
#		"description": "Google Bard is a large language model (LLM) chatbot developed by Google AI. It is trained on a massive dataset of text and code, and can generate text, translate languages, write different kinds of creative content, and answer your questions in an informative way.",
#	}
}

# default is $LLM_MODEL or default_model as above

# first_model = next(iter(models.keys()))

env_llm_model = os.environ.get("LLM_MODEL")

if env_llm_model in models:
	default_model = env_llm_model

ALLOWED_ROLES = ["user", "assistant", "system"]

DEFAULT_TEMPERATURE = 1
TOKEN_LIMIT = inf

fake_completion = {
	"choices": [
		{
			"finish_reason": "stop",
			"index": 0,
			"message": {
				"content": "\n\nSure, Sam! Here's a dad joke for you: \"Why did the tomato turn red? Because it saw the salad dressing!\"",
				"role": "assistant"
			}
		}
	],
	"created": 1678809131,
	"id": "chatcmpl-6u1EZ06waciROkpOqDHVdi2HtL3iX",
	"model": "gpt-3.5-turbo-0301",
	"object": "chat.completion",
	"usage": {
		"completion_tokens": 104,
		"prompt_tokens": 24,
		"total_tokens": 128
	}
}


def get_model_by_alias(model):
	""" If the model is an alias or abbreviation, expand it. """
	abbrev_models = [k for k, v in models.items() if model in v.get("alias", [])]
	if len(abbrev_models) == 1:
		model = abbrev_models[0]
	return model


class AutoInit:  # pylint: disable=too-few-public-methods
	""" Automatically set attributes from kwargs. """
	def __init__(self, **kwargs):
		for k, v in kwargs.items():
			if hasattr(self, k):
				setattr(self, k, v)
	def __str__(self):
	    attributes = []
	    for key, value in vars(self).items():
	        if not key.startswith('_'):
	            attributes.append(f"{key}={value!r}")
	    class_name = self.__class__.__name__
	    return f"{class_name}({', '.join(attributes)})"
	


class Options(AutoInit):  # pylint: disable=too-few-public-methods
	""" Options for the chat function. """
	model: str = default_model
	fake: bool = False
	temperature: Optional[float] = None
	token_limit: Optional[int] = None
	indent: Optional[str] = None
	state_file: Optional[str] = None
	auto_save: bool = False
	def __init__(self, **kwargs):
		if kwargs.get("model"):
			kwargs["model"] = get_model_by_alias(kwargs["model"])
		if kwargs.get("state_file") and kwargs.get("auto_save") is None:
			kwargs["auto_save"] = True
		super().__init__(**kwargs)


opts: Options = Options()


def set_opts(_opts):
	""" Set the global options. """
	global opts  # pylint: disable=global-statement
	opts = Options(**_opts)


def chat_gpt(messages):  # 0.9, token_limit=150, top_p=1, frequency_penalty=0, presence_penalty=0, stop=["\n\n"]):
	""" Chat with OpenAI ChatGPT models. """
	model = opts.model
	if "id" in models[model]:
		model = models[model]["id"]

	logger.debug("model: %s", model)

	temperature = opts.temperature
	token_limit = opts.token_limit

	if temperature is None:
		temperature = DEFAULT_TEMPERATURE
	if token_limit is None:
		token_limit = TOKEN_LIMIT
	response = openai_client.chat.completions.create(model=model, messages=messages)

	logger.debug("llm: response: %s", response)

	message = response.choices[0].message
	output_message = {
		"role": message.role,
		"content": message.content,
	}

	return output_message


def chat_claude(messages):
	""" Chat with Anthropic Claude models. """
	model = opts.model
	if "id" in models[model]:
		model = models[model]["id"]

	temperature = opts.temperature
	token_limit = opts.token_limit
	response = claude.chat_claude(messages, model=model, temperature=temperature, token_limit=token_limit)
	completion = claude.response_completion(response)
	message = { "role": "assistant", "content": completion }
	return message


def chat_bard(messages):
	""" Chat with Google Bard models. """
	# We can only pass in the last user message; let's hope we have the right state file!
	# We can't run all the user messages again; Bard will likely not do the same thing so it would be a mess.
	# Perhaps we should save state in chat metadata.
	if not messages or messages[-1]["role"] == "assistant":
		raise ValueError("Bard requires a conversation ending with a user message.")
	bard = Bard(state_file=opts.state_file, auto_save=opts.auto_save)
	response = bard.get_answer(messages[-1]["content"])
	completion = response["content"]
	message = { "role": "assistant", "content": completion }
	return message


def llm_chat(messages):
	""" Send a list of messages to the model, and return the response. """
	logger.debug("llm_chat: input: %r", messages)

	model = opts.model
	vendor = models[model]["vendor"]

	if opts.fake:
		return fake_completion
	if vendor == "anthropic":
		return chat_claude(messages)
	if vendor == "openai":
		return chat_gpt(messages)
	if vendor == "google":
		return chat_bard(messages)
	raise ValueError(f"unknown model: {model}")


def split_message_line(message, allowed_roles=None):
	""" Split a message into a role and content. """

	try:
		role, message = message.split(":", 1)
	except ValueError as ex:
		raise ValueError(f"invalid message, missing role: {message}") from ex

	if allowed_roles is not None and role not in allowed_roles:
		raise ValueError(f"invalid role in message: {role}")

	message = message.strip()

	return role, message


def lines_to_messages(lines, system=None):
	""" Convert a list of lines to a list of messages, with roles. """

	messages = []

	if system is not None:
		system_message_obj = {"role": "system", "content": system}
		logger.info("system message: %s", system_message_obj)
		messages.append(system_message_obj)

	# add the input messages
	i = 0
	line = lines[0]
	while i < len(lines):
		role, message = split_message_line(line, allowed_roles=ALLOWED_ROLES)
		while True:
			i += 1
			if i == len(lines):
				break
			line = lines[i].rstrip('\r\n')
			if line and not re.match(r'^\s', line):
				break
			line = re.sub(r'^\s', '', line)
			message += "\n" + line

		message_obj = {"role": role, "content": message}
		logger.info("input message: %s", message_obj)
		messages.append(message_obj)

		# the role alternates by default
		role = "assistant" if role == "user" else "user"

	return messages


def messages_to_lines(messages):
	""" Convert a list of messages to a list of lines, with roles. """
	lines = []
	# add the output messages

	for message in messages:
		role = message['role']
		content = message['content'].strip()
		content = re.sub(r'\n', '\n\t', content)
		line = f"{role}:\t{content}\n"
		lines.append(line)
	return lines


def read_utf_replace(istream):
	""" Read input, replacing invalid UTF-8 with the replacement character. """
	try:
		input_data = istream.buffer.read()
		input_text = input_data.decode("utf-8", errors="replace")
	except UnicodeDecodeError as ex:
		logger.warning("error reading input: %s", ex)
		input_text = istream.read()
	return input_text


@argh.arg("prompt", nargs="+", help="prompt text")
@argh.arg("-P", "--prompt2", help="second prompt text")
@argh.arg("-i", "--input", dest="istream", default=None, help="input file")
@argh.arg("-o", "--output", dest="ostream", default=None, help="output file")
@argh.arg("-m", "--model", default=default_model, help="model name")
@argh.arg("-I", "--indent", default=None, help="indentation string")
@argh.arg("-t", "--temperature", type=float, help="temperature")
@argh.arg("-l", "--token-limit", type=int, help="token limit")
@argh.arg("-r", "--retries", type=int, default=RETRIES, help="number of retries")
@argh.arg("-s", "--state-file", help="state file for Google Bard")
@argh.arg("-e", "--empty-to-empty", action="store_true", help="return empty string for empty input")
@argh.arg("-E", "--empty-ok", action="store_true", help="allow empty input")
@argh.arg("-L", "--log", action="store_true", help=f"log to a file in {LOGDIR}")
@argh.arg("-x", "--lines", action="store_true", help="process each line separately, like perl -p")
@argh.arg("-R", "--repeat", action="store_true", help="repeat the prompt as prompt2, changing 'below' to 'above' only")
def process(*prompt, prompt2: Optional[str]=None, istream: IO[str]=None, ostream: IO[str]=None, model: str=default_model, indent=None, temperature=None, token_limit=None, retries=RETRIES, state_file=None, empty_ok=False, empty_to_empty=True, log=True, lines=False, repeat=False):
	""" Process some text through the LLM with a prompt. """
	if __name__ == "__main__":
		istream = sys.stdin
		ostream = sys.stdout

	set_opts(vars())

	prompt = " ".join(prompt)
	prompt = prompt.rstrip()

	input_text = read_utf_replace(istream)
	input_text = input_text.rstrip()

	if not input_text and empty_to_empty:
		return ""
	if not input_text and not empty_ok:
		raise ValueError("no input")

	if prompt2:
		prompt2 = prompt2.rstrip()
	if repeat:
		prompt2 = re.sub(r"\bbelow\b", "above", prompt)

	if not lines:
		return process2(prompt, prompt2, input_text, ostream=ostream, model=model, indent=indent, temperature=temperature, token_limit=token_limit, retries=retries, state_file=state_file, log=log)

	# split the input into lines
	lines = input_text.splitlines()
	output = []

	for line in lines:
		line = line.rstrip()
		if not line:
			continue
		output1 = process2(prompt, prompt2, line, ostream=ostream, model=model, indent=indent, temperature=temperature, token_limit=token_limit, retries=retries, state_file=state_file, log=log)
		output.append(output1)

	output_s = "\n".join(output)

	return output_s


def process2(prompt, prompt2, input_text, ostream, model, indent, temperature, token_limit, retries, state_file, log):
	""" Process some text through the LLM with a prompt. """
	full_input = f"""
{prompt}

{input_text}
"""
	if prompt2:
		full_input += "\n" + prompt2 + "\n"
	return query(full_input, ostream=ostream, model=model, indent=indent, temperature=temperature, token_limit=token_limit, retries=retries, state_file=state_file, log=log)


def query(*prompt, ostream: Optional[IO[str]]=None, model: str=default_model, indent=None, temperature=None, token_limit=None, retries=RETRIES, state_file=None, log=True):  # pylint: disable=unused-argument
	""" Ask the LLM a question. """
	if __name__ == "__main__":
		ostream = sys.stdout
	set_opts(vars())
	return retry(query2, retries, *prompt, ostream=ostream, log=log)


def query2(*prompt, ostream: Optional[IO[str]]=None, log=True):
	""" Ask the LLM a question. """
	prompt = " ".join(prompt)

	prompt = prompt.rstrip() + "\n"

	# TODO use a system message?

	input_message = {"role": "user", "content": prompt}
	output_message = llm_chat([input_message])
	content = output_message["content"]

	# fix indentation for code
	if opts.indent:
		logger.warning("fix indentation for code")
		lines = content.splitlines()
		lines = tab.fix_indentation_list(lines, opts.indent)
		content = "".join(lines)
	if log:
		LOGDIR.mkdir(parents=True, exist_ok=True)
		basename = slugify(prompt)[:LOGFILE_NAME_MAX_LEN]
		logfile = LOGDIR/(f"answer.{basename}.md")
		logfile_prompt = LOGDIR/(f"prompt.{basename}.md")
		while logfile.exists():
			time_s = time.strftime("%Y-%m-%dT%H:%M:%S")
			logfile = LOGDIR/f"answer.{basename}.{time_s}.md"
			logfile_prompt = LOGDIR/Path(f"prompt.{basename}.{time_s}.md")
		logfile_prompt.write_text(prompt.rstrip()+"\n", encoding="utf-8")
		logfile.write_text(content.rstrip()+"\n", encoding="utf-8")

	if ostream:
		print(content, file=ostream)
		return ""

	return content


# TODO use backoff module?
def retry(fn, n_tries, *args, sleep_min=1, sleep_max=2, **kwargs):
	""" Retry a function n_tries times. """
	for i in range(n_tries):
		try:
			return fn(*args, **kwargs)
		except exceptions_to_retry as ex:
			delay = random.uniform(sleep_min, sleep_max)
			logger.warning("retry: exception, sleeping for %.3f: %s", delay, ex)
			msg = str(ex)
			if i == n_tries - 1:
				raise
			time.sleep(delay)
			sleep_min *= 2
			sleep_max *= 2
	return None


def chat(istream=stdin, ostream=stdout, model=default_model, fake=False, temperature=None, token_limit=None, retries=RETRIES, state_file=None, auto_save=None):  # pylint: disable=unused-argument
	""" Chat with the LLM, well it inputs a chat file and ouputs the new message to append. """
	set_opts(vars())
	return retry(chat2, retries, istream=istream, ostream=ostream)


def chat2(istream=stdin, ostream=stdout):
	""" Chat with the LLM, well it inputs a chat file and ouputs the new message to append. """
	input_lines = read_utf_replace(istream).splitlines()
	input_messages = lines_to_messages(input_lines)
	response_message = llm_chat(input_messages)
	output_lines = messages_to_lines([response_message])
	ostream.writelines(output_lines)


def count(istream=stdin, model=default_model, in_cost=False, out_cost=False):
	""" count tokens in a file """
	set_opts(vars())
	text = read_utf_replace(istream)
	model = models[opts.model]
	vendor = model["vendor"]
	if vendor == "openai":
		try:
			enc = tiktoken.encoding_for_model(opts.model)
		except KeyError:
			enc_name = "o200k_base"
			logger.warning(f"model {opts.model} not known to tiktoken, assuming {enc_name}")
			enc = tiktoken.get_encoding(enc_name)
		tokens = enc.encode(text)
		n_tokens = len(tokens)
	elif vendor == "anthropic":
		n_tokens = claude.count(text)
	else:
		raise ValueError(f"unknown model vendor: {vendor}")
	rv = [n_tokens]
	if in_cost:
		rv.append(model["cost_in"] * n_tokens / 1e6)
	if out_cost:
		rv.append(model["cost_out"] * n_tokens / 1e6)
	return tuple(rv)


#def cost(istream=stdin, model=default_model):
#	""" count tokens in a file """
#	set_opts(vars())
#	text = read_utf_replace(istream)
#	model = opts.model
#	if model.startswith("gpt"):
#		enc = tiktoken.encoding_for_model(model)
#		tokens = enc.encode(text)
#		return len(tokens)
#	if model.startswith("claude"):
#		return claude.count(text)
#	raise ValueError(f"unknown model: {model}")


def list_models(verbose=False):
	""" List the available models. """
	for name, model in models.items():
		print(name)
		if not verbose:
			continue
		for k, v in model.items():
			if k == "description":
				v = textwrap.fill(v, width=80, subsequent_indent='\t\t')
			print(f"\t{k}: {v}")


if __name__ == "__main__":
	argh.dispatch_commands([chat, query, process, count, list_models])
