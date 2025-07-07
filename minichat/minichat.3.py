#!/usr/bin/env python3

""" A simple stdio chat app for the OpenAI API """

import os
import sys
import getpass
from datetime import datetime

from openai import OpenAI

username = getpass.getuser().title()
assistant_name = os.getenv('AGENT', 'Emmy')
api_base = os.getenv('API_BASE', 'https://api.openai.com/v1')
api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('API_MODEL', 'gpt-4.1')
max_context_messages = int(os.getenv('MAX_CONTEXT', '30'))

client = OpenAI(api_key=api_key, base_url=api_base)
messages = []

if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = f"{username}_{assistant_name}.txt"

chat_file = open(filename, "a")
print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", file=chat_file, flush=True)

while True:
    try:
        user_input = input(f'{username}: ')
    except EOFError:
        break
    messages.append({"role": "user", "content": user_input})
    print(f'{username}:', user_input, file=chat_file, flush=True)
    response = client.chat.completions.create(model=model, messages=messages[-max_context_messages:])
    assistant_message = response.choices[0].message.content
    print(f'{assistant_name}:', assistant_message)
    print(f'{assistant_name}:', assistant_message, file=chat_file, flush=True)
    messages.append({"role": "assistant", "content": assistant_message})

print(file=chat_file, flush=True)
chat_file.close()
