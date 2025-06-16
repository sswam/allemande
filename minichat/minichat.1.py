#!/usr/bin/env python3

""" A simple stdio chat app for the OpenAI API """

import os
import getpass

from openai import OpenAI

username = getpass.getuser().title()
assistant_name = os.getenv('AGENT', 'Emmy')
api_base = os.getenv('API_BASE', 'https://api.openai.com/v1')
api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('API_MODEL', 'gpt-4.1')

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
