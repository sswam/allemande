#!/bin/bash
create.sh learn.py "$(cat <<'END'
Given a markdown flashcards file like deep-learning.md, double blank line between cards,
and numbered headings for card sections, implement spaced repetition learning
for the user.

In ~/learn/ (or $LEARN_DIR), create a file for each note like
deep-learning-00001.md, warn and don't clobber if it already exists.
~/learn/cards.tsv is a learning schedule, the columns are timestamp due,
interval, card name, and 'prompt' side for that the card. Add each note twice,
for its Front and Back as the 'question'.

Write a ~/learn/Makefile and script if needed, or can we use pandoc? to convert
all cards to HMTL (with tables, syntax-highlighted code, TeX, mermaid, etc),
and run the Makefile when adding new cards. Add CSS to hide the whole card by
default, and JavaScript to show the 'question' side based on the url
'fragment', like deep-learning-00001.md#Front.

On click or keypress, show the other side and the Extra section underneath.
Show buttons 1 through 5, 1 is best (easy). User can click or type the number.

Mostly my cards are reversible term <-> definition, but if a card has "Question"
and "Answer" sections, it is not reversible. The "Extra" section is always
hidden until the user clicks or presses a key, it has non-essential interesting
info to distract the user from ploughing through the cards!

User can run learn.py without args to study due cards, which are opened one at
a time in the browser by the script. It just opens the HTML files, but runs a
localhost http server to receive responses (if possible, else serve the html too).
The cards.tsv is append only, just append a row with new due date and other
info. Another helper suggested this method for calculating due dates:


```python
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

# Usage
card = Card()
next_review = card.review(4)  # Quality: 0 (worst) to 5 (best)
```

Ideally at first if the users scores low (4 or 5) it would show the card again soon like within 5 or 10 minutes. If they score high, show the next day. Like Anki.

We might turn this into a web app later but for now just do it how I said, please. I like me a plain text file, I do. It's fine to serve the HTML instead of using a file:/// URL, probably a better idea. It should be static HTML though. The CSS and JavaScript files can go in a separate learn.js file in the same folder as the cards, user might want to edit them.

If I missed anything essential, please try to do that to, or make a note of it.
END
)" ./deep-learning.md
