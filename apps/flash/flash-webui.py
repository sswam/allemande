#!/usr/bin/env python3
""" run flash in a web interface """

# TODO other data types:
# text, image, audio, video, sketchpad, or label
# TODO get GPT-4 to generate custom Gradio UIs for different tools

import os
import logging
import tempfile
from pathlib import Path

from ucm_gradio import run_subprocess

os.environ["GRADIO_ANALYTICS"] = "False"
import gradio as gr   # pylint: disable=wrong-import-position


os.environ["PATH"] = os.environ.get("PATH", "") + ":" + os.getcwd()

WHISPER = os.environ.get("WHISPER", "whisp")


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


cmd = "flash-cached"
opts = [ "WHISPER="+WHISPER ]
name = "Video to Flashcards"
title = os.environ.get("RUNNER_TITLE", f"{name}")
desc = os.environ.get("RUNNER_DESC", "Enter the URL of a short video (<15m). The program will try to summarize the video, and produce flashcards.")


def process_text(video_url):
	""" run a text processing command in a web interface """

	logger.info("Processing: %r", video_url)

	# show PATH
	logger.debug("PATH: %r", os.environ["PATH"].split(":"))

	status, stdout_lines, stderr_lines, _all_lines = run_subprocess(cmd, video_url, *opts)

	output_text = "".join(stdout_lines)
	error_text = "".join(stderr_lines)

	tmpdir = tempfile.mkdtemp()
	output_file = Path(tmpdir) / "post.txt"

	# TODO how to delete the tmpdir

	with open(output_file, "w", encoding="utf-8") as f:
		f.write(output_text)

	status_str = "Success" if status == 0 else "Error"

	status = f"{status}: {status_str}"

	return status, error_text, output_text, str(output_file)

demo = gr.Interface(
	fn=process_text,
	inputs=[
		gr.Textbox(label="Video URL",
		lines=1,
		placeholder="https://www.youtube.com/watch?v=",
		value=""),
	],
	outputs=[
		gr.Textbox(label="Exit Status"),
		gr.Textbox(label="Messages"),
		gr.Textbox(label="Output Text"),
		gr.File(label="Download Output Text"),
	],
	title=title,
	description=desc,
	allow_flagging='never',
)

if __name__ == "__main__":
	demo.launch(
		server_port=8080,
	)
