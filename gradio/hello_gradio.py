#!/usr/bin/env python3-allemande

import os
os.environ["GRADIO_ANALYTICS"] = "False"
import gradio as gr

def greet(name, is_morning, temperature):
	salutation = "Good morning" if is_morning else "Good evening"
	greeting = f"{salutation}, {name}! It is {temperature} degrees out right now."
	fahrenheit = temperature * 9/5 + 32
	return greeting, round(fahrenheit, 2)

demo = gr.Interface(
	fn=greet,
	inputs=[
		gr.Textbox(label="Name"),
		gr.Checkbox(label="Is it morning?"),
		gr.Slider(0, 100, label="Temperature (°C)")
	],
	outputs=[
		gr.Textbox(label="Greeting"),
		gr.Number(label="Temperature (°F)")
	],
	allow_flagging='never'
)

if __name__ == "__main__":
	demo.launch()
