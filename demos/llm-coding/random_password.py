#!/usr/bin/env python3-allemande
# random_password.py - Generate a random password of given length
# Written by ChatGPT 3.5 as a response to the query:
# gpt query 'Please write me a small python program to do whatever! Just think of anything random to do, please.'

import random
import string

def generate_password(length):
	"""Generate a random password of given length"""
	password = ""
	for i in range(length):
		password += random.choice(string.ascii_letters + string.digits + string.punctuation)
	return password

password_length = int(input("Enter length of password: "))
print("Your random password is:", generate_password(password_length))
