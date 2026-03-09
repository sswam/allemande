import re

"""
Attempt to avoid Llama repetition by removing duplicate common prefixes
and suffixes from chat history.
"""

__version__ = "0.1.1"


def _first_word(s: str) -> str:
    """Return the first alphanumeric word in s, or empty string."""
    m = re.search(r'\w+', s)
    return m.group() if m else ""


def _last_word(s: str) -> str:
    """Return the last alphanumeric word in s, or empty string."""
    words = re.findall(r'\w+', s)
    return words[-1] if words else ""


def _strip_word_prefix(prior: str, later: str) -> str:
    """Strip the longest common word-sequence prefix of prior from prior."""
    words_prior = re.findall(r'\w+', prior)
    words_later = re.findall(r'\w+', later)
    n = 0
    for w1, w2 in zip(words_prior, words_later):
        if w1 != w2:
            break
        n += 1
    if n == 0:
        return prior
    if n >= len(words_prior):
        return ""
    # Find the nth word match in prior and cut from there
    word_matches = list(re.finditer(r'\w+', prior))
    cut = word_matches[n].start()
    # Strip any leading non-word characters before the cut word
    m = re.search(r'\w', prior[cut:])
    if not m:
        return ""
    return prior[cut + m.start():]


def _strip_word_suffix(prior: str, later: str) -> str:
    """Strip the longest common word-sequence suffix of prior from prior."""
    words_prior = re.findall(r'\w+', prior)
    words_later = re.findall(r'\w+', later)
    n = 0
    for w1, w2 in zip(reversed(words_prior), reversed(words_later)):
        if w1 != w2:
            break
        n += 1
    if n == 0:
        return prior
    if n >= len(words_prior):
        return ""
    word_matches = list(re.finditer(r'\w+', prior))
    cut = word_matches[-n].start()
    return prior[:cut].rstrip()


def _apply_prefix_stripping(messages: list[dict[str, str]]) -> None:
    """Backward pass: strip common word-prefixes from older messages."""
    prefix_index: dict[str, str] = {}
    for msg in reversed(messages):
        content = msg["content"]
        if not content.strip():
            continue
        key = _first_word(content).lower()
        if not key:
            continue
        if key in prefix_index:
            content = _strip_word_prefix(content, prefix_index[key])
            content = re.sub(r'^\W+', '', content)
            msg["content"] = content
        else:
            prefix_index[key] = content


def _apply_suffix_stripping(messages: list[dict[str, str]]) -> None:
    """Backward pass: strip common word-suffixes from older messages."""
    suffix_index: dict[str, str] = {}
    for msg in reversed(messages):
        content = msg["content"]
        if not content.strip():
            continue
        key = _last_word(content).lower()
        if not key:
            continue
        if key in suffix_index:
            content = _strip_word_suffix(content, suffix_index[key])
            content = re.sub(r'\W+$', '', content)
            msg["content"] = content
        else:
            suffix_index[key] = content


def hacky_anti_rep(messages: list[dict[str, str]], strip_empty: bool = True) -> None:
    """
    Attempt to avoid Llama repetition by removing duplicate common prefixes
    and suffixes from chat history.
    """
    _apply_prefix_stripping(messages)
    _apply_suffix_stripping(messages)
    if strip_empty:
        messages[:] = [m for m in messages if m["content"]]
