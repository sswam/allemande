#!/usr/bin/env python3-allemande

"""
learn.py - A spaced repetition learning system for markdown flashcards.
"""

import os
import sys
import logging
import datetime
import random
import webbrowser
from typing import TextIO, Optional
from pathlib import Path

from argh import arg
import markdown
import http.server
import socketserver
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ally import main

__version__ = "0.1.0"

logger = main.get_logger()

LEARN_DIR = os.environ.get("LEARN_DIR", os.path.expanduser("~/learn"))
CARDS_TSV = os.path.join(LEARN_DIR, "cards.tsv")

PORT = int(os.environ.get("LEARN_PORT", 2272))


class Card:
    def __init__(self):
        self.ease_factor = 2.5
        self.interval = 1
        self.review_count = 0

    def review(self, quality):
        if self.review_count > 0:
            self.ease_factor = max(1.3, self.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
            self.interval *= self.ease_factor
        else:
            self.interval = 1 if quality < 3 else 6 if quality == 3 else 4

        self.review_count += 1
        return round(self.interval)


def parse_markdown(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    cards = content.split('\n\n\n')
    parsed_cards = []

    for card in cards:
        sections = card.split('\n\n')
        parsed_card = {}
        for section in sections:
            lines = section.split('\n')
            if lines[0].startswith('# '):
                key = lines[0].split('.')[1].strip()
                value = '\n'.join(lines[1:])
                parsed_card[key] = value
        parsed_cards.append(parsed_card)

    return parsed_cards


def create_html(card, card_id, side):
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Flashcard</title>
        <link rel="stylesheet" href="learn.css">
        <script src="learn.js"></script>
    </head>
    <body>
        <div class="card" id="card-{card_id}">
            <div class="side" id="{side}">
                {markdown.markdown(card[side])}
            </div>
            <div class="side" id="{'Back' if side == 'Front' else 'Front'}" style="display: none;">
                {markdown.markdown(card['Back' if side == 'Front' else 'Front'])}
            </div>
            <div class="extra" id="Extra" style="display: none;">
                {markdown.markdown(card.get('Extra', ''))}
            </div>
        </div>
        <div class="buttons">
            <button onclick="rate(1)">1</button>
            <button onclick="rate(2)">2</button>
            <button onclick="rate(3)">3</button>
            <button onclick="rate(4)">4</button>
            <button onclick="rate(5)">5</button>
        </div>
    </body>
    </html>
    """
    return html


def add_cards_to_schedule(cards, file_name):
    with open(CARDS_TSV, 'a') as f:
        for i, card in enumerate(cards):
            for side in ['Front', 'Back']:
                if side in card:
                    due_date = datetime.datetime.now().isoformat()
                    f.write(f"{due_date}\t1\t{file_name}-{i:05d}\t{side}\n")


class CardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Welcome to the flashcard server!")
        elif self.path.startswith('/card/'):
            card_id, side = self.path.split('/')[-2:]
            card = get_card(card_id)
            if card:
                html = create_html(card, card_id, side)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html.encode())
            else:
                self.send_error(404, "Card not found")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/rate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            card_id, rating = post_data.split('=')
            update_card_schedule(card_id, int(rating))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Rating received")
        else:
            self.send_error(405, "Method not allowed")


def get_card(card_id):
    # TODO Implement this function to retrieve the card data
    pass


def update_card_schedule(card_id, rating):
    # TODO Implement this function to update the card's schedule
    pass


def start_server():
    handler = CardHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()


def study_due_cards():
    # Study due cards
    due_cards = get_due_cards()
    if not due_cards:
        put("No cards due for review.")
        return

    start_server()
    for card in due_cards:
        webbrowser.open(f"http://localhost:{PORT}/card/{card['id']}/{card['side']}")


@arg("file", nargs='*', help="markdown files to process")
def learn(
    input: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    file: list[str] = [],
):
    """
    Process markdown flashcard files and implement spaced repetition learning.
    """
    get, put = main.io(input, output)

    if not file:
    else:
        for md_file in file:
            cards = parse_markdown(md_file)
            file_name = os.path.splitext(os.path.basename(md_file))[0]

            for i, card in enumerate(cards):
                card_file = os.path.join(LEARN_DIR, f"{file_name}-{i:05d}.md")
                if main.file_not_empty(card_file):
                    put(f"Warning: {card_file} already exists. Skipping.")
                    continue

                with open(card_file, 'w') as f:
                    for section, content in card.items():
                        f.write(f"# {section}\n{content}\n\n")

            add_cards_to_schedule(cards, file_name)

        # Run Makefile to generate HTML
        os.system(f"cd {LEARN_DIR} && make")


def get_due_cards():
    # Implement this function to retrieve due cards from cards.tsv
    pass


if __name__ == "__main__":
    main.run(learn)

# Notes:
# 1. TODO You'll need to implement the `get_card`, `update_card_schedule`, and `get_due_cards` functions to interact with the `cards.tsv` file.
# 2. The script uses a simple HTTP server to serve the flashcards and handle ratings. You may want to add more robust error handling and security measures for a production environment.
# 3. The CSS and JavaScript files can be customized further to improve the user interface and experience.
# 4. You may want to add more command-line options to control the behavior of the script, such as specifying the number of cards to review or setting a time limit for the study session.
