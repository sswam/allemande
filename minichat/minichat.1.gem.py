#!/usr/bin/env python3

""" A simple AI chat app using the OpenAI API, e.g. Gemma 4 31B through OpenRouter """

import os
import getpass

from openai import OpenAI

username = getpass.getuser().title()
assistant_name = os.getenv('AGENT', 'Gem')
api_base = os.getenv('API_BASE', 'https://openrouter.ai/api/v1')
api_key = os.getenv('OPENROUTER_API_KEY')
model = os.getenv('API_MODEL', "google/gemma-4-31b-it")

client = OpenAI(api_key=api_key, base_url=api_base)
messages = []

while True:
    try:
        user_input = input(f'{username}: ')
    except EOFError:
        break
    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(model=model, messages=messages)
    assistant_message = response.choices[0].message.content
    print(f'{assistant_name}:', assistant_message)
    messages.append({"role": "assistant", "content": assistant_message})
