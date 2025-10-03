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
EXCLUDE_TOOLS = set(["Palc", "Dogu", "Gido", "Lary", "Matz", "Luah", "Jyan", "Jahl", "Faby", "Qell", "Bilda", "Goog", "Gimg", "Utube", "Pr0nto"])
EXCLUDE_PARTICIPANTS = set(["System", "Sia", "Nova", "Pixi", "Brie", "Chaz", "Atla", "Pliny", "Morf"])
# EXCLUDE_PARTICIPANTS = set(["System", "Palc", "Dogu", "Gid", "Lary", "Matz", "Luah", "Jyan", "Jahl", "Faby", "Qell", "Bilda"])
EXCLUDE_PARTICIPANTS_SYSTEM = set(["System", "The Cast"])

EVERYONE_MAX = 5
AI_EVERYONE_MAX = 2

USE_PLURALS = True
