#!/usr/bin/env python3
""" llm.py: a simple wrapper for the OpenAI ChatGPT API and Anthropic's Claude API """

# TODO create compatible libraries for other APIs in future
# TODO consider splitting off the OpenAI specific stuff into a separate library
# TODO use cached responses if possible

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

import argh

import openai
import tiktoken

import tab
import claude
from bard import Bard
from slugify import slugify

# import json

logger = logging.getLogger(__name__)

# settngs

LOGDIR = Path(os.environ["HOME"])/"llm.log"
LOGFILE_NAME_MAX_LEN = 100
RETRIES = 20
BAD_ERRORS_NO_RETRY = "maximum context length", "context_length_exceeded"

models = {
	"gpt-3.5-turbo": {
		"abbrev": "3+",
		"description": "Most capable GPT-3.5 model and optimized for chat at 1/10th the cost of text-davinci-003. Will be updated with our latest model iteration.",
		"cost": 0.002,
	},
	"gpt-4": {
		"abbrev": "4",
		"id": "gpt-4-1106-preview", # gpt-4-turbo
		"description": "More capable than any GPT-3.5 model, able to do more complex tasks, and optimized for chat. Will be updated with our latest model iteration.",
		"cost": 0.03,
	},
	"gpt-4-orig": {
		"abbrev": "4o",
		"description": "More capable than any GPT-3.5 model, able to do more complex tasks, and optimized for chat. Will be updated with our latest model iteration.",
		"cost": 0.03,
	},
	"claude-2": {
		"abbrev": "c",
		"description": "Anthropic's Claude 2 is an AI assistant with a focus on safety and Constitutional AI. It is trained to be helpful, harmless, and honest. This is our largest model, ideal for a wide range of more complex tasks.",
		"cost": 0.0,  # at least for now!
	},
	"claude-v1": {
		"abbrev": "c1",
		"description": "Anthropic's Claude is an AI assistant with a focus on safety and Constitutional AI. It is trained to be helpful, harmless, and honest. This is our largest model, ideal for a wide range of more complex tasks.",
		"cost": 0.0,  # at least for now!
	},
	"claude-instant-v1": {
		"abbrev": "i",
		"description": "A smaller model with far lower latency, sampling at roughly 40 words/sec! Its output quality is somewhat lower than claude-v1 models, particularly for complex tasks. However, it is much less expensive and blazing fast. We believe that this model provides more than adequate performance on a range of tasks including text classification, summarization, and lightweight chat applications, as well as search result summarization. Using this model name will automatically switch you to newer versions of claude-instant-v1 as they are released.",
		"cost": 0.0,  # at least for now!
	},
	"claude-v1-100k": {
		"abbrev": "c+",
		"description": "Anthropic's Claude with an 100k token window.",
		"cost": 0.0,  # at least for now!
	},
	"claude-instant-v1-100k": {
		"abbrev": "i+",
		"description": "Anthropic's Claude Instant with an 100k token window.",
		"cost": 0.0,  # at least for now!
	},
	"gpt-4-32k": {
		"abbrev": "4+",
		"description": "Same capabilities as the base gpt-4 mode but with 4x the context length. Will be updated with our latest model iteration.",
		"cost": 0.06,
	},
	"bard": {
		"abbrev": "b",
		"description": "Google Bard is a large language model (LLM) chatbot developed by Google AI. It is trained on a massive dataset of text and code, and can generate text, translate languages, write different kinds of creative content, and answer your questions in an informative way.",
	}
#	"gpt-3.5-turbo-0301": {
#		"description": "Snapshot of gpt-3.5-turbo from March 1st 2023. Unlike gpt-3.5-turbo, this model will not receive updates, and will only be supported for a three month period ending on June 1st 2023.",
#		"cost": 0.002,
#	},
#	"gpt-4-0314": {
#		"description": "Snapshot of gpt-4 from March 14th 2023. Unlike gpt-4, this model will not receive updates, and will only be supported for a three month period ending on June 14th 2023.",
#		"cost": 0.03,
#	},
#	"gpt-4-32k-0314": {
#		"description": "Snapshot of gpt-4-32 from March 14th 2023. Unlike gpt-4-32k, this model will not receive updates, and will only be supported for a three month period ending on June 14th 2023.",
#		"cost": 0.06,
#	},
#	"claude-v1.0": {
#		"description": "An earlier version of claude-v1.",
#		"cost": 0.0
#	},
#	"claude-v1.2": {
#		"description": "An improved version of claude-v1. It is slightly improved at general helpfulness, instruction following, coding, and other tasks. It is also considerably better with non-English languages. This model also has the ability to role play (in harmless ways) more consistently, and it defaults to writing somewhat longer and more thorough responses.",
#		"cost": 0.0
#	},
#	"claude-v1.3": {
#		"description": "A significantly improved version of claude-v1. Compared to claude-v1.2, it's more robust against red-team inputs, better at precise instruction-following, better at code, and better and non-English dialogue and writing.",
#		"cost": 0.0
#	},
#	"claude-instant-v1.0": {
#		"description": "Current default for claude-instant-v1.",
#		"cost": 0.0
#	}
}

#	"code-davinci-002": {
#		"abbrev": "x2",
#		"description": "Code completion model trained on 1.5 billion lines of code. Will be updated with our latest model iteration.",
#		"cost": 0,
#	},
#	"code-cushman-001": {
#		"abbrev": "x1",
#		"description": "Almost as capable as Davinci Codex, but slightly faster. This speed advantage may make it preferable for real-time applications.",
#		"cost": 0,
#	},

# default is $LLM_MODEL or first model in the dict

first_model = next(iter(models.keys()))
default_model = os.environ.get("LLM_MODEL", first_model)
if default_model not in models:
	default_model = first_model

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


def get_model_by_abbrev(model):
	""" If the model is an abbreviation, expand it. """
	abbrev_models = [k for k, v in models.items() if v.get("abbrev") == model]
	if len(abbrev_models) == 1:
		model = abbrev_models[0]
	return model


class AutoInit:  # pylint: disable=too-few-public-methods
	""" Automatically set attributes from kwargs. """
	def __init__(self, **kwargs):
		for k, v in kwargs.items():
			if hasattr(self, k):
				setattr(self, k, v)

class Options(AutoInit):  # pylint: disable=too-few-public-methods
	""" Options for the chat function. """
	model: str = default_model
	fake: bool = False
	temperature: Optional[float] = None
	token_limit: Optional[int] = None
	indent: str = "\t"
	state_file: Optional[str] = None
	auto_save: bool = False
	def __init__(self, **kwargs):
		if kwargs.get("model"):
			kwargs["model"] = get_model_by_abbrev(kwargs["model"])
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

	temperature = opts.temperature
	token_limit = opts.token_limit

	if temperature is None:
		temperature = DEFAULT_TEMPERATURE
	if token_limit is None:
		token_limit = TOKEN_LIMIT
	completion = openai.ChatCompletion.create(
		model=model,
		messages=messages
	)

	logger.debug("llm: completion: %s", completion)

	output_message = completion['choices'][0]['message']

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

	if opts.fake:
		return fake_completion
	if model.startswith("claude"):
		return chat_claude(messages)
	if model.startswith("gpt"):
		return chat_gpt(messages)
	if model.startswith("bard"):
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


def read_utf_replace(inp):
	""" Read input, replacing invalid UTF-8 with the replacement character. """
	try:
		input_data = inp.buffer.read()
		input_text = input_data.decode("utf-8", errors="replace")
	except UnicodeDecodeError as ex:
		logger.warning("error reading input: %s", ex)
		input_text = inp.read()
	return input_text


@argh.arg("prompt", nargs="+", help="prompt text")
@argh.arg("-P", "--prompt2", help="second prompt text")
@argh.arg("-i", "--inp", default=stdin, help="input file")
@argh.arg("-o", "--out", default=stdout, help="output file")
@argh.arg("-m", "--model", default=default_model, help="model name")
@argh.arg("-I", "--indent", default="\t", help="indentation string")
@argh.arg("-t", "--temperature", type=float, help="temperature")
@argh.arg("-l", "--token-limit", type=int, help="token limit")
@argh.arg("-r", "--retries", type=int, default=RETRIES, help="number of retries")
@argh.arg("-s", "--state-file", help="state file for Google Bard")
@argh.arg("-e", "--empty-to-empty", action="store_true", help="return empty string for empty input")
@argh.arg("-E", "--empty-ok", action="store_true", help="allow empty input")
@argh.arg("-L", "--log", action="store_true", help=f"log to a file in {LOGDIR}")
@argh.arg("-p", "--lines", action="store_true", help="process each line separately, like perl -p")
@argh.arg("-R", "--repeat", action="store_true", help="repeat the prompt as prompt2, changing 'below' to 'above' only")
def process(*prompt, prompt2: Optional[str]=None, inp: IO[str]=stdin, out: IO[str]=stdout, model: str=default_model, indent="\t", temperature=None, token_limit=None, retries=RETRIES, state_file=None, empty_ok=False, empty_to_empty=True, log=True, lines=False, repeat=False):
	""" Process some text through the LLM with a prompt. """
	set_opts(vars())

	prompt = " ".join(prompt)
	prompt = prompt.rstrip()

	input_text = read_utf_replace(inp)
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
		return process2(prompt, prompt2, input_text, out=out, model=model, indent=indent, temperature=temperature, token_limit=token_limit, retries=retries, state_file=state_file, log=log)

	# split the input into lines
	lines = input_text.splitlines()
	output = []

	for line in lines:
		line = line.rstrip()
		if not line:
			continue
		output1 = process2(prompt, prompt2, line, out=out, model=model, indent=indent, temperature=temperature, token_limit=token_limit, retries=retries, state_file=state_file, log=log)
		output.append(output1)

	output_s = "\n".join(output)

	return output_s


def process2(prompt, prompt2, input_text, out, model, indent, temperature, token_limit, retries, state_file, log):
	""" Process some text through the LLM with a prompt. """
	full_input = f"""
{prompt}

{input_text}
"""
	if prompt2:
		full_input += "\n" + prompt2 + "\n"
	return query(full_input, out=out, model=model, indent=indent, temperature=temperature, token_limit=token_limit, retries=retries, state_file=state_file, log=log)


def query(*prompt, out: Optional[IO[str]]=stdout, model: str=default_model, indent="\t", temperature=None, token_limit=None, retries=RETRIES, state_file=None, log=True):  # pylint: disable=unused-argument
	""" Ask the LLM a question. """
	set_opts(vars())
	return retry(query2, retries, *prompt, out=out, log=log)


def query2(*prompt, out: Optional[IO[str]]=stdout, log=True):
	""" Ask the LLM a question. """
	prompt = " ".join(prompt)

	prompt = prompt.rstrip() + "\n"

	# TODO use a system message?

	input_message = {"role": "user", "content": prompt}
	output_message = llm_chat([input_message])
	content = output_message["content"]

	# fix indentation for code
	if opts.indent:
		lines = content.splitlines()
		lines = tab.fix_indentation_list(lines, opts.indent)
		content = "".join(lines)
	if log:
		LOGDIR.mkdir(parents=True, exist_ok=True)
		logfile = base = LOGDIR/(slugify(prompt)[:LOGFILE_NAME_MAX_LEN])
		while logfile.exists():
			time_s = time.strftime("%Y-%m-%dT%H:%M:%S")
			logfile = Path(f"{base}.{time_s}")
		logfile.write_text(content, encoding="utf-8")

	if out:
		out.write(content)
		return ""

	return content


def retry(fn, n_tries, *args, sleep_min=1, sleep_max=2, **kwargs):
	""" Retry a function n_tries times. """
	for i in range(n_tries):
		try:
			return fn(*args, **kwargs)
		except Exception as ex:  # pylint: disable=broad-except
			delay = random.uniform(sleep_min, sleep_max)
			logger.warning("retry: exception, sleeping for %.3f: %s", delay, ex)
			msg = str(ex)
			bad = any(bad_error in msg for bad_error in BAD_ERRORS_NO_RETRY)
			if bad or i == n_tries - 1:
				raise
			time.sleep(delay)
			sleep_min *= 2
			sleep_max *= 2
	return None


#def dict_to_namespace(d):
#	""" Convert a dict to an argparse namespace. """
#	ns = argparse.Namespace()
#	for k, v in d.items():
#		setattr(ns, k, v)
#	return ns


def chat(inp=stdin, out=stdout, model=default_model, fake=False, temperature=None, token_limit=None, retries=RETRIES, state_file=None, auto_save=None):  # pylint: disable=unused-argument
	""" Chat with the LLM, well it inputs a chat file and ouputs the new message to append. """
	set_opts(vars())
	return retry(chat2, retries, inp=inp, out=out)


def chat2(inp=stdin, out=stdout):
	""" Chat with the LLM, well it inputs a chat file and ouputs the new message to append. """
	input_lines = read_utf_replace(inp).splitlines()
	input_messages = lines_to_messages(input_lines)
	response_message = llm_chat(input_messages)
	output_lines = messages_to_lines([response_message])
	out.writelines(output_lines)


def count(inp=stdin, model=default_model):
	""" count tokens in a file """
	set_opts(vars())
	text = read_utf_replace(inp)
	model = opts.model
	if model.startswith("gpt"):
		enc = tiktoken.get_encoding("cl100k_base")
		tokens = enc.encode(text)
		return len(tokens)
	if model.startswith("claude"):
		return claude.count(text)
	raise ValueError(f"unknown model: {model}")


def list_models():
	""" List the available models. """
	for model in models:
		print(model)


if __name__ == "__main__":
	argh.dispatch_commands([chat, query, process, count, list_models])
