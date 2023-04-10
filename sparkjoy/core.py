#!/usr/bin/env python3

# Electric Barbarella v3 - core

import sys
import os
import yaml
import transformers
from collections import namedtuple

import argh
# import sh

os.environ["TRANSFORMERS_OFFLINE"] = "1"


# look for models at /opt/models/llm by default

class LLMModelServer:
	# types?
	model = None
	tokenizer = None

	def __init__(self):
		self.model = self.load_model()
		self.cow = 123

	load_model_default_args = {
#		"path": "EleutherAI/gpt-neo-2.7B",
		"path": os.environ.get("LLM_MODEL_DIR", "/opt/models/llm"),
	}


	def load_model(name=None, **kwargs):
		kwargs.extend(self.load_model_default_args)
		print(kwargs)
		return

		kwargs["name"] = name
		o = namedtuple("args", kwargs.keys())(*kwargs.values())
		o.path = os.path.join(o.path, o.name)

		self.tokenizer = transformers.LlamaTokenizer.from_pretrained(o.path)
		self.model = transformers.LlamaForCausalLM.from_pretrained(
			o.path,
			device_map=device_map,
			#device_map="auto",
			torch_dtype=torch.float16,
			#max_memory = {0: "14GB", 1: "14GB", 2: "14GB", 3: "14GB",4: "14GB",5: "14GB",6: "14GB",7: "14GB"},
			max_memory = {0: "20GB"},
			load_in_8bit=o["load_in_8bit"],
			# load_in_8bit_threshold=0.8,
			low_cpu_mem_usage=True,
			cache_dir="cache"
		).cuda()

		model.tokenizer = tokenizer

		return model


	def request_loop(self):
		# Main loop
		pass
		# calls: 

	def read_headers(self):
		# Read headers
		pass

	def read_body(self, content_length):
		# Read body, ideally streaming?
		pass

	def handle_request(self, request):
#	def process_request(request):
		# Handle request
		# Process the request and generate a response using your AI LLM model
		# Example: response = model.generate(request['input_text'])
		# TODO
		response = "blah blah"
		return response

	def send_response(self, response):
		# Send response
		pass


def load_model(model_path, eight_bit=False, device_map="auto"):
	# Load your AI LLM model here and allocate VRAM
	# For example, using TensorFlow or PyTorch
	if device_map == "zero":
		device_map = "balanced_low_0"

	tokenizer = transformers.LlamaTokenizer.from_pretrained(model_path)

	model = transformers.LlamaForCausalLM.from_pretrained(
		model_path,
		device_map=device_map,
		#device_map="auto",
		torch_dtype=torch.float16,
		#max_memory = {0: "14GB", 1: "14GB", 2: "14GB", 3: "14GB",4: "14GB",5: "14GB",6: "14GB",7: "14GB"},
		max_memory = {0: "20GB"},
		load_in_8bit=eight_bit,
		# load_in_8bit_threshold=0.8,
		low_cpu_mem_usage=True,
		cache_dir="cache"
	).cuda()

	model.tokenizer = tokenizer

	return model

def process(model, inp, out):
	headers = read_headers()
	read_input(headers)
#	model.

def main2():
	model = load_model(model_path, load_in_8bit=load_in_8bit)
	while True:
		process(sys.stdin, sys.stdout)


def main3():
	# TODO parse args using argh

	model = load_model()

	while not sys.stdin.closed:
		# Read headers
		headers = []
		while (line := sys.stdin.readline().strip()) != "":
			headers.append(line)

		if not headers:
			break

		# Parse YAML headers, case insensitive
		headers = "\n".join(headers)
		metadata = {k.lower(): v for k, v in yaml.safe_load(headers).items()}

		# Read content_length bytes from stdin
		content_length = int(metadata["content-length"])
		input_text = sys.stdin.read(content_length)

		# Process request and generate response
		request = {"input_text": input_text}
		response = process_request(request)

		# Print response metadata and body
		response_metadata = {"content-length": len(response)}
		response_metadata_yaml = yaml.dump(response_metadata)
		print(response_metadata_yaml)
		print(response)

#if __name__ == "__main__":
#	main()

def parse_args():
	pass
	# use argh
	

if __name__ == "__main__":
	server = LLMModelServer()
	server.request_loop()

# TODO handle EOFError to exit cleanly?


# TODO test load_in_8bit with load_in_8bit_threshold
# TODO accept all options as arguments, or via a yaml file?
# TODO make sure I fully understand all the options we are using there, e.g. device_map, max_memory, load_in_8bit, low_cpu_mem_usage, cache_dir ...
