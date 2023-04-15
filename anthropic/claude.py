#!/usr/bin/env python3

""" A command line interface to the anthropic API """

import sys
import os
import logging
import asyncio
import json
import argh
import anthropic

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

max_tokens = 9216

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

def complete(message, max_tokens_to_sample: int = 10000, model="claude-v1.3", streaming=False, _async=False):
	""" Complete a message """
	prompt=f"{anthropic.HUMAN_PROMPT} {message}{anthropic.AI_PROMPT}"
	prompt_tokens = anthropic.count_tokens(prompt)
	max_possible_tokens_to_sample = max_tokens - prompt_tokens
	if max_possible_tokens_to_sample <= 0:
		logger.warning("Prompt is too long: %d tokens", prompt_tokens)
		return ""
	if max_tokens_to_sample > max_possible_tokens_to_sample:
		max_tokens_to_sample = max_possible_tokens_to_sample
		logger.debug("Reducing max_tokens_to_sample to %d", max_tokens_to_sample)
	c = anthropic.Client(os.environ["ANTHROPIC_API_KEY"])
	fn = c.completion_stream if streaming else c.completion
	if _async:
		fn = c.acompletion_stream if streaming else c.acompletion
	else:
		fn = c.completion_stream if streaming else c.completion
	response = fn(
		prompt=prompt,
		stop_sequences=[anthropic.HUMAN_PROMPT],
		model=model,
		max_tokens_to_sample=max_tokens_to_sample,
		streaming=streaming,
	)
	return response

def query(message, max_tokens_to_sample: int = 10000, model="claude-v1.3", debug=False):
	""" Syncronous access to the anthropic API """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	response = complete(message, max_tokens_to_sample=max_tokens_to_sample, model=model)
	return response_completion(response)

def stream(message, max_tokens_to_sample: int = 10000, model="claude-v1.3", out=sys.stdout, debug=False):
	""" Streaming access to the anthropic API """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	response = complete(message, max_tokens_to_sample=max_tokens_to_sample, model=model, streaming=True)
	completion = ""
	for data in response:
		completion = stream_completion(data, completion, out)
	# return completion

async def async_query(message, max_tokens_to_sample: int = 10000, model="claude-v1.3", debug=False):
	""" Asyncronous access to the anthropic API """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	response = await complete(message, max_tokens_to_sample=max_tokens_to_sample, model=model, _async=True)
	return response_completion(response)

async def async_stream(message, max_tokens_to_sample: int = 10000, model="claude-v1.3", out=sys.stdout, debug=False):
	""" Asyncronous streaming access to the anthropic API """
	if debug:
		logging.basicConfig(level=logging.DEBUG)
	response = await complete(message, max_tokens_to_sample=max_tokens_to_sample, model=model, streaming=True, _async=True)
	completion = ""
	async for data in response:
		completion = stream_completion(data, completion, out)
	# return completion

def aquery(message, max_tokens_to_sample: int = 10000, model="claude-v1.3", debug=False):
	""" Asyncronous access to the anthropic API - argh wrapper """
	response = asyncio.run(async_query(message, max_tokens_to_sample=max_tokens_to_sample, model=model, debug=debug))
	return response

def astream(message, max_tokens_to_sample: int = 10000, model="claude-v1.3", out=sys.stdout, debug=False):
	""" Asyncronous streaming access to the anthropic API - argh wrapper """
	response = asyncio.run(async_stream(message, max_tokens_to_sample=max_tokens_to_sample, model=model, out=out, debug=debug))
	return response

if __name__ == "__main__":
	argh.dispatch_commands([query, stream, aquery, astream, count])
