#!/usr/bin/env python3

# bard.py: A Python wrapper for Google's BARD chatbot API.

# based on Bard-API by MinWoo Park
# Copyright (c) 2023 MinWoo Park
# Copyright (c) 2023 Sam Watkins

import json
import random
import re
import string
import os
import sys
import readline
import requests
import argh


class Bard:
    def __init__(self, timeout=30, proxies=None, session=None, state=None, state_file=None, auto_save=None):
        """
        Initialize Bard

        :param timeout: (`int`, *optional*)
            Timeout in seconds when connecting bard server. The timeout is used on each request.
        :param proxies: (`Dict[str, str]`, *optional*)
            A dictionary of proxy servers to use by protocol or endpoint, e.g., `{'http': 'foo.bar:3128',
            'http://hostname': 'foo.bar:4012'}`. The proxies are used on each request.
        :param session: (`requests.Session`, *optional*)
            An existing requests.Session object to be used for making HTTP requests.
        :param state: (`Dict[str, str]`, *optional*)
            A state object, which contains the conversation_id, response_id, and choice_id, and cookies,
            to enable resuming a conversation in a different session.
        """
        self.proxies = proxies
        self.timeout = timeout
        self.state_file = state_file
        if auto_save is None:
            auto_save = bool(state_file)
        self.auto_save = auto_save
        headers = {
            "Host": "bard.google.com",
            "X-Same-Domain": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.114 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Origin": "https://bard.google.com",
            "Referer": "https://bard.google.com/",
        }
        self._reqid = int("".join(random.choices(string.digits, k=4)))

        if session is None:
            self.session = requests.Session()
            self.session.headers = headers
            self.session.cookies.set("__Secure-1PSID", os.environ["_BARD_API_KEY"])
        else:
            self.session = session

        if state_file:
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
            except FileNotFoundError:
                pass

        print(state)

        if state:
            self.conversation_id = state["conversation_id"]
            self.response_id = state["response_id"]
            self.choice_id = state["choice_id"]
            self.SNlM0e = state["SNlM0e"]
            cookies = state["cookies"]
            for k in cookies:
                self.session.cookies.set(k, cookies[k])
        else:
            self.SNlM0e = self._get_snim0e()
            self.conversation_id = ""
            self.response_id = ""
            self.choice_id = ""

    def get_state(self):
        return {
            "conversation_id": self.conversation_id,
            "response_id": self.response_id,
            "choice_id": self.choice_id,
            "SNlM0e": self.SNlM0e,
            "cookies": self.session.cookies.get_dict(),
        }

    def save_state(self, state_file=None):
        if state_file:
            self.state_file = state_file
        if not self.state_file:
            raise Exception("state_file is not set")
        with open(self.state_file, "w") as f:
            json.dump(self.get_state(), f)

    def _get_snim0e(self):
        resp = self.session.get(
            url="https://bard.google.com/", timeout=self.timeout, proxies=self.proxies
        )
        if resp.status_code != 200:
            raise Exception(f"Response Status: {resp.status_code}")
        return re.search(r"SNlM0e\":\"(.*?)\"", resp.text).group(1)

    def get_answer(self, input_text: str) -> dict:
        params = {
            "bl": "boq_assistant-bard-web-server_20230419.00_p1",
            "_reqid": str(self._reqid),
            "rt": "c",
        }
        input_text_struct = [
            [input_text],
            None,
            [self.conversation_id, self.response_id, self.choice_id],
        ]
        data = {
            "f.req": json.dumps([None, json.dumps(input_text_struct)]),
            "at": self.SNlM0e,
        }
        resp = self.session.post(
            "https://bard.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate",
            params=params,
            data=data,
            timeout=self.timeout,
            proxies=self.proxies,
        )
        resp_dict = json.loads(resp.content.splitlines()[3])[0][2]
        if resp_dict is None:
            return {"content": f"Response Error: {resp.content}."}
        parsed_answer = json.loads(resp_dict)
        bard_answer = {
            "content": parsed_answer[0][0],
            "conversation_id": parsed_answer[1][0],
            "response_id": parsed_answer[1][1],
            "factualityQueries": parsed_answer[3],
            "textQuery": parsed_answer[2][0] if parsed_answer[2] is not None else "",
            "choices": [{"id": i[0], "content": i[1]} for i in parsed_answer[4]],
        }
        self.conversation_id = bard_answer["conversation_id"]
        self.response_id = bard_answer["response_id"]
        self.choice_id = bard_answer["choices"][0]["id"]
        self._reqid += 100000

        if self.auto_save:
            self.save_state()

        return bard_answer

def default_user():
    return os.environ["USER"].title()

def chat(state_file=None, user=None):
    if user is None:
        user = default_user()
    bard = Bard(state_file=state_file, auto_save=bool(state_file))
    while True:
        try:
            input_text = input(f"{user}: ")
        except EOFError:
            break
        except KeyboardInterrupt:
            sys.exit(1)
        answer = bard.get_answer(input_text)
        print("Bard:", answer["content"])
        print(json.dumps(answer, indent=4))
#        if answer["choices"]:
#            print("Choices:")
#            for i in answer["choices"]:
##                print(f"{i['id']}: {i['content']}")
##            choice_id = input("Your choice: ")
##            answer = bard.get_answer(choice_id)
##            print("Bard: ", answer["content"])

if __name__ == '__main__':
    argh.dispatch_command(chat)
