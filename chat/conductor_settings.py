# The EVERYONE_WORDS and ANYONE_WORDS now only work with @ prefix, so we can include more words

IGNORE_CASE = False

EVERYONE_WORDS = [
    # General plural addresses
    "everyone",
    "everybody",
    "all",
    "girls",
    "boys",
    "ladies",
    "gentlemen",
    "men",
    "women",
    "folks",
    "y'all",
    "you all",
    "all of you",
    "gang", "crew", "team",
]

ANYONE_WORDS = [
    "anyone",
    "someone",
    "who",
    "anybody",
    "somebody",
    "another",
    "other",

    # "one of you",
    # "one of y'all",
    # "who's next",
    # "who's up next",
    # "who's ready",
    # "who's going to",
    # "who is next",
    # "who is ready",
    # "who is going",
    # "who wants to",
    # "who else",
]

SELF_WORDS = ["", "self", "me", "himself", "herself"]   # @ alone means self, or rather don't want an AI reply

# TODO configureable by room

# TODO exclude based on an attribute or settings
# TODO should not include tools in the list of participants
EXCLUDE_TOOLS = set(["palc", "dogu", "gido", "lary", "matz", "luah", "jyan", "jahl", "faby", "qell", "bilda", "goog", "gimg", "utube", "pr0nto"])
EXCLUDE_PARTICIPANTS = set(["system", "sia", "nova", "pixi", "brie", "chaz", "atla", "pliny", "morf"])
# EXCLUDE_PARTICIPANTS = set(["system", "palc", "dogu", "gid", "lary", "matz", "luah", "jyan", "jahl", "faby", "qell", "bilda"])
EXCLUDE_PARTICIPANTS_SYSTEM = set(["system", "the cast"])

EVERYONE_MAX = 5
AI_EVERYONE_MAX = 2

USE_PLURALS = True

# AUTO_CREATE_UNKNOWN_AGENTS = "Chara"
