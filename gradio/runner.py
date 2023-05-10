#!/usr/bin/env python3
""" run a text processing command in a web interface """

# TODO other data types:
# text, image, audio, video, sketchpad, or label
# TODO get GPT-4 to generate custom Gradio UIs for different tools

# TODO use net2sh syntax, like:
#   cp from< to>

# Note to self: See here for ideas:
#  - https://chat.openai.com/c/97414fcd-4d80-4274-ae7f-3262351894bf
#  - https://chat.openai.com/c/db7f96e5-a702-4274-9e5c-ba636ad1aa01


import subprocess
import os
import logging
import tempfile
from pathlib import Path

os.environ["GRADIO_ANALYTICS"] = "False"
import gradio as gr   # pylint: disable=wrong-import-position


logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__name__)


cmd = os.environ.get("RUNNER_CMD", "wc -w")
# args = os.environ.get("RUNNER_ARGS", "")
# args = [x for x in args.split(" ") if x]
name = os.environ.get("RUNNER_NAME", f"`{cmd}`")
title = os.environ.get("RUNNER_TITLE", f"Process Text with {name}")
desc = os.environ.get("RUNNER_DESC", f"Enter text to process using {name}")


def process_text(text_input, file_input):
    """ run a text processing command in a web interface """
    if file_input is not None:
        with open(file_input.name, "r", encoding="utf-8") as f:
            text_input = f.read()

    result = subprocess.run(
        cmd,
        shell=True,
        input=text_input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    output_text = result.stdout
    error_text = result.stderr
    status = result.returncode

    tmpdir = tempfile.mkdtemp()
    output_file = Path(tmpdir) / "output.txt"

    # TODO how to delete the tmpdir

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output_text)

    status_str = "Success" if status == 0 else "Error"

    status = f"{status}: {status_str}"

    return status, error_text, output_text, str(output_file)


#inputs=[
#    gr.inputs.Textbox(label="Input Text", lines=5, placeholder="Enter your text here..."),
#    gr.inputs.File(label="Upload Input Text"),
#],


demo = gr.Interface(
    fn=process_text,
    inputs=[
        gr.inputs.Textbox(label="Input Text", lines=5, placeholder="Enter your text here..."),
        gr.inputs.File(label="Upload Input Text"),
    ],
    outputs=[
        gr.outputs.Textbox(label="Exit Status"),
        gr.outputs.Textbox(label="Messages"),
        gr.outputs.Textbox(label="Output Text"),
        gr.outputs.File(label="Download Output Text"),
    ],
    title=title,
    description=desc,
    allow_flagging='never',
)


if __name__ == "__main__":
    demo.launch(
#        server_name="0.0.0.0",
        server_port=8080,
    )
