import re

"""
Attempt to avoid Llama repetition by removing duplicate common prefixes
and suffixes from chat history.
"""

__version__ = "0.1.5"

# Apostrophe is treated as a word character (e.g. "don't", "it's")
_WORD = r"[\w']+"
_TWO_WORDS = r"[\w']+[\W]+[\w']+"
_WORD_CHAR = r"[\w']"
_NON_WORD = r"[^\w']"


def _first_word(s: str) -> str:
    """Return the first alphanumeric word in s, or empty string."""
    m = re.search(_WORD, s)
    return m.group() if m else ""


def _first_two_words(s: str) -> str:
    """Return the first two alphanumeric word in s, or empty string."""
    m = re.search(_TWO_WORDS, s)
    return m.group() if m else ""


def _last_word(s: str) -> str:
    """Return the last alphanumeric word in s, or empty string."""
    words = re.findall(_WORD, s)
    return words[-1] if words else ""


def _strip_word_prefix(prior: str, later: str) -> str:
    """Strip the longest common word-sequence prefix of prior from prior."""
    words_prior = re.findall(_WORD, prior)
    words_later = re.findall(_WORD, later)
    n = 0
    for w1, w2 in zip(words_prior, words_later):
        if w1.lower() != w2.lower():
            break
        n += 1
    if n == 0:
        return prior
    if n >= len(words_prior):
        return ""
    # Find the nth word match in prior and cut from there
    word_matches = list(re.finditer(_WORD, prior))
    cut = word_matches[n].start()
    # Strip any leading non-word characters before the cut word
    m = re.search(_WORD_CHAR, prior[cut:])
    if not m:
        return ""
    return prior[cut + m.start():]


def _prefix_strip_length(later: str, prior: str) -> int:
    """Return the character length of the common word-sequence prefix stripped from later."""
    stripped = _strip_word_prefix(later, prior)
    stripped = re.sub(f'^{_NON_WORD}+', '', stripped)
    stripped = re.sub(rf'^and{_NON_WORD}+', '', stripped, re.IGNORECASE)  # HACK: don't allow final text to start with "and"
    return len(later) - len(stripped)


def _strip_word_suffix(prior: str, later: str) -> str:
    """Strip the longest common word-sequence suffix of prior from prior."""
    words_prior = re.findall(_WORD, prior)
    words_later = re.findall(_WORD, later)
    n = 0
    for w1, w2 in zip(reversed(words_prior), reversed(words_later)):
        if w1.lower() != w2.lower():
            break
        n += 1
    if n == 0:
        return prior
    if n >= len(words_prior):
        return ""
    word_matches = list(re.finditer(_WORD, prior))
    cut = word_matches[-n].start()
    return prior[:cut].rstrip()


def _suffix_strip_length(later: str, prior: str) -> int:
    """Return the character length of the common word-sequence suffix stripped from later."""
    stripped = _strip_word_suffix(later, prior)
    stripped = re.sub(f'{_NON_WORD}+$', '', stripped)
    stripped = re.sub(r'\band$', '', stripped, re.IGNORECASE)  # HACK: don't allow final text to end with "and"
    return len(later) - len(stripped)


def _apply_prefix_stripping(messages: list[dict[str, str]], strip_both: bool = True) -> None:
    """Backward pass: strip common word-prefixes from older (earlier) messages.
    If strip_both, also strip the shared prefix from the newer message.
    We track the prefix length stripped from the later message so subsequent
    prior messages are matched against the original later content correctly."""
    # index maps key -> (msg_dict, original_content, strip_len_from_later)
    prefix_index: dict[str, tuple] = {}
    for msg in reversed(messages):
        if msg["user"] in ["", "System"]:
            continue
        content = msg["content"]
        if not content.strip():
            continue
        key = _first_two_words(content).lower()
        if not key:
            continue
        if key in prefix_index:
            later_msg, later_original, later_strip_len = prefix_index[key]
            stripped_prior = _strip_word_prefix(content, later_original)
            stripped_prior = re.sub(f'^{_NON_WORD}+', '', stripped_prior)
            msg["content"] = stripped_prior
            if strip_both:
                new_strip_len = _prefix_strip_length(later_original, content)
                if new_strip_len > later_strip_len:
                    # Apply the longer strip to the later message
                    new_later = re.sub(f'^{_NON_WORD}+', '', later_original[new_strip_len:])
                    if new_later:  # don't empty the later message
                        later_msg["content"] = new_later
                        prefix_index[key] = (later_msg, later_original, new_strip_len)
                # else keep existing strip on later_msg
            else:
                # Update index so subsequent matches strip against the original content
                prefix_index[key] = (later_msg, later_original, 0)
        else:
            prefix_index[key] = (msg, content, 0)


def _trailing_newlines(s: str) -> str:
    """Detect and return trailing newlines"""
    m = re.search(r'\n+$', s)
    return m.group() if m else ''


def _apply_suffix_stripping(messages: list[dict[str, str]], strip_both: bool = True) -> None:
    """Backward pass: strip common word-suffixes from older (earlier) messages.
    If strip_both, also strip the shared suffix from the newer message.
    We track the suffix length stripped from the later message so subsequent
    prior messages are matched against the original later content correctly."""
    suffix_index: dict[str, tuple] = {}
    for msg in reversed(messages):
        if msg["user"] in ["", "System"]:
            continue
        content = msg["content"]
        if not content.strip():
            continue
        key = _last_word(content).lower()
        if not key:
            continue
        if key in suffix_index:
            later_msg, later_original, later_strip_len = suffix_index[key]
            stripped_prior = _strip_word_suffix(content, later_original)
            stripped_prior = re.sub(f'{_NON_WORD}+$', '', stripped_prior)
            msg["content"] = stripped_prior + _trailing_newlines(content)
            if strip_both:
                new_strip_len = _suffix_strip_length(later_original, content)
                if new_strip_len > later_strip_len:
                    new_later = re.sub(f'{_NON_WORD}+$', '', later_original[:-new_strip_len] if new_strip_len else later_original)
                    if new_later:  # don't empty the later message
                        later_msg["content"] = new_later + _trailing_newlines(later_original)
                        suffix_index[key] = (later_msg, later_original, new_strip_len)
                # else keep existing strip on later_msg
            else:
                suffix_index[key] = (later_msg, later_original, 0)
        else:
            suffix_index[key] = (msg, content, 0)


def hacky_anti_rep(messages: list[dict[str, str]], strip_empty: bool = True, strip_both: bool = True, keep_last: bool = True) -> None:
    """
    Attempt to avoid Llama repetition by removing duplicate common prefixes
    and suffixes from chat history. strip_both strips the repeated portion
    from both the older and newer message (on by default).
    """
    last = None
    if keep_last and messages:
        last = messages[-1]["content"]
    _apply_prefix_stripping(messages, strip_both=strip_both)
    _apply_suffix_stripping(messages, strip_both=strip_both)
    if last:
        messages[-1]["content"] = last
    if strip_empty:
        messages[:] = [m for m in messages if m["content"]]
