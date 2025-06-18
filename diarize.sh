#!/bin/sh
# Simple example of converting a transcript (e.g. from whisper) to a bb chat file with speaker names.
< call.txt process -m=emmy "Please add speaker names Alice:\t and Bob:\t, indent subsequent lines, and a blank line after each message. Please correct any transcription errors where possible. For context, Alice is a marketing consultant helping Bob launch his new eco-friendly coffee shop chain called 'Green Bean'. Bob previously ran several successful food trucks." | tee call.bb
