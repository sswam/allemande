#!/usr/bin/env python3
""" gpt.py: a simple wrapper for the OpenAI ChatGPT API and also Anthropic's Claude """

# TODO create compatible libraries for other APIs in future

from sys import stdin, stdout
import os
import logging
import re
from typing import Optional, IO
from math import inf

from argh import dispatch_commands

import openai

import tab
import claude

# import json

logger = logging.getLogger(__name__)

# settngs

models = {
	"gpt-3.5-turbo": {
		"abbrev": "3+",
		"description": "Most capable GPT-3.5 model and optimized for chat at 1/10th the cost of text-davinci-003. Will be updated with our latest model iteration.",
		"cost": 0.002,
	},
	"gpt-4": {
		"abbrev": "4",
		"description": "More capable than any GPT-3.5 model, able to do more complex tasks, and optimized for chat. Will be updated with our latest model iteration.",
		"cost": 0.03,
	},
	"gpt-4-32k": {
		"abbrev": "4+",
		"description": "Same capabilities as the base gpt-4 mode but with 4x the context length. Will be updated with our latest model iteration.",
		"cost": 0.06,
	},
	"gpt-3.5-turbo-0301": {
		"description": "Snapshot of gpt-3.5-turbo from March 1st 2023. Unlike gpt-3.5-turbo, this model will not receive updates, and will only be supported for a three month period ending on June 1st 2023.",
		"cost": 0.002,
	},
	"gpt-4-0314": {
		"description": "Snapshot of gpt-4 from March 14th 2023. Unlike gpt-4, this model will not receive updates, and will only be supported for a three month period ending on June 14th 2023.",
		"cost": 0.03,
	},
	"gpt-4-32k-0314": {
		"description": "Snapshot of gpt-4-32 from March 14th 2023. Unlike gpt-4-32k, this model will not receive updates, and will only be supported for a three month period ending on June 14th 2023.",
		"cost": 0.06,
	},
	"claude-v1": {
		"abbrev": "c",
		"description": "Anthropic's Claude is an AI assistant with a focus on safety and Constitutional AI. It is trained to be helpful, harmless, and honest. This is our largest model, ideal for a wide range of more complex tasks.",
		"cost": 0.0  # at least for now!
	},
	"claude-v1.0": {
		"description": "An earlier version of claude-v1.",
		"cost": 0.0
	},
	"claude-v1.2": {
		"description": "An improved version of claude-v1. It is slightly improved at general helpfulness, instruction following, coding, and other tasks. It is also considerably better with non-English languages. This model also has the ability to role play (in harmless ways) more consistently, and it defaults to writing somewhat longer and more thorough responses.",
		"cost": 0.0
	},
	"claude-v1.3": {
		"description": "A significantly improved version of claude-v1. Compared to claude-v1.2, it's more robust against red-team inputs, better at precise instruction-following, better at code, and better and non-English dialogue and writing.",
		"cost": 0.0
	},
	"claude-instant-v1": {
		"abbrev": "i",
		"description": "A smaller model with far lower latency, sampling at roughly 40 words/sec! Its output quality is somewhat lower than claude-v1 models, particularly for complex tasks. However, it is much less expensive and blazing fast. We believe that this model provides more than adequate performance on a range of tasks including text classification, summarization, and lightweight chat applications, as well as search result summarization. Using this model name will automatically switch you to newer versions of claude-instant-v1 as they are released.",
		"cost": 0.0
	},
	"claude-instant-v1.0": {
		"description": "Current default for claude-instant-v1.",
		"cost": 0.0
	}
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

# default is $GPT_MODEL or first model in the dict

first_model = next(iter(models.keys()))
default_model = os.environ.get("GPT_MODEL", first_model)

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

def chat_claude(*args, **kwargs):
	response = claude.chat_claude(*args, **kwargs)
	completion = claude.response_completion(response)
	message = { "role": "assistant", "content": completion }
	return message

def llm_chat(messages, model=default_model, fake=False, temperature=None, token_limit=None):
	""" Send a list of messages to the model, and return the response. """
	logger.debug("llm_chat: input: %r", messages)

	if fake:
		completion = fake_completion
	elif model.startswith("claude"):
		return chat_claude(messages, model=model, temperature=temperature, token_limit=token_limit)
	elif model.startswith("gpt"):
		return chat_gpt(messages, model=model, temperature=temperature, token_limit=token_limit)
	else:
		raise ValueError(f"unknown model: {model}")

	logger.debug("llm_chat: output message: %s", output_message)

def chat_gpt(messages, model=default_model, temperature=None, token_limit=None):  # 0.9, token_limit=150, top_p=1, frequency_penalty=0, presence_penalty=0, stop=["\n\n"]):
	if temperature is None:
		temperature = DEFAULT_TEMPERATURE
	if token_limit is None:
		token_limit = TOKEN_LIMIT
	completion = openai.ChatCompletion.create(
		model=model,
		messages=messages
	)

	logger.debug("gpt: completion: %s", completion)

	output_message = completion['choices'][0]['message']

	return output_message


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


def process(prompt: str, inp: IO[str]=stdin, out: IO[str]=stdout, prompt2: Optional[str]=None, model: str=default_model, indent="\t", temperature=None, token_limit=None):
	""" Process some text through GPT with a prompt. """
	prompt = prompt.rstrip()
	input_text = inp.read().rstrip()
	if prompt2:
		prompt2 = prompt2.rstrip()

	full_input = f"""
{prompt}

{input_text}
"""

	if prompt2:
		full_input += "\n" + prompt2 + "\n"

	return query(full_input, out=out, model=model, indent=indent, temperature=temperature, token_limit=token_limit)


def query(prompt: str, out: IO[str]=stdout, model: str=default_model, indent="\t", temperature=None, token_limit=None):
	""" Ask GPT a question. """

	model = get_model_by_abbrev(model)

	prompt = prompt.rstrip() + "\n"

	# TODO use a system message?

	input_message = {"role": "user", "content": prompt}
	output_message = llm_chat([input_message], model=model)
	content = output_message["content"]

	# fix indentation for code
	if indent:
		lines = content.splitlines()
		lines = tab.fix_indentation_list(lines, indent)
		content = "".join(lines)

	out.write(content)


def chat(inp=stdin, out=stdout, model=default_model, fake=False, temperature=None, token_limit=None):
	""" Chat with GPT. """
	model = get_model_by_abbrev(model)
	input_lines = inp.readlines()
	input_messages = lines_to_messages(input_lines)
	response_message = llm_chat(input_messages, fake=fake, model=model, temperature=temperature, token_limit=token_limit)
	output_lines = messages_to_lines([response_message])
	out.writelines(output_lines)


def list_models():
	""" List the available models. """
	for model in models:
		print(model)


if __name__ == "__main__":
	dispatch_commands([chat, query, process, list_models])
