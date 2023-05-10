#!/usr/bin/env python3

import os
os.environ["GRADIO_ANALYTICS"] = "False"
import gradio as gr

def greet1(name):
	return "Hello " + name + "!"

def greet(name, is_morning, temperature):
	salutation = "Good morning" if is_morning else "Good evening"
	greeting = f"{salutation}, {name}! It is {temperature} degrees out right now."
	farenheit = temperature * 9/5 + 32
	return greeting, round(farenheit, 2)

# text, image, audio, video, sketchpad, or label

#demo = gr.Interface(fn=greet, inputs="text", outputs="text")
#demo = gr.Interface(fn=greet, inputs=gr.Textbox(lines=2, placeholder="Name here"), outputs="text")
demo = gr.Interface(fn=greet, inputs=["text", "checkbox", gr.Slider(0,100)],
	outputs=["text", "number"], allow_flagging='never')

if __name__ == "__main__":
	demo.launch()
