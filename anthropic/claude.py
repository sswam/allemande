#!/usr/bin/env python3

""" A command line interface to the anthropic API """

import sys
import os
import logging
import asyncio
import json
from typing import Optional
import argh
import anthropic

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

DEFAULT_TEMPERATURE = 1.0
TOKEN_LIMIT = 9216
TOKEN_LIMIT_100K = 100000  # 100000  # exactly?
# TODO does this vary for claude-instant-v1 and other models?  It does with 100K clearly
MODEL_DEFAULT = "claude-v1"
MODEL_INSTANT = "claude-instant-v1"
MODEL_100K = "claude-v1-100k"
MODEL_INSTANT_100K = "claude-instant-v1-100k"
# see also: https://console.anthropic.com/docs/api/reference

def show_args(*args, **kwargs):
	""" Show the arguments """
	# use yaml
	import yaml
	logger.warning("args:\n%s", yaml.dump(args))
	logger.warning("kwargs:\n%s", yaml.dump(kwargs))

def count(message, add_prompts=True):
	""" Count the number of tokens in a message """
	if add_prompts:
		message=f"{anthropic.HUMAN_PROMPT} {message}{anthropic.AI_PROMPT}"
	num_tokens = anthropic.count_tokens(message)
	return num_tokens

def response_completion(response):
	""" Extract the completion from a response """
	logger.debug("Response: %s", json.dumps(response))
	completion = response.get("completion")
	if completion.startswith(" "):
		completion = completion[1:]
	return completion

def stream_completion(data, completion, out):
	""" Extract the completion from a stream response """
	logger.debug("Response data: %s", json.dumps(data))
	part = data.get("completion")
	if part.startswith(" "):
		part = part[1:]
	if part.startswith(completion):
		new = part[len(completion):]
		completion = part
		print(new, file=out, end="", flush=True)
	else:
		logger.warning("\nUnexpected part: %s", part)
		completion = part
		print(part, file=out, end="", flush=True)
	return completion

def message_to_string(message):
	""" Convert a message object to a string """
	if message["role"] in ["system", "user"]:
		prompt = anthropic.HUMAN_PROMPT
	elif message["role"] == "assistant":
		prompt = anthropic.AI_PROMPT
	else:
		raise ValueError(f"unknown role: {message['role']}")
	return f"{prompt} {message['content']}"

def chat_claude(messages, model=None, token_limit: int = None, temperature=None, streaming=False, _async=False):
	""" Chat with claude """
	real_token_limit = TOKEN_LIMIT_100K if "100k" in model else TOKEN_LIMIT
	logger.debug("model: %s", model)
	logger.debug("real_token_limit: %s", real_token_limit)
	if model is None:
		model = MODEL_DEFAULT
	if token_limit is None:
		token_limit = real_token_limit
	if temperature is None:
		temperature = DEFAULT_TEMPERATURE
	message_strings = map(message_to_string, messages)
	prompt = "".join(message_strings) + anthropic.AI_PROMPT
	prompt_tokens = anthropic.count_tokens(prompt)
	# max_possible_tokens_to_sample = min(real_token_limit - prompt_tokens, TOKEN_LIMIT)  # gen tokens is limited to 9216?
	max_possible_tokens_to_sample = real_token_limit - prompt_tokens
	if max_possible_tokens_to_sample <= 0:
		raise ValueError(f"[context_length_exceeded] Prompt is too long: {prompt_tokens} tokens > {real_token_limit}")
	if token_limit > max_possible_tokens_to_sample:
		token_limit = max_possible_tokens_to_sample
		logger.debug("Reducing token_limit to %d", token_limit)
	c = anthropic.Client(os.environ["ANTHROPIC_API_KEY"])
	fn = c.completion_stream if streaming else c.completion
	if _async:
		fn = c.acompletion_stream if streaming else c.acompletion
	else:
		fn = c.completion_stream if streaming else c.completion
#	show_args(
#		prompt=prompt,
#		stop_sequences=[anthropic.HUMAN_PROMPT],
#		model=model,
#		max_tokens_to_sample=token_limit,
#		streaming=streaming,
#		temperature=temperature,
#	)
	response = fn(
		prompt=prompt,
		stop_sequences=[anthropic.HUMAN_PROMPT],
		model=model,
		max_tokens_to_sample=token_limit,
		streaming=streaming,
		temperature=temperature,
	)
	return response

def complete(message, **kwargs):
	""" Complete a message """
	messages = [ { "role": "user", "content": message, }, ]
	return chat_claude(messages, **kwargs)

async def async_query(message, debug=False, **kwargs):
	""" Asyncronous access to the anthropic API """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	response = await complete(message, _async=True, **kwargs)
	return response_completion(response)

async def async_stream(message, out=sys.stdout, debug=False, **kwargs):
	""" Asyncronous streaming access to the anthropic API """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	response = await complete(message, streaming=True, _async=True, **kwargs)
	completion = ""
	async for data in response:
		completion = stream_completion(data, completion, out)
	# return completion

def default_token_limit_for_model(model: str):
	return TOKEN_LIMIT_100K if "100k" in model else TOKEN_LIMIT

def query(message, model=MODEL_DEFAULT, debug=False, token_limit: Optional[int] = None, temperature=DEFAULT_TEMPERATURE):
	""" Syncronous access to the anthropic API """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	token_limit = default_token_limit_for_model(model) if token_limit is None else token_limit
	response = complete(message, model=model, token_limit=token_limit, temperature=temperature)
	return response_completion(response)

def stream(message, model=MODEL_DEFAULT, out=sys.stdout, debug=False, token_limit: Optional[int] = None, temperature=DEFAULT_TEMPERATURE):
	""" Streaming access to the anthropic API """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	token_limit = default_token_limit_for_model(model) if token_limit is None else token_limit
	response = complete(message, model=model, token_limit=token_limit, streaming=True, temperature=temperature)
	completion = ""
	for data in response:
		completion = stream_completion(data, completion, out)
	# return completion

def aquery(message, model=MODEL_DEFAULT, debug=False, token_limit: Optional[int] = None, temperature=DEFAULT_TEMPERATURE):
	""" Asyncronous access to the anthropic API - argh wrapper """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	token_limit = default_token_limit_for_model(model) if token_limit is None else token_limit
	response = asyncio.run(async_query(message, model=model, debug=debug, token_limit=token_limit, temperature=temperature))
	return response

def astream(message, model=MODEL_DEFAULT, out=sys.stdout, debug=False, token_limit: Optional[int] = None, temperature=DEFAULT_TEMPERATURE):
	""" Asyncronous streaming access to the anthropic API - argh wrapper """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	token_limit = default_token_limit_for_model(model) if token_limit is None else token_limit
	asyncio.run(async_stream(message, model=model, out=out, debug=debug, token_limit=token_limit, temperature=temperature))

if __name__ == "__main__":
	argh.dispatch_commands([query, stream, aquery, astream, count])
