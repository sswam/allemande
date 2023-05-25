#!/usr/bin/env python3
""" run document processor in a web interface """

import sys
import os
import logging
from pathlib import Path
import tempfile
import subprocess
import shutil
import threading

from functools import partial

os.environ["PATH"] = os.environ.get("PATH", "") + ":" + os.getcwd()

WHISPER = os.environ.get("WHISPER", "whisp")

os.environ["GRADIO_ANALYTICS"] = "False"
import gradio as gr

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__name__)

cmd = "alfred"
opts = [ "WHISPER="+WHISPER ]
name = "Alfred Document Processor"
title = name
desc = "Upload documents (PDFs, Word docs, etc.). Alfred will convert them to text, summarize them, and perform tasks based on the documents' contents."

def print_and_flush(*args, file=sys.stdout, **kwargs):
	print(*args, file=file, flush=True, **kwargs)

def print_and_save_stream(stream, lines=None, printer=print, all_lines=None, label=None):
	for line in iter(stream.readline, ''):
		if lines is not None:
			lines.append(line)
		if all_lines is not None:
			all_lines.append({"label":label, "line":line})
		if printer is not None:
			printer(line, end='')

def run_subprocess(cmd, *args, **kwargs):
	# set environment variables
	env = os.environ.copy()
	for k, v in kwargs.items():
		env[k] = v

	cmd = [cmd, *args]

	stdout_lines = []
	stderr_lines = []
	all_lines = []

	process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
	thread_out = threading.Thread(
		target=print_and_save_stream,
		args=(process.stdout, stdout_lines, print_and_flush, all_lines, "out")
	)
	thread_err = threading.Thread(
		target=print_and_save_stream,
		args=(process.stderr, stderr_lines, partial(print_and_flush, file=sys.stderr), all_lines, "err")
	)
	thread_out.start()
	thread_err.start()
	thread_out.join()
	thread_err.join()
	exit_code = process.wait()
	return exit_code, stdout_lines, stderr_lines, all_lines

def process_files(document_files, mission):
	""" run a file processing command in a web interface """

	# show PATH
	logger.debug("PATH: %r", os.environ["PATH"].split(":"))

	tmpdir = tempfile.mkdtemp()
	input_dir = Path(tmpdir) / "input"
	os.mkdir(input_dir)

	docs = []

	# put all the document files into the tempdir
	for src_file in document_files:
		src_path = Path(src_file.name)
		basename = src_path.name
		path = input_dir / basename
		logger.warning("Copying %r to %r", src_path, path)
		shutil.copy(src_path, str(path))
		src_file.close()
		docs.append(path)

	# chdir to the tempdir
	os.chdir(tmpdir)

	# run command
	status, stdout_lines, stderr_lines, all_lines = run_subprocess(cmd, *opts)

	all_text = "".join(map(lambda d: f"{d['label']}: {d['line']}", all_lines))
	output_text = "".join(stdout_lines)
	error_text = "".join(stderr_lines)

	# chdir to /
	os.chdir("/")

	output_file = Path(tmpdir) / "output.md"

	output_file_text = output_file.read_text(encoding="utf-8")

#	with open(output_file, "w", encoding="utf-8") as f:
#		f.write(output_text)

	status_str = "Success" if status == 0 else "Error"
	status = f"{status}: {status_str}"

	# TODO display all_lines in HTML with error lines highlighted red or whatever

	return status, all_text, output_file_text, str(output_file)


demo = gr.Interface(
	fn=process_files,
	inputs=[
		gr.inputs.File(label="Documents", file_count="multiple"),
		gr.inputs.Textbox(lines=5, label="Mission"),
	],
	outputs=[
		gr.outputs.Textbox(label="Exit Status"),
		gr.outputs.Textbox(label="Messages"),
		gr.outputs.Textbox(label="Output Text"),
		gr.outputs.File(label="Output File"),
	],
	title=title,
	description=desc,
	allow_flagging='never',
)


if __name__ == "__main__":
	demo.launch(
		server_port=8080,
	)
