#!/usr/bin/env python3
""" run document processor in a web interface """

import os
import logging
from pathlib import Path
import re
import tempfile
import shutil

from ucm_gradio import run_subprocess

os.environ["GRADIO_ANALYTICS"] = "False"
import gradio as gr  # pylint: disable=wrong-import-position


os.environ["PATH"] = os.environ.get("PATH", "") + ":" + os.getcwd()

WHISPER = os.environ.get("WHISPER", "whisp")


logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__name__)


cmd = "alfred"
opts = [ "WHISPER="+WHISPER ]
name = "Alfred Document Processor"
title = name
desc = "Upload documents (PDFs, Word docs, etc.). Alfred will convert them to text, summarize them, and perform tasks based on the documents' contents."

prog_dir = os.environ.get("PROG_DIR", os.getcwd())

default_mission_file = Path(prog_dir) / "mission.txt"
if default_mission_file.exists():
	mission_default = default_mission_file.read_text(encoding="utf-8").rstrip()
else:
	mission_default = ""
mission_placeholder = """Enter your mission here..."""


def process_files(mission, document_files, turbo): # pylint: disable=too-many-locals
	""" run a file processing command in a web interface """

	# show PATH
	logger.debug("PATH: %r", os.environ["PATH"].split(":"))

	my_opts = opts.copy()

	if turbo:
		my_opts += ["LLM_MODEL=i", "LLM_MODEL_LONG=i+", "OCR_MODEL=i", "IMAGE2TEXT_MODE=fast"]

	# TODO how to delete the tmpdir

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
	status, _stdout_lines, _stderr_lines, all_lines = run_subprocess(cmd, *my_opts)

	all_text = "".join(map(lambda d: f"{d['label']}: {d['line']}" if d['label'] else d['line'], all_lines))
	# _output_text = "".join(stdout_lines)
	# _error_text = "".join(stderr_lines)

	# chdir to /
	os.chdir("/")

	output_files = list(Path(tmpdir) / f"output.{ext}" for ext in ["zip", "md", "html", "pdf", "docx"])

	output_file_md = Path(tmpdir) / "output.md"


	if output_file_md.exists():
		output_file_text = output_file_md.read_text(encoding="utf-8")
	else:
		output_file_text = ""

	status_str = "Success" if status == 0 else "Error"
	status = f"{status}: {status_str}"

	# TODO display all_lines in HTML with error lines highlighted red or whatever

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
