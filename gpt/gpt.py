#!/usr/bin/env python3
""" gpt.py: a simple wrapper for the OpenAI ChatGPT API """

# TODO create compatible libraries for other APIs in future

from sys import stdin, stdout
import os
import logging
import re
from typing import Optional, IO
from argh import dispatch_commands

import openai

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
}

# default is $GPT_MODEL or first model in the dict

first_model = next(iter(models.keys()))
default_model = os.environ.get("GPT_MODEL", first_model)

ALLOWED_ROLES = ["user", "assistant", "system"]

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


def gpt(messages, model=default_model, fake=False):
	""" Send a list of messages to the model, and return the response. """

	logger.debug("gpt: input: %r", messages)

	if fake:
		completion = fake_completion
	else:
		completion = openai.ChatCompletion.create(
			model=model,
			messages=messages
		)

	logger.debug("gpt: completion: %s", completion)

	output_message = completion['choices'][0]['message']

	logger.debug("gpt: output message: %s", output_message)

	return output_message


def split_message_line(message, allowed_roles=None):
	""" Split a message into a role and content. """

	try:
		role, message = message.split(":", 1)
	except ValueError as e:
		raise ValueError(f"invalid message, missing role: {message}") from e

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


def process(prompt: str, inp: IO[str]=stdin, out: IO[str]=stdout, prompt2: Optional[str]=None, model: str=default_model):
	""" Process some text through GPT with a prompt. """
	model = get_model_by_abbrev(model)
	prompt = prompt.rstrip()
	input_text = inp.read().rstrip()
	if prompt2:
		prompt2 = prompt2.rstrip()

	full_input = f"""
{prompt.rstrip()}

{input_text.rstrip()}
"""

	if prompt2:
		full_input += "\n" + prompt2

	# TODO use a system message?

	input_message = {"role": "user", "content": full_input}

	output_message = gpt([input_message], model=model)

	content = output_message["content"]

	# TODO fix indentation?

	out.write(content)


def list_models():
	""" List the available models. """
	for model in models:
		print(model)


def get_model_by_abbrev(model):
	""" If the model is an abbreviation, expand it. """
	abbrev_models = [k for k, v in models.items() if v.get("abbrev") == model]
	if len(abbrev_models) == 1:
		model = abbrev_models[0]
	return model


def chat(inp=stdin, out=stdout, model=default_model, fake=False):
	""" The main function, called when this module is run as a script. """
	model = get_model_by_abbrev(model)
	input_lines = inp.readlines()
	input_messages = lines_to_messages(input_lines)
	response_message = gpt(input_messages, fake=fake, model=model)
	output_lines = messages_to_lines([response_message])
	out.writelines(output_lines)


if __name__ == "__main__":
	dispatch_commands([chat, process, list_models])
