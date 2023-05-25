#!/usr/bin/env python3
""" run document processor in a web interface """

import sys
import os
import logging
from pathlib import Path
import re
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

prog_dir = os.environ.get("PROG_DIR", os.getcwd())

mission_file = Path(prog_dir) / "mission.txt"
if mission_file.exists():
	mission_default = mission_file.read_text(encoding="utf-8").rstrip()
else:
	mission_default = ""
mission_placeholder = """Enter your mission here..."""


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
		args=(process.stdout, stdout_lines, print_and_flush, all_lines, None)
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


def process_files(mission, document_files, turbo):
	""" run a file processing command in a web interface """

	# show PATH
	logger.debug("PATH: %r", os.environ["PATH"].split(":"))

	my_opts = opts.copy()

	if turbo:
		my_opts += ["LLM_MODEL=i", "LLM_MODEL_LONG=i+", "OCR_MODEL=i"]

	tmpdir = tempfile.mkdtemp()
	input_dir = Path(tmpdir) / "input"
	os.mkdir(input_dir)

	docs = []

	# write mission text into tmpdir/mission.txt
	mission_file = Path(tmpdir) / "mission.txt"
	mission_file.write_text(mission, encoding="utf-8")

	# put all the document files into the tempdir
	for src_file in document_files:
		src_path = Path(src_file.name)
		basename = src_path.name
		basename_no_stupid_chars = re.sub(r"[^a-zA-Z0-9_.-]", "_", basename)
		path = input_dir / basename_no_stupid_chars
		logger.warning("Copying %r to %r", src_path, path)
		shutil.copy(src_path, str(path))
		src_file.close()
		docs.append(path)

	# chdir to the tempdir
	os.chdir(tmpdir)

	# run command
	status, stdout_lines, stderr_lines, all_lines = run_subprocess(cmd, *opts)

	all_text = "".join(map(lambda d: f"{d['label']}: {d['line']}" if d['label'] else d['line'], all_lines))
	output_text = "".join(stdout_lines)
	error_text = "".join(stderr_lines)

	# chdir to /
	os.chdir("/")

	output_file_md = Path(tmpdir) / "output.md"
	output_file_html = Path(tmpdir) / "output.html"
	output_file_pdf = Path(tmpdir) / "output.pdf"
	output_file_docx = Path(tmpdir) / "output.docx"
	output_file_zip = Path(tmpdir) / "output.zip"

	if output_file_md.exists():
		output_file_text = output_file_md.read_text(encoding="utf-8")
	else:
		output_file_text = ""

#	with open(output_file, "w", encoding="utf-8") as f:
#		f.write(output_text)

	status_str = "Success" if status == 0 else "Error"
	status = f"{status}: {status_str}"

	# TODO display all_lines in HTML with error lines highlighted red or whatever

	output_files = [output_file_zip, output_file_md, output_file_html, output_file_pdf, output_file_docx]
	output_files = [str(f) if f.exists() else None for f in output_files]

	return status, all_text, output_file_text, *output_files


demo = gr.Interface(
	fn=process_files,
	inputs=[
		gr.inputs.Textbox(lines=5, label="Mission", default=mission_default, placeholder=mission_placeholder),
		gr.inputs.File(label="Documents", file_count="multiple"),
		gr.inputs.Checkbox(label="Turbo Mode", default=True),
	],
	outputs=[
		gr.outputs.Textbox(label="Exit Status"),
		gr.outputs.Textbox(label="Messages"),
		gr.outputs.Textbox(label="Output Text"),
		gr.outputs.File(label="Full Output (Zip)"),
		gr.outputs.File(label="Output File (Markdown)"),
		gr.outputs.File(label="Output File (HTML)"),
		gr.outputs.File(label="Output File (PDF)"),
		gr.outputs.File(label="Output File (DOCX)"),
	],
	title=title,
	description=desc,
	allow_flagging='never',
)


if __name__ == "__main__":
	demo.launch(
		server_port=8081,
	)
