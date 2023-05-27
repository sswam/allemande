#!/usr/bin/env python3

import os
import anthropic

for max_tokens_to_sample in [9000, 90000]:
    c = anthropic.Client(os.environ["ANTHROPIC_API_KEY"])
    response = c.completion(
        prompt=f"{anthropic.HUMAN_PROMPT} Hello, Claude 100k model. How are you?{anthropic.AI_PROMPT}",
        model="claude-v1-100k",
        max_tokens_to_sample=max_tokens_to_sample,
        temperature=1.0,
    )
    print(response.get('completion', ''))
