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
desc = "Upload documents (PDFs, Word docs, HTML, images, audio, videos, etc.) and enter URLs to download. Alfred will convert them to text, summarize them, and perform tasks based on the documents' contents."

prog_dir = os.environ.get("PROG_DIR", os.getcwd())

default_mission_file = Path(prog_dir) / "mission.txt"
if default_mission_file.exists():
	mission_default = default_mission_file.read_text(encoding="utf-8").rstrip()
else:
	mission_default = ""
topic_default = ""
topic_placeholder = """Enter the topic here..."""
mission_placeholder = """Enter your mission here..."""
urls_placeholder = """Enter URLs of webpages and media here..."""


def process_files(topic, mission, document_files, urls_text, turbo): # pylint: disable=too-many-locals
	""" run a file processing command in a web interface """

	if not topic:
		raise ValueError("Topic is required")
	if not mission:
		raise ValueError("Mission is required")

	if not document_files:
		document_files = []

	# show PATH
	logger.debug("PATH: %r", os.environ["PATH"].split(":"))

	my_opts = opts.copy()

	my_opts += [f"TOPIC={topic}"]

	if turbo:
		my_opts += ["LLM_MODEL=i", "LLM_MODEL_LONG=i+", "OCR_MODEL=i", "IMAGE2TEXT_MODE=fast"]

	# TODO how to delete the tmpdir

	tmpdir = tempfile.mkdtemp(prefix="alfred_")
	input_dir = Path(tmpdir) / "input"
	os.mkdir(input_dir)

	docs = []

	# write mission text into tmpdir/mission.txt
	mission_file = Path(tmpdir) / "mission.1.txt"
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
		# if its an .htm* file
		if re.match(r'.*\.(htm|html)$', basename_no_stupid_chars, re.IGNORECASE):
			# create a .html.url file next to it
			url_file = input_dir / (basename_no_stupid_chars + ".url")
			url_file.write_text(str(path), encoding="utf-8")

	# chdir to the input dir
	os.chdir(tmpdir)
	os.chdir("input")

	all_text = ""

	# download URLs
	urls = re.split(r'\s+', urls_text.strip())
	for url in urls:
		if not url:
			continue
		if not re.match(r'^https?://', url):
			url = "https://" + url

		# get a sorted list of files in the current directory
		files_before = sorted(os.listdir("."))

		status, _stdout_lines, _stderr_lines, all_lines = run_subprocess("yt-dlp", "-i", "-f", "251/bestaudio/best", "-o", "%(title)s.%(ext)s", url)
		all_text += "".join(map(lambda d: f"{d['label']}: {d['line']}" if d['label'] else d['line'], all_lines))
		if status != 0:
			status, _stdout_lines, _stderr_lines, all_lines = run_subprocess("wget", "--trust-server-names", url)
			all_text += "".join(map(lambda d: f"{d['label']}: {d['line']}" if d['label'] else d['line'], all_lines))

		files_after = sorted(os.listdir("."))
		new_files = list(set(files_after) - set(files_before))

		if len(new_files) != 1:
			logger.warning("Expected 1 new file, got %d: %r", len(new_files), new_files)

		# run extension-fix on the new file/s
		status, _stdout_lines, _stderr_lines, all_lines = run_subprocess("extension-fix", "-a", "-v", *new_files)
		all_text += "".join(map(lambda d: f"{d['label']}: {d['line']}" if d['label'] else d['line'], all_lines))

		files_ext_fixed = sorted(os.listdir("."))
		new_files = list(set(files_ext_fixed) - set(files_before))

		for filename in new_files:
			# add a .url file next to it
			url_file = Path(filename + ".url")
			url_file.write_text(url, encoding="utf-8")

	# rename downloaded files
	for filename in os.listdir("."):
		new_filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
		if new_filename != filename:
			os.rename(filename, new_filename)

	# chdir to the tempdir
	os.chdir(tmpdir)

	# run command
	status, _stdout_lines, _stderr_lines, all_lines = run_subprocess(cmd, *my_opts)

	all_text += "".join(map(lambda d: f"{d['label']}: {d['line']}" if d['label'] else d['line'], all_lines))
	# _output_text = "".join(stdout_lines)
	# _error_text = "".join(stderr_lines)

	# chdir to /
	os.chdir("/")

	output_files = list(Path(tmpdir) / f"output.1.{ext}" for ext in ["md", "html", "pdf", "docx"])

	output_file_md = Path(tmpdir) / "output.1.md"


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
		gr.inputs.Textbox(lines=1, label="Topic", default=topic_default, placeholder=topic_placeholder),
		gr.inputs.Textbox(lines=5, label="Mission", default=mission_default, placeholder=mission_placeholder),
		gr.inputs.File(label="Documents", file_count="multiple"),
		gr.inputs.Textbox(lines=5, label="URLs", placeholder=urls_placeholder),
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
