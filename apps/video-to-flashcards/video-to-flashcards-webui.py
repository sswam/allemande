#!/usr/bin/env python3
""" run video-to-flashcards in a web interface """

# TODO other data types:
# text, image, audio, video, sketchpad, or label
# TODO get GPT-4 to generate custom Gradio UIs for different tools


import subprocess
import os
import logging
import tempfile
from pathlib import Path

WHISPER = os.environ.get("WHISPER", "whisp")

os.environ["GRADIO_ANALYTICS"] = "False"
import gradio as gr   # pylint: disable=wrong-import-position


logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__name__)


cmd = "video-to-flashcards-cached"
opts = [ "WHISPER="+WHISPER ]
name = "Video to Flashcards"
title = os.environ.get("RUNNER_TITLE", f"{name}")
desc = os.environ.get("RUNNER_DESC", f"Enter the URL of a short video (<15m). The program will try to summarize the video, and produce flashcards.")


def process_text(Video_url):
    """ run a text processing command in a web interface """

    logger.info("Processing: %r", video_url)

    error_text = ""
    output_text = ""
    status = 255

    result = None

    # show PATH
    logger.debug("PATH: %r", os.environ["PATH"].split(":"))

    result = subprocess.run(
        [cmd, video_url, *opts],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

#    try:
#        result = subprocess.run(
#            [cmd, video_url],
#            stdout=subprocess.PIPE,
#            stderr=subprocess.PIPE,
#            text=True,
#            check=False,
#        )
#    except subprocess.CalledProcessError as err:
#        logger.error("Error: %r", err)
#        error_text += repr(err) + "\n\n"

    if result:
        output_text = result.stdout
        error_text += result.stderr
        status = result.returncode

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
        gr.inputs.Textbox(label="Video URL",
        lines=1,
        placeholder="Enter the URL here...",
        default="https://www.youtube.com/watch?v=NsevBxOWFXs"),
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
        server_port=8080,
    )
