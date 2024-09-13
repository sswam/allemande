#!/usr/bin/env python3

""" writes a program """

import llm

def program():
    query = "Please write a truly original, novel, unique, short program."
    response = llm.query(query, temperature=1)
    print(response)

if __name__ == '__main__':
    program()
