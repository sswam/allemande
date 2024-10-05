#!/usr/bin/env python3
# pyq: process python object notation like jq, using jq
# also supports json, xml, and yaml

# TODO: support more formats, such as csv, tsv, shell env, ini, etc

# usage: pyq <jq args>

# plan:
# 1. load stdin as python object notation
# 2. run jq on it
# 3. convert jq output back to python object notation
# 4. print it

import sys
import json
import subprocess
import argparse
import pprint
import xmltodict
import yaml
import jq

which_jq = "system"  # "system" or "python"

def pyq_subprocess(data, *args):
	proc = subprocess.Popen(['jq'] + list(args), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	proc.stdin.write(json.dumps(data).encode('utf-8'))
	proc.stdin.close()

	jqout = json.loads(proc.stdout.read().decode('utf-8'))
	return jqout

def pyq_subprocess_to_file(data, out_file, *args):
	proc = subprocess.Popen(['jq'] + list(args), stdin=subprocess.PIPE, stdout=out_file)
	proc.stdin.write(json.dumps(data).encode('utf-8'))
	proc.stdin.close()

def pyq_jq(data, jq_program):
	p = jq.compile(jq_program)
	jqout = p.input(data).all()
	return jqout

def pyq(data, jq_program, jq_opts=None):
	if which_jq == "system":
		return pyq_subprocess(data, jq_program, *jq_opts)
	elif jq_opts:
		raise ValueError("jq_opts not supported with python jq")
	else:
		return pyq_jq(data, jq_program)

def pyq_streams(in_file, out_file, jq_program, jq_opts=None, from_="py", to="json", compact=False):
	jq_opts = jq_opts or []

	loader = loaders[from_]
	formatter = formatters[to]

	data = loader(in_file)

	if to == "json" and which_jq == "system":
		# we can output directly to the file,
		# which can give colorized output
		pyq_subprocess_to_file(data, out_file, jq_program, *jq_opts)
	else:
		jqout = pyq(data, jq_program, jq_opts)
		print(formatter(jqout, pretty=not compact), file=out_file)

def load_json(in_file) -> object:
	return json.load(in_file)

def load_python(in_file) -> object:
	# Danger, will robinson!
	return eval(in_file.read())

def format_json(obj, pretty=True) -> str:
	if pretty:
		return json.dumps(obj, indent=4)
	else:
		return json.dumps(obj)

def format_python(obj, pretty=True) -> str:
	if pretty:
		return pprint.pformat(obj, indent=4)
	else:
		return repr(obj)

def load_xml(in_file) -> object:
	return xmltodict.parse(in_file.read())

def format_xml(obj, pretty=True) -> str:
	if not isinstance(obj, dict):
		obj = {"root": {"item": obj}}
	elif len(obj) > 1:
		obj = {"root": obj}
	return xmltodict.unparse(obj, pretty=pretty)

def load_yaml(in_file) -> object:
	return yaml.safe_load(in_file)

def format_yaml(obj, pretty=True) -> str:
	if pretty:
		return yaml.dump(obj, default_flow_style=not pretty, indent=4)
	else:
		return yaml.dump(obj)

loaders = {
	'json': load_json,
	'py': load_python,
	'xml': load_xml,
	'yaml': load_yaml,
}

formatters = {
	'json': format_json,
	'py': format_python,
	'xml': format_xml,
	'yaml': format_yaml,
}

def main():
	parser = argparse.ArgumentParser(description='Process python object notation like jq, using jq')

	# options to read and write either python object notation or json
	# default is py to json
	# option --from to specify input format
	parser.add_argument('--from', dest='from_', default='py', choices=formatters.keys(), help='input format')
	# option --to to specify output format
	parser.add_argument('--to', dest='to', default='json', choices=formatters.keys(), help='output format')
	# option --format to specify both input and output format
	parser.add_argument('--format', dest='format', default=None, choices=formatters.keys(), help='input and output format')
	# option --ugly 
	parser.add_argument('--compact', '-c', action='store_true', help='compact output')
	parser.add_argument('--jq', choices=("system", "python"), help='use system jq or python jq')
	parser.add_argument('jq_program', nargs='?', help='jq program')
	parser.add_argument('jq_opts', nargs=argparse.REMAINDER, help='jq options')

	args = parser.parse_args()

	if args.format is not None:
		args.from_ = args.format
		args.to = args.format

	if not args.jq_program:
		args.jq_program = '.'

	if args.jq:
		global which_jq
		which_jq = args.jq

	pyq_streams(sys.stdin, sys.stdout, args.jq_program, args.jq_opts, args.from_, args.to, compact=args.compact)

if __name__ == '__main__':
	main()
