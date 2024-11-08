#!/usr/bin/env python3-allemande

""" A command line interface to the anthropic API """

import sys
import os
import logging
import asyncio
import json
import copy
from typing import Optional
import argh
from anthropic import Anthropic, AsyncAnthropic, HUMAN_PROMPT, AI_PROMPT

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

logging.basicConfig(level=logging.INFO)

DEFAULT_TEMPERATURE = 0.3
# TOKEN_LIMIT = 9216
# TOKEN_LIMIT = 100000  # exactly?
TOKEN_LIMIT = 8192
TOKEN_LIMIT_HAIKU = 4096
MODEL_DEFAULT = "claude-3-5-sonnet-latest"
MODEL_INSTANT = "claude-3-haiku-20240307"
# previous model names: "claude-v1" "claude-v1-100k" "claude-instant-v1-100k"
# see also: https://console.anthropic.com/docs/api/reference

client = Anthropic()  # uses os.environ["ANTHROPIC_API_KEY"]
client_async = AsyncAnthropic()

def show_args(*args, **kwargs):
	""" Show the arguments """
	# use yaml
	import yaml
	logger.warning("args:\n%s", yaml.dump(args))
	logger.warning("kwargs:\n%s", yaml.dump(kwargs))

def count(message, add_prompts=True):
	""" Count the number of tokens in a message """
	if add_prompts:
		message=f"{HUMAN_PROMPT} {message}{AI_PROMPT}"
	num_tokens = client.count_tokens(message)
	return num_tokens

def response_completion(response):
	""" Extract the completion from a response """
	completion = response.content[0].text
	logger.debug("Response: %s", json.dumps({"model":response.model, "stop_reason":response.stop_reason, "completion":completion}))
	if completion.startswith(" "):
		completion = completion[1:]
	return completion

def stream_completion(data, out, first=False):
	""" Extract the completion from a stream response """
#	logger.debug("Response data: %s", json.dumps({"model":data.model, "stop_reason":data.stop_reason, "completion":data}))
	part = data
	if first and part.startswith(" "):
		part = part[1:]
	print(part, file=out, end="", flush=True)

def message_to_string(message):
	""" Convert a message object to a string """
	if message["role"] in ["system", "user"]:
		prompt = HUMAN_PROMPT
	elif message["role"] == "assistant":
		prompt = AI_PROMPT
	else:
		raise ValueError(f"unknown role: {message['role']}")
	return f"{prompt} {message['content']}"

def chat_claude(messages, model=None, token_limit: int = None, temperature=None, stream=False, _async=False):
	""" Chat with claude """
	# TODO clean up this code, if indeed all models are 100K now; test with claude-1 also I guess
	real_token_limit = TOKEN_LIMIT_HAIKU if model == MODEL_INSTANT else TOKEN_LIMIT
	logger.debug("model: %s", model)
	logger.debug("real_token_limit: %s", real_token_limit)
	if model is None:
		model = MODEL_DEFAULT
	if token_limit is None:
		token_limit = real_token_limit
	if token_limit > real_token_limit:
		token_limit = real_token_limit
	if temperature is None:
		temperature = DEFAULT_TEMPERATURE
	# message_strings = map(message_to_string, messages)
	messages = copy.deepcopy(messages)
	for m in messages:
		if not isinstance(m["content"], str):
			continue
		m["content"] = [
			{
				"type": "text",
				"text": m["content"],
			}
		]
#	prompt = "".join(message_strings) + AI_PROMPT
#	prompt_tokens = client.count_tokens(prompt)
#	# max_possible_tokens_to_sample = min(real_token_limit - prompt_tokens, TOKEN_LIMIT)  # gen tokens is limited to 9216?
#	max_possible_tokens_to_sample = real_token_limit - prompt_tokens
#	if max_possible_tokens_to_sample <= 0:
#		raise ValueError(f"[context_length_exceeded] Prompt is too long: {prompt_tokens} tokens > {real_token_limit}")
#	if token_limit > max_possible_tokens_to_sample:
#		token_limit = max_possible_tokens_to_sample
#		logger.debug("Reducing token_limit to %d", token_limit)
	c = client_async if _async else client
#	show_args(
#		prompt=prompt,
#		stop_sequences=[HUMAN_PROMPT],
#		model=model,
#		max_tokens_to_sample=token_limit,
#		stream=stream,
#		temperature=temperature,
#	)
	if stream:
		fn = c.messages.stream
	else:
		fn = c.messages.create
	response = fn(
		messages=messages,
		stop_sequences=[HUMAN_PROMPT],
		model=model,
		max_tokens=token_limit,
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
	# TODO output can block and it should be async too, but this is just a demo
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	stream = complete(message, stream=True, _async=True, **kwargs)
	first = True
	async with stream as s:
		async for data in s.text_stream:
			stream_completion(data, out, first=first)
			first = False
	print("", file=out, flush=True)

def query(message, model=MODEL_DEFAULT, debug=False, token_limit: Optional[int] = None, temperature=DEFAULT_TEMPERATURE):
	""" Syncronous access to the anthropic API """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	response = complete(message, model=model, token_limit=token_limit, temperature=temperature)
	return response_completion(response)

def stream(message, model=MODEL_DEFAULT, out=sys.stdout, debug=False, token_limit: Optional[int] = None, temperature=DEFAULT_TEMPERATURE):
	""" Streaming access to the anthropic API """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	stream = complete(message, model=model, token_limit=token_limit, stream=True, temperature=temperature)
	first = True
	with stream as s:
		for data in s.text_stream:
			stream_completion(data, out, first=first)
			first = False
	print("", file=out, flush=True)

def aquery(message, model=MODEL_DEFAULT, debug=False, token_limit: Optional[int] = None, temperature=DEFAULT_TEMPERATURE):
	""" Asyncronous access to the anthropic API """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	response = asyncio.run(async_query(message, model=model, debug=debug, token_limit=token_limit, temperature=temperature))
	return response

def astream(message, model=MODEL_DEFAULT, out=sys.stdout, debug=False, token_limit: Optional[int] = None, temperature=DEFAULT_TEMPERATURE):
	""" Asyncronous streaming access to the anthropic API """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	asyncio.run(async_stream(message, model=model, out=out, debug=debug, token_limit=token_limit, temperature=temperature))

if __name__ == "__main__":
	argh.dispatch_commands([query, stream, aquery, astream, count])
