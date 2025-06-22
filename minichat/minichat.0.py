#!/usr/bin/env python3

""" A simple stdio chat app for the OpenAI API """

import getpass

from openai import OpenAI

username = getpass.getuser().title()

client = OpenAI()
messages = []

while True:
    user_input = input(f'{username}: ')
    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(model='gpt-4.1', messages=messages)
    assistant_message = response.choices[0].message.content
    print(f'Emmy:', assistant_message)
    messages.append({"role": "assistant", "content": assistant_message})
