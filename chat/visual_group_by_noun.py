#!/usr/bin/env python3-allemande

"""
Filter functions to make Pony-style prompts more acceptable for Krea 2 and
similar models, especially to avoid it drawing duplicate people
"""

import sys
import re
from collections import defaultdict


BLACKLIST_TAGS = {
    "pretty eyes"
}

BLACKLIST_NOUNS = {
    "old"
}


def prompt_group_by_noun(prompt: str) -> str:
    """Process a whole prompt, splitting by subject (1girl, etc), then grouping by noun; this is hacky but should work okay"""
    parts = re.split(r"\b((?:1girl|1boy|1other),?\s*)\b", prompt) + [""]
    parts2 = []
    for i in range(0, len(parts), 2):
        part, delim = parts[i : i + 2]
        part2 = visual_group_by_noun_with_set(part)
        parts2.append(part2.strip())
        parts2.append(delim.strip())
    prompt2 = " ".join(parts2).strip()
    return prompt2


def visual_group_by_noun_with_set(prompt: str) -> str:
    """Split a prompt to extract [set ...]...[/set] and [choose] macros, then put the other parts through visual_group_by_noun"""
    parts = re.findall(r"\[set.*?\[/set\],?|\[choose.*?\[/choose\],?|.+?(?=\[set|\[choose|$)", prompt)
    parts2 = []
    for part in parts:
        part = part.strip()
        if re.match(r"\[set|\[choose", part):
            parts2.append(part)
        else:
            parts2.append(visual_group_by_noun(part).strip())
    prompt2 = " ".join(parts2)
    return prompt2


def visual_group_by_noun(prompt: str) -> str:
    """Group comma-separated tags by noun, so they work better with Krea 2 and similar models"""
    tags = re.split(r"\s*,\s*", prompt)
    by_noun = defaultdict(list)
    for tag in tags:
        match = re.match(r"(.*)\s+(\S+)$", tag)
        match2 = re.match(r"\((.*)\s+(\S+?)\s*(:[0-9.]+)?\s*\)$", tag)
        if match2:
            adjectives, noun, weight = match2.groups()
            if noun not in BLACKLIST_NOUNS:
                by_noun[noun].append(f"({adjectives}{weight or ''})")
                continue
        elif match and tag not in BLACKLIST_TAGS:
            adjectives, noun = match.groups()
            if noun not in BLACKLIST_NOUNS:
                by_noun[noun].append(adjectives)
                continue
        by_noun[tag].append("")
    terms = []
    for noun, adjectives_list in by_noun.items():
        term = " ".join([adjs for adjs in adjectives_list if adjs] + [noun])
        terms.append(term)
    prompt2 = ", ".join(terms).strip()
    if prompt.endswith(",") and not prompt2.endswith(","):
        prompt2 += ","
    return prompt2


def main():
    for line in sys.stdin:
        print(prompt_group_by_noun(line))


if __name__ == "__main__":
    main()
