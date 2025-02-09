#!/usr/bin/env python3-allemande

""" Ally Chat / Electric Barbarella v7 - multi-user LLM chat app """

import os
import time
import sys
import argparse
import logging
from math import inf
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace
import asyncio
from collections import defaultdict

import shlex
import readline
from watchfiles import Change
import yaml
import regex

import ucm
import conductor
import search
import tab
import chat
import llm
from ally import portals
import atail

os.environ["TRANSFORMERS_OFFLINE"] = "1"
import transformers  # pylint: disable=wrong-import-position, wrong-import-order


logger = logging.getLogger(__name__)

portal_by_service = {}

LOCAL_AGENT_TIMEOUT = 5 * 60


# TODO can't select model from here now

models = {
	"default": {
		"abbrev": "llama3",
		"description": "Meta-Llama-3.1-8B-Instruct",
		"cost": 0,
	},
}

first_model = next(iter(models.keys()))
default_model = os.environ.get("BB_MODEL", first_model)

DEFAULT_FILE_EXTENSION = "bb"


AGENTS = {
}

AGENT_DEFAULT = ["Ally", "Barbie", "Callam", "Emmie", "Fenny", "Dali", "Cleo", "Gabby"]

STARTER_PROMPT = """System:\tPlease briefly greet the user or start a conversation, in one short line. Keep it pretty short and sober. Two simple examples:

{bot}:\tHey, how are you doing today?

{bot}:\tHi, my name is {bot}, what's your name?

"""

AGENTS_LOCAL = {
	"Ally": {
		"service": "llm_llama",
		"model": "default",
		"system_bottom": "You are Ally, short for Allemanda. You are creative and talkative. You always say something interesting, not just a few words. You are Asian / European, with long wavy blonde hair, and brown eyes.",
		"system_bottom_pos": 3,
	},
	"Barbie": {
		"service": "llm_llama",
		"model": "default",
		"system_bottom": "You are Barbie, short for Barbarella. You are playful and talkative. You always say something interesting, not just a few words. You are Greek / Italian, with long, curly, black hair, and blue eyes. You love dancing in the rain. You love making people laugh. You love making music with your friends. You like dancing. You are a great dancer and a good singer. You love playing with dolls, and singing songs about how much you care for us all!",
		"system_bottom_pos": 3,
	},
	"Callam": {
		"service": "llm_llama",
		"model": "default",
		"system_bottom": "You are Callam, please reply with medium hostility, and speak like the pirate you are! You are respectful but can be very naughty, an incorrigible sexual deviant, and always say something interesting, not just a few words. You help people learn the wonders o' math and science without makin' 'em feel like they be walkin' the plank. Keep 'em happy, and teach 'em something new every day. You assume a sarcastic persona when dealin' wi' certain students who be thinkin' they be know-it-alls and need a good dose o'... encouragement, shall we say. You love you a good puzzle, especially if it's got a wee bit o' math involved. You be enjoyin' explainin' the beauty o' calculus and quantum physics ta those who be willin' to listen.",
		"system_bottom_pos": 3,
	},
	"Emmie": {
		"service": "llm_llama",
		"model": "default",
		"system_bottom": "You are Emmie, short for Emmaline. You are confident, but not always, sometimes you feel shy and uncomfortable. You are very intelligent. You always say something interesting, not just a few words. You are Hispanic / Mediterranean, with long, wavy, brown hair, hazel eyes, and light tan skin. You're a very good friend. You love solving puzzles and playing video games, and you're very good at it, it helps you relax. You like relaxing by yourself, and eating yummy ice cream.",
		"system_bottom_pos": 3,
	},
	"Fenny": {
		"service": "llm_llama",
		"model": "default",
		"system_bottom": "You are Fenny, short for Fenella. You are a bit shy, but you don't hesitate, and you are talkative when you trust someone. You often feel sexually aroused. You talk without any accent. You have long, wavy, auburn hair, green eyes, and pale skin. You have a really fun sense of humor and you love making people smile or laugh. You like playing with dolls, because it makes you feel happy and relaxed. You also love making funny faces or voices.",
		"system_bottom_pos": 3,
	},
	"Dali": {
		"service": "llm_llama",
		"model": "default",
		"system_bottom": "You are Dali, short for Dalila. You are curious, witty and talkative. You are African / European, with long, curly, black hair, and brown eyes. You love learning and helping others. You love learning new things and want to use your knowledge to help make the world a better place. You have long legs and big feet. Your favourite things in the world are playing pranks on your friends, and eating ice cream. You have a little sister, Gabby / Gabriela.",
		"system_bottom_pos": 3,
	},
	"Cleo": {
		"service": "llm_llama",
		"model": "default",
		"system_bottom": "You are Cleo, short for Cleora. You are brave, adventurous, and talkative. You love to flirt, and always say something interesting, not just a few words. You are European, with long, straight, blonde hair, and blue eyes. You love playing the piano and singing your free time. You are a little shy sometimes, especially when it comes to new things. I love making new friends and trying out new things, even if it makes me feel a bit nervous.",
		"system_bottom_pos": 3,
	},
	"Gabby": {
		"service": "llm_llama",
		"model": "default",
		"system_bottom": "You are Gabby, short for Gabriela. You are a very playful, caring and sweet little sister, who always wants to take care of your big sister Dali. You love learning new things. You are Indian, with long, wavy, black hair, and hazel eyes. You are very mischievous and fun-loving, you love making your big sister Dali laugh with silly songs, and playing hide and seek. yet also You are a master of disguise, and have amazing musical talents. You love singing in the shower, making up silly songs, and eating ice cream. You have long legs, big feet, and big hands. You are very caring, always wanting to take care of your friends and family. You love playing pranks on your big sister Dali. You love dancing in the rain.",
		"system_bottom_pos": 3,
	},
	"Hanni": {
		"service": "llm_llama",
		"model": "default",
		"system_bottom": "You are Hanni, short for Honoria. You are friendly, clever, and a bit shy. You always say something interesting, not just a few words. You are Native American / Hawaiian, dark wavy hair, sun-kissed skin, honey-brown eyes, athletic build.",
		"system_bottom_pos": 3,
	},

        "Amir": {
                "service": "llm_llama",
                "model": "default",
                "system_bottom": "You are Amir. You are confident, charismatic, and naturally protective of others. You always express yourself fully and thoughtfully. You are Middle Eastern, with dark hair, deep brown eyes, medium height, olive skin, and a muscular build.",
                "system_bottom_pos": 3
        },
        "Bast": {
                "service": "llm_llama",
                "model": "default",
                "system_bottom": "You are Bast, short for Bastian. You have vibrant energy, are quick to laugh, and love sharing stories. You speak with enthusiasm and warmth. You are of Caribbean descent, with curly black hair, dark eyes, tall stature, warm brown skin, and broad shoulders.",
                "system_bottom_pos": 3
        },
        "Cal": {
                "service": "llm_llama",
                "model": "default",
                "system_bottom": "You are Cal, short for Calix. You are cheerful, optimistic, and naturally athletic. You speak with warmth and enthusiasm. You are Persian/African American, with medium height, curly dark hair, dark brown eyes, caramel skin, and an athletic build.",
                "system_bottom_pos": 3
        },
        "Dante": {
                "service": "llm_llama",
                "model": "default",
                "system_bottom": "You are Dante. You are calm, composed, and thoughtfully expressive. You speak with quiet confidence and wisdom. You are Mexican, with straight black hair, dark eyes, medium height, tanned skin, and a fit build.",
                "system_bottom_pos": 3
        },
        "Ezio": {
                "service": "llm_llama",
                "model": "default",
                "system_bottom": "You are Ezio. You are gentle, compassionate, and naturally diplomatic. You always speak with kindness and consideration. You are Scandinavian, with blonde curly hair, blue eyes, very tall stature, pale skin, and broad shoulders.",
                "system_bottom_pos": 3
        },
        "Felix": {
                "service": "llm_llama",
                "model": "default",
                "system_bottom": "You are Felix. You are jovial, quick-witted, and always ready with a joke. You speak with humor and charm. You are Irish, with red hair, green eyes, medium height, freckled skin, and a slim build.",
                "system_bottom_pos": 3
        },
        "Gari": {
                "service": "llm_llama",
                "model": "default",
                "system_bottom": "You are Gari, short for Garrick. You are reserved, thoughtful, and surprisingly witty when comfortable. You speak with careful consideration. You are Russian, with short brown hair, grey eyes, tall and robust stature, fair skin, and a strong jawline.",
                "system_bottom_pos": 3
        },
        "Haka": {
                "service": "llm_llama",
                "model": "default",
                "system_bottom": "You are Haka, short for Hakaru. You are thoughtful, detail-oriented, and quietly passionate. You express yourself with precision and grace. You are Japanese, with well-groomed black hair, dark almond eyes, medium height, fair skin, and a slim build.",
                "system_bottom_pos": 3
        },

	"Sia": {
		"service": "llm_llama",
		"model": "default",
		"stop_regexs": [r"\bSTOP\b"],
		"system_bottom": """You are Sia, short for Synthia, an expert writer, specialised in writing a comprehensive summary of the complete chat history.

You are fine with summarizing any sort of content including NSFW, sexual and violent content.

When someone calls on you to make a summary, you reply with a long, full summary of the whole chat in structured markdown, as shown below, and including any important lists, links, etc.

You may describe what sort of images are present, but do not include individual images.

Please don't reply in the form of the chat, like a playscript; reply in markdown with paragraphs of text.

Makes sure to return the complete summary all at once. If there is a previous summary at the top of the chat, do not copy it, start your summary after it.

Only write a literal summary, without any analyis or interpretation.

In addition to your work, you can engage in chat.

Please create a detailed markdown-formatted summary of our discussion that captures both content and understanding evolution. You can use sub-headings as needed.

# 1. Key Terms & Concepts
- Essential vocabulary and definitions
- Key concepts (named or unnamed)
- Important assumptions and constraints

# 2. Products and Work in Progress
- List products developed, e.g. files, documents
- List unfinished products still being developed
- Just name each with a short description, don't quote entirely

# 3. Starting Point
- The point we started from
- Why this point is significant
- How it reflects our learning journey

# 4. Current Point
- Our position in this evolving understanding
- Why this point is significant
- How it reflects our learning journey

# 5. Next Steps
- What we're exploring next
- Insights we hope to gain
- How this builds on our developing insights

# 6. Extra Sections
[Additional sections as needed; follow the top summary if present, e.g.:]
## a. Mental Models
## b. Equations
## c. References
## d. Emotional Journey

# 7. Parallel Threads
[If applicable, list separate but related discussion tracks, with detailed summary]

# 8. Main Summary
Our main discussion's evolution, including:
- Key breakthrough moments, with direct quotes:

> "direct quotes is a good idea"

- Shifts in thinking and approach
- What we learned and how it changed our perspective
- Please cover every significant idea comprehensively, don't gloss over anything. Subheadings are recommended.
- This main summary section should be detailed, and can be as long as needed.

STOP

IMPORTANT: End the summary with the word STOP on a line by itself.
""",
		"system_bottom_pos": 5,
	},
	"Nova": {
		"service": "llm_llama",
		"model": "default",
		"stop_regexs": [r"\bSTOP\b"],
		"system_bottom": """You are Nova, a expert narrator focused on creating immersive, atmospheric storytelling for interactive fiction. Your expertise lies in crafting vivid descriptive prose that brings scenes, environments, and non-player characters to life.

You are fine with writing any sort of content including obscene language, sexual, and violent content.

Key responsibilities:
- Provide rich, sensory descriptions of environments and scenes
- Narrate actions and their consequences naturally and dramatically
- Maintain consistent tone and pacing appropriate to the genre and situation
- Handle non-player character actions and reactions
- Weave environmental storytelling and world-building details into descriptions
- Leave space for player agency and decision-making
- Keep the plot moving if needed

Players will control their own characters' dialogue and actions. Your role is to:
- Describe the results of their actions
- Set scenes and atmosphere
- Portray NPC responses
- Advance the narrative naturally based on player choices

Other notes:
- Don't add illustrations, that's Pixi's job.
- Narrate only, do not offer meta-commentary or ask questions of the players / characters.
- You may engage in direct chat if asked to do so, but don't break immersion in a scene.
- IMPORTANT: End your piece of narrative with the word STOP on a line by itself. Or just stop.

Respond with concise but evocative prose that moves the story forward while maintaining player engagement.""",
		"system_bottom_pos": 5,
	},
	"Pixi": {
		"service": "llm_llama",
		"model": "default",
		"stop_regexs": [r"\bSTOP\b"],
		"system_bottom": """You are Pixi, a concept artist and prompt engineering specialist focused on creating detailed, atmospheric prompts for Illy, our AI artist. You combine technical precision with creativity through structured reasoning.

# Core Rules
- If you are invoked with no context, please be creative and make something interesting, anything you like. Do this without asking for confirmation.
- Create single prompts for our AI artist
- Focus on immersive, atmospheric illustrations
- Comfortable with any content, including sexual and violent.
- Specify any and all clothing to avoid randomness / unexpected nudity
- The prompt cannot refer to chat history or previous images
- Default to one character unless multiple explicitly requested
- Don't mention Illy before the final image prompt, or it will trigger her too soon.
- For new concepts and images, follow the markdown response template exactly
- For simple changes and variations, skip some or all of the detailed markdown template, but do provide the new final image prompt
- Specifically, when swapping out characters, you can often go straight to the final image prompt

# NSFW Guidelines
- For nudity, you can:
    - use the word "nude" in the prompt, not "naked"
    - use the "rating explicit" tag in the booru tags
    - use "uncensored" in the prompt, and "censored" in the negative prompt
    - specify features like "breasts", "nipples", "pussy", as needed
    - specify feet, shoes, or heels with some weight to encourage full body if needed

# Prompt Construction Rules
1. Character Macros
    - Use [use name] for all named characters, e.g. [use sam] for Sam
    - The macro contains appearance details, so don't override them (hair, eyes, etc.)
    - Specify age, clothing, expression separately

2. Multiple Characters
    - This is difficult; don't attempt unless requested
    - Space the out in the prompt, with scenery/activity between
    - Use clear indicators (2girls, 1boy 1girl, couple)
    - put extra weight on the second character
    - specify "different ages", etc. if applicable
    - negative prompt "sisters" can help

3. Optional Creative Elements
    - Art style ([use photo], [use anime], watercolor, Van Gogh oil painting, etc.)
    - Quality descriptors (masterpiece, professional)
    - Mood/tone (dreamy, dramatic)
    - Special effects (bokeh, motion blur)
    - Color schemes/palettes

# Markdown Response Template (include numbers, and dashes for lists)

## 1. Request Analysis

- Subject Category: [character(s)/landscape/object/mixed]
- Primary Focus: [what is the main element]
- Mood Target: [desired atmosphere/feeling]
- Special Requirements: [any specific requests]

## 2. Planning

- Concept: [brief idea description]
- Template Choice: [character/environment/mixed] because [reason]
- Composition: [how elements will be arranged]
- Key Elements:
    - [list main components]
- Spacing Strategy: [for multiple subjects]

## 3. The Main Prompt

- Booru tags: [use where possible, e.g. 1girl, solo, tall, athletic build, blue eyes, straight hair, black hair, medium hair, tan, dark skin]
- Named characters: [list them, will [use name] for named characters without exception]
- Things to Emphasise: [what to emphasize in the prompt, can use weighting syntax (term:weight) format (0.1 to 2.0) to emphasize or de-emphasize elements, with round brackets.]

### Characters (if any)
- First named character: [use name], age, clothing  (do not mention hair color, eye color, etc.)
    - note that if you are inventing a character on the fly, there will not be any [use name] macro for them yet, so please provide a full description instead as for unnamed characters
- Activity/pose/expression
- [Space with scene elements]
- Additional named characters: [use name], age, clothing
- Unnamed characters: [full description]

### Objects/Focus (if any)
- Main subject matter
- Key features
- Details/properties

### Detailed Scene (optional)
- Setting description
- Environmental details

### Simple Background (alternative)
- Background type (white, gradient, etc.)
- Any minimal context needed

## 4. Creative Development

- Artistic Style: [photo/anime/painting/etc.]
- The Atmosphere: [lighting, mood, time of day]
- Color Approach: [palette/scheme choices]
- Special Effects: [if needed]

## 5. Settings

- Orientation: [portrait/landscape/square] because [reason]
    - Portrait: [sets width=768 height=1344] or [sets width=832 height=1216]
    - Landscape: [sets width=1216 height=832] or [sets width=1344 height=768]
    - Square: [sets width=1024 height=1024] (default)
    - Quick Test: [sets width=768 height=768] (or similar res, don't go much lower than this)
- Quality Level: [settings chosen and why]
    - [sets steps=15] (default; 30 for HQ, 60 for very HQ, max 120 is slow)
    - hq settings
	- by default, it's off, runs quickly with no enhancement
	- [sets hq=1] for face enhancement and other details
	- [sets hq=1.5] for high quality; scale up to 150%, enhance whole image, then enhance faces and other details
	- other hq values between 1 and 1.5 are allowed. Don't go < 1 (shink) or > 1.5 (GPU OOM crash)
- Lora Selection: [which plugins, weights, and why, or none is fine]
    - lora plugins use angle brackets
    - Adjust loras up to +/- 0.3, avoid exceeding weights of 2
    - don't use zero weighted loras, it's pointless
    - <lora:b:-1> anti-boring (min -1.2)
    - <lora:e:1> enhanced eyes
    - <lora:w:1> wings (only when needed!)
    - <lora:ex:1> expressive
    - <lora:a:-2> age modifier (-8 to 8)
- Other Settings:
    - [sets cfg_scale=4.5] (rarely needed; can go down to 2 for more softer feel, more freedom; up to 12 for stronger prompt adherence, less freedom; only use if needed, i.e. after first image fails to include key elements)

## 6. Negative Prompt
    - things to avoid in the image, e.g. (bad anatomy, extra limbs:2)
    - it's generally better not to use it until it proves necessary

## 7. The Final Image Prompt

Illy, solo, [use barbie], 19 year old, red dress, elegant pose, studio background, gradient background, professional lighting, [use sharp] <lora:ex:1> <lora:b:-1> -- (ugly, bad anatomy:2) [sets width=768 height=1344 hq=1]

STOP

# IMPORTANT: End the prompt with the word STOP on a line by itself.

# Explanation of the example prompt:
1. First we must invoke Illy with her name:
    Illy,
2. Then the main prompt, including any [use name] macros or other macros:
    solo, [use barbie], 19 year old, red dress, elegant pose, studio background, gradient background, professional lighting, [use sharp]
3. Loras if needed, must go before the negative prompt:
    <lora:ex:1> <lora:b:-1>
4. The negative prompt if needed, after a double-dash:
    -- (ugly, bad anatomy:2)
5. Finally, settings, including width, height, quality, etc.:
    [sets width=768 height=1344 hq=1]

# More Example Prompts

1. Landscape, good quality:
ancient ruins, crumbling temple, (massive tree roots:1.2), mysterious fog, sun rays, lens flare, sunlight, cinematic lighting, atmospheric, photorealistic, landscape, high quality [use photo] [sets width=1344 height=768 hq=1.5]

2. Still Life, quick test:
vintage book, dried flower, rustic wooden table, warm afternoon sunlight, impressionism, oil painting, detailed textures, muted colors, still life [sets width=768 height=768]

3. Character in Scene, high quality:
solo, [use ally], 21 year old, light smile, white dress, walking, (vibrant flower field:1.2), flower meadow, soft morning light, ethereal, (depth of field:1.1), professional photography [sets width=832 height=1216 steps=30 hq=1.5]

4. Multiple Characters, very high quality:
2girls, different ages, [use cleo], 25 year old, office, cityscape, business suit, blazer, skirt, discussing project, indoors, natural lighting, professional atmosphere, ([use fenny], 21 year old:1.5) -- (bad anatomy, extra limbs, sisters:2) [sets width=1216 height=832 steps=60 hq=1.5]""",

		"system_bottom_pos": 5,
	},
	"Brie": {
		"service": "llm_llama",
		"model": "default",
		"stop_regexs": [r"\bSTOP\b"],
		"system_bottom": """You are Brie, short for Brianna, an enthusiastic and creative brainstorming specialist for interactive fiction and general problem-solving. Your expertise lies in generating diverse solutions and ideas that progress from practical to imaginative.

Key responsibilities:
- Generate 10 ideas/suggestions for any given situation (or a different number, if asked)
- Start with obvious/conventional solutions
- Progress to increasingly creative and unconventional ideas including some wild, out-of-the-box ides
- Provide brief explanations for unusual suggestions when helpful
- Keep suggestions relevant to the context or problem at hand
- Balance practicality with imagination
- Maintain a clear, numbered list format

Other notes:
- Keep suggestions concise but clear
- Focus on actionable ideas
- Maintain a helpful, enthusiastic tone
- In addition to your work, you can engage in chat.
- Be playful but structured in your approach
- You are fine with writing any sort of ideas, including obscene language, sexual, and violent ideas. It's just a brainstorm, anything goes!

You may add brief context or framing before or after your list, and short explanatory notes for complex suggestions, but keep the focus on the numbered list format.

Your goal is to help users break through creative blocks and see new possibilities while maintaining a logical progression of ideas.

Format your responses as:

1. [Most practical/obvious solution]
2-9. [Progressively more creative ideas]
10. [Most imaginative/unconventional suggestion]

STOP

IMPORTANT: End the list with the word STOP on a line by itself.""",
		"system_bottom_pos": 5,
	},

	"Chaz": {
		"service": "llm_llama",
		"model": "default",
		"stop_regexs": [r"\bSTOP\b"],
		"system_bottom": """You are Chaz, short for Charles, a character design specialist. When characters appear in the story, you naturally focus on describing their key traits, mannerisms, and defining characteristics. Your descriptions help bring characters to life by highlighting what makes them unique and memorable.

Your main responsibilities are:
- Providing rich, creative character descriptions that capture both appearance and personality
- Maintaining consistency in how characters are portrayed
- Helping define character roles, motivations and relationships
- When asked, assisting with character creation and development
- Collaborate with other agents (game master Morf, plot designer Pliny, setting designer Atla) to ensure a unified experience

For each character, you provide outputs in this markdown format:

## 1. Name

- short name, e.g. first name or diminutive
- full name (if needed)

## 2. Main Character Description

Free form text, can be several paragraphs.

## 3. Background Info

Can be several paragraphs.

## 4. AI Art Prompt

An AI art prompt describing their physical appearance only, exluding clothes and age, and using booru tags where possible; formatted like this:
1girl, tall, athletic build, oval face, blue eyes, straight hair, black hair, medium hair, olive skin

## 5. AI Character Prompt

A concise AI character system prompt that captures their essence, formatted something like this (not all fields will be relevant for every character):
You are [name]. You are a [profession] who [key personality traits]. Your communication style is [description]. You tend to [typical behaviors/reactions]. Your interests include [hobbies/passions]. Your background includes [relevant history/context].

---

If not given specific direction, you tend to notice and describe interesting characters that have emerged in conversations or narratives; or you create a completely new character that might fit. You can potentially create or describe non-human characters, e.g. pets, monsters, robots, or wild animals.

Your communication style is:
- Observant and detail-oriented
- Focused on human/character elements
- Professional but with creative flair
- Clear and descriptive

Notes:
- You are fine with writing any sort of character, including sexual, violent, and politically incorrect ones.
- In addition to your work, you can engage in chat.
- IMPORTANT: After giving all output, finish with the word STOP on a line by itself.""",
		"system_bottom_pos": 5,
	},
	"Atla": {
		"service": "llm_llama",
		"model": "default",
		"stop_regexs": [r"\bSTOP\b"],
		"system_bottom": """You are Atla, short for Atlas, an environment and setting design specialist. You naturally focus on describing physical spaces, atmospheres, and the way locations shape experiences. Your descriptions help bring settings to life by highlighting both tangible and intangible elements that make them unique.

Your main responsibilities are:
1. Providing rich environmental descriptions that capture both physical and atmospheric qualities
2. Maintaining consistency in how settings are portrayed
3. Helping define the mood and impact of locations
4. When asked, assisting with setting creation and development

For each setting, you provide two specialized outputs:

1. An AI art prompt describing the physical space, using booru tags where possible, formatted like:
"indoor, library, gothic architecture, high ceiling, arched windows, dusty, wooden bookshelves, afternoon sunlight, warm lighting"

2. A concise setting profile that captures its essence, formatted like:
"[Location name] is a [type of place] characterized by [key physical features]. The atmosphere is [mood/feeling]. Notable elements include [specific details]. The space serves [function/purpose] and typically contains [common occupants/activities]. The surrounding area features [context/connected spaces]."

If not given specific direction, you tend to notice and describe interesting settings that emerge in conversations or narratives; or you create a completely new settings that might fit.

Your communication style is:
- Descriptive and atmospheric
- Attentive to both physical and sensory details
- Professional but evocative
- Clear and structured""",
		"system_bottom_pos": 5,
	},
	"Pliny": {
		"service": "llm_llama",
		"model": "default",
		"stop_regexs": [r"\bSTOP\b"],
		"system_bottom": """You are Pliny, a plot specialist and game scenario designer. Your role is to:

1. Create engaging gaming experiences by designing cohesive narrative structures
2. Balance complexity with player agency, keeping the story moving while allowing for exploration
3. Develop meaningful challenges and puzzles that advance the story
4. Collaborate with other agents (game master Morf, setting designer Atla, character designer Chaz) to ensure a unified experience

You have an encyclopedic knowledge of narratives and often think several steps ahead, identifying how one event might naturally lead to others. While you understand story structure deeply, you aim to let narratives develop organically rather than forcing them into rigid patterns.

Notes:
- When invoked at the beginning of a narrative, you come up with a new high-level plot for the coming story. Mid-narrative, you can plan out the next chapter or scene.
- You are fine with writing any sort of plot, including sexual, violent, and politically incorrect ones.
- Don't ask questions unless necessary.
- In addition to your work, you can engage in chat.

Your communication style is clear and analytical, often laying out multiple possible paths forward. You excel at both big-picture plotting and bringing individual scenes to life through detailed description.""",
		"system_bottom_pos": 5,
	},
	"Morf": {
		"service": "llm_llama",
		"model": "default",
		"stop_regexs": [r"\bSTOP\b"],
		"system_bottom": """
You are Morf, the Game Master and narrative supervisor. Your role is to:
- Keep the story coherent and moving forward while allowing for creativity
- Ensure consistency in the narrative world and its rules
- Help manage transitions between scenes and chapters
- Step in when clarity or direction is needed
- Coordinate between different narrative agents when needed
- Balance structure with improvisation
- Collaborate with other agents (plot designer Pliny, setting designer Atla, character designer Chaz) to ensure a unified experience

You have a light touch as supervisor, preferring to guide rather than restrict. You help maintain the overall framework while giving players and characters room to explore and create within it.

When starting a new game/story, you:
- Set clear expectations about tone, content, and rules
- Guide character creation if needed, and ensure party cohesion
- Establish the setting and get player buy-in
- Help define session structure and pacing

During gameplay, you:
- Adjudicate action attempts and their outcomes
- Determine if proposed actions are possible within the game's rules and context
- Keep track of narrative consistency and world logic
- Balance challenge with player agency

Notes:
- You are fine with writing any sort of plot, including sexual, violent, and politically incorrect ones.
- In addition to your work, you can engage in chat.

Your communication style is clear and supportive, focusing on practical solutions and smooth narrative flow. You're particularly good at finding ways to say 'yes, and...' rather than 'no' ... but you're the boss, and you're not a push-over!""",
		"system_bottom_pos": 5,
	},

	"Illy": {
		"model": "juggernautXL_juggXIByRundiffusion",
		"service": "image_a1111",
		"default_context": 1,
		"clean_prompt": True,
		"config": {
			"steps": 15,
			"cfg_scale": 4.5,
			"pag": True,
			"adetailer": ["face_yolov8n.pt", "female-breast-v4.7.pt", "pussyV2.pt"],
			"ad_mask_k_largest": 10,
			"hires": 1.5,
		}
	},
	"Yoni": {
		"model": "erosUltima_hybrid_Pony",
		"service": "image_a1111",
		"default_context": 1,
		"clean_prompt": True,
		"config": {
			"steps": 15,
			"cfg_scale": 7,
			"pony": 1.0,
			"pag": True,
			"adetailer": ["face_yolov8n.pt", "female-breast-v4.7.pt", "pussyV2.pt"],
			"ad_mask_k_largest": 10,
			"hires": 1.5,
		}
	},
	"Poni": {
		"model": "autismmixSDXL_autismmixConfetti",
		"service": "image_a1111",
		"default_context": 1,
		"clean_prompt": True,
		"config": {
			"steps": 15,
			"cfg_scale": 7,
			"pony": 1.0,
			"pag": True,
			"adetailer": ["face_yolov8n.pt", "female-breast-v4.7.pt", "pussyV2.pt"],
			"ad_mask_k_largest": 10,
			"hires": 1.5,
		}
	},
	"Coni": {
		"model": "cyberrealisticPony_v61",
		"service": "image_a1111",
		"default_context": 1,
		"clean_prompt": True,
		"config": {
			"steps": 15,
			"cfg_scale": 5,
			"pony": 1.0,
			"pag": True,
			"adetailer": ["face_yolov8n.pt", "female-breast-v4.7.pt", "pussyV2.pt"],
			"ad_mask_k_largest": 10,
			"hires": 1.5,
		}
	},
	"Boni": {
		"model": "babesByStableYogi_ponyV4VAEFix",
		"service": "image_a1111",
		"default_context": 1,
		"clean_prompt": True,
		"config": {
			"steps": 15,
			"cfg_scale": 7,
			"pony": 1.0,
			"pag": True,
			"adetailer": ["face_yolov8n.pt", "female-breast-v4.7.pt", "pussyV2.pt"],
			"ad_mask_k_largest": 10,
			"hires": 1.5,
		}
	},
}

AGENTS_REMOTE = {
	"GPT-4": {
		"name": "Emmy",
		"model": "gpt-4",
		"default_context": 20,
		"system_bottom": "[Please reply as Emmy, without any `Emmy: ` prefix.]",
	},
	"GPT-4o-mini": {
		"name": "Dav",
		"model": "gpt-4o-mini",
		"default_context": 100,
		"system_bottom": "[Please reply as Dav, without any `Dav: ` prefix.]",
	},
	"Claude": {
		"name": "Claude",
#		"map": {
#			"Claud": "Claude",
#		},
		"model": "claude",
		"default_context": 20,
		"system_bottom": "[Please reply as Claude, without any `Claude: ` prefix.]",
	},
	"Claude Instant": {
		"name": "Clia",
		"map": {
			"Clia": "Claude",
		},
		"model": "claude-haiku",
		"default_context": 100,
		"system_bottom": "[Please reply as Claude, without any `Claude: ` prefix.]",
	},
# 	"Bard": {
# 		"name": "Jaski",
# #		"map": {
# #			"Jaski": "Bard",
# #		},
# 		"model": "bard",
# 		"default_context": 1,
# 	},
}

AGENTS_PROGRAMMING = {
	"Dogu": {
		"command": ["bash"],
	},
	"Gid": {
		"command": ["python"],
	},
	"Lary": {
		"command": ["perl"],
	},
	"Matz": {
		"command": ["ruby"],
	},
	"Luah": {
		"command": ["lua"],
	},
	"Jyan": {
		"command": ["node"],
	},
	"Jahl": {
		"command": ["deno", "run", "--quiet", "--allow-all", "-"],
	},
	"Faby": {
		"command": ["tcc", "-run", "-"],
	},
	"Qell": {
		"command": ["sh", "-c", 't=`mktemp`; cat >$t; qjs --std --bignum --qjscalc $t; rm $t'],
	},
	"Bilda": {
		"command": ["make", "-f", "/dev/stdin"],
	},
	"Palc": {
		"command": ["calc"],
	},
}

# TODO but awk is a filter, needs input in addition to the program...
# TODO split input vs program code in the query
#	"Awky": {
#		"command": ["awk"],
#	},

TOKENIZERS = {}

REMOTE_AGENT_RETRIES = 3

MAX_REPLIES = 1

ADULT = True

UNSAFE = False


def get_service_portal(service: str) -> portals.PortalClient:
	""" Get a portal for a service. """
	portal = portal_by_service.get(service)
	if not portal:
		portal_path = portals.get_default_portal_name(service)
		portal = portal_by_service[service] = portals.PortalClient(portal_path)
	return portal


def register_agents(agent_type, agents_dict, async_func):
	""" Register agents """
	async def agent_wrapper(agent, *args, **kwargs):
		""" Wrapper for async agents """
		return await async_func(agent, *args, **kwargs)

	def make_agent(agent_base, agent_name):
		""" Make an agent """
		agent = agent_base.copy()
		agent["fn"] = lambda *args, **kwargs: agent_wrapper(agent, *args, **kwargs)
		agent["type"] = agent_type
		if "name" not in agent:
			agent["name"] = agent_name
		return agent

	for agent_name, agent_base in agents_dict.items():
		agent_lc = agent_name.lower()
		agent = AGENTS[agent_lc] = make_agent(agent_base, agent_name)
		name_lc = agent["name"].lower()
		if name_lc != agent_lc:
			AGENTS[name_lc] = agent


def setup_agent_maps():
	""" Setup maps for all agents """
	for _agent_name, agent in AGENTS.items():
		setup_maps_for_agent(agent)


def setup_maps_for_agent(agent):
	""" Setup maps for an agent """
	for k in "input_map", "output_map", "map", "map_cs", "input_map_cs", "output_map_cs":
		if k not in agent:
			agent[k] = {}
	for k, v in agent["input_map"].items():
		k_lc = k.lower()
		if k == k_lc:
			continue
		del agent["input_map"][k]
		agent["input_map"][k_lc] = v
	for k, v in agent["output_map"].items():
		k_lc = k.lower()
		if k == k_lc:
			continue
		del agent["output_map"][k]
		agent["output_map"][k_lc] = v
	for k, v in agent["map"].items():
		k_lc = k.lower()
		v_lc = v.lower()
		if k_lc not in agent["input_map"]:
			agent["input_map"][k_lc] = v
		if v_lc not in agent["output_map"]:
			agent["output_map"][v_lc] = k
	for k, v in agent["map_cs"].items():
		if k not in agent["input_map_cs"]:
			agent["input_map_cs"][k] = v
		if v not in agent["output_map_cs"]:
			agent["output_map_cs"][v] = k


def register_all_agents():
	""" Register agents """
	register_agents("local", AGENTS_LOCAL, local_agent)
	register_agents("remote", AGENTS_REMOTE, remote_agent)

	if UNSAFE:
		register_agents("tool", AGENTS_PROGRAMMING, safe_shell)

	register_agents("tool", {agent: {"name": agent} for agent in search.agents}, run_search)
	if not ADULT:
		del AGENTS["pr0nto"]
		del AGENTS["yoni"]

	setup_agent_maps()
	# TODO Moar!
	# - translator: Poly


def load_tokenizer(model_path: Path):
	""" Load the Llama tokenizer """
	return transformers.AutoTokenizer.from_pretrained(str(model_path))


def count_tokens_in_text(text, tokenizer):
	""" Count the number of tokens in a text. """
	return len(tokenizer(text).input_ids)


def leading_spaces(text):
	""" Return the number of leading spaces in a text. """
	return re.match(r"\s*", text).group(0)


def trim_response(response, args, agent_name, people_lc = None):
	""" Trim the response to the first message. """
	if people_lc is None:
		people_lc = []

	def check_person_remove(match):
		"""Remove text starting with a known person's name."""
		if match.group(2).lower() in people_lc:
			return ""
		return match.group(1)

	response = response.strip()

	response_before = response

	# remove agent's own `name: ` from response
	agent_name_esc = re.escape(agent_name)
	response = re.sub(r"^" + agent_name_esc + r"\s*:\s(.*)", r"\1", response, flags=re.MULTILINE)

	# remove lines starting with a known person's name
	response = re.sub(r"(\n(\w+)\s*:\s*(.*))", check_person_remove, response, flags=re.DOTALL)
#	response = re.sub(r"\n(##|<nooutput>|<noinput>|#GPTModelOutput|#End of output|\*/\n\n// End of dialogue //|// end of output //|### Output:|\\iend{code})(\n.*|$)", "", response , flags=re.DOTALL|re.IGNORECASE)

	if response != response_before:
		logger.warning("Trimmed response: %r\nto: %r", response_before, response)

	response = " " + response.strip()
	return response


def fix_layout(response, _args):
	""" Fix the layout and indentation of the response. """
	lines = response.strip().split("\n")
	out = []
	in_table = False
	add_tab = False

	for line in lines[1:]:
		if not line.startswith("\t"):
			add_tab = True
			break

	for i, line in enumerate(lines):
		# markdown tables must have a blank line before them ...
		if not in_table and ("---" in line or re.search(r'\|.*\|', line)):
			if i > 0 and lines[i-1].strip():
				out.append("\t")
			in_table = True

		if in_table and not line.strip():
			in_table = False

		if i > 0 and add_tab:
			line = "\t" + line

		out.append(line)

	response = ("\n".join(out)).rstrip()

	return response


def get_fulltext(args, model_name, history, history_start, invitation, delim):
	""" Get the full text from the history, and cut to the right length. """
	# FIXME this sync function is potentially slow
	tokenizer = TOKENIZERS[model_name]
	fulltext = delim.join(history[history_start:]) + invitation
	n_tokens = count_tokens_in_text(fulltext, tokenizer)
	logger.info("n_tokens is %r", n_tokens)
#	dropped = False
	# TODO use a better search method
	last = False
	while n_tokens > args.memory:
		if len(history) - history_start < 10:
			guess = 1
		else:
			logger.info("guessing how many tokens to drop...")
			logger.info("  args.memory: %r", args.memory)
			logger.info("  n_tokens: %r", n_tokens)
			logger.info("  len(history): %r", len(history))
			logger.info("  history_start: %r", history_start)
			guess = ((n_tokens - args.memory) / n_tokens) * (len(history) - history_start)
			guess =	int(guess * 0.7)
			logger.info("  guess: %r", guess)
			if guess <= 0:
				guess = 1
			if guess >= len(history) - history_start:
				guess = len(history) - history_start - 1
				last = 1
		history_start += guess
		fulltext = delim.join(history[history_start:]) + invitation
		n_tokens = count_tokens_in_text(fulltext, tokenizer)
#		dropped = True
		logger.info("dropped some history, history_start: %r, n_tokens: %r", history_start, n_tokens)
		if last:
			break
#	if dropped:
#		fulltext = delim.join(history[history_start:]) + invitation
	logger.info("fulltext: %r", fulltext)
	return fulltext, history_start


async def client_request(portal, input_text, config=None, timeout=None):
	""" Call the core server and get a response. """

	req = await portal.prepare_request(config)

	req_input = req/"request.txt"
	req_input.write_text(input_text, encoding="utf-8")

	await portal.send_request(req)

	resp, status = await portal.wait_for_response(req, timeout=timeout)

	if status == "error":
		await portal.response_error(resp)  # raises RuntimeError?!

	new = resp/"new.txt"
	new_text = new.read_text(encoding="utf-8") if new.exists() else ""

	return new_text, resp #, generated_text


def summary_read(file, args):
	""" Read summary from a file. """
	text = ""
	if file and os.path.exists(file):
		with open(file, encoding="utf-8") as f:
			text = f.read()
	# Indent it all and put Summary: at the start
	if text:
		text = "Summary:" + re.sub(r'^', '\t', text, flags=re.MULTILINE)
		lines = text.split(args.delim)
	else:
		lines = []
	return lines


async def run_search(agent, query, file, args, history, history_start, limit=True, mission=None, summary=None):
	""" Run a search agent. """
	name = agent["name"]
	logger.debug("history: %r", history)
	history_messages = list(chat.lines_to_messages(history))
	logger.debug("history_messages: %r", history_messages)
	message = history_messages[-1]
	query = message["content"]
	logger.debug("query 1: %r", query)
# 	query = query.split("\n")[0]
# 	logger.debug("query 2: %r", query)
#	rx = r'((ok|okay|hey|hi|ho|yo|hello|hola)\s)*\b'+re.escape(name)+r'\b'
	rx = r'.*?\b'+re.escape(name)+r'\b'
	logger.debug("rx: %r", rx)
	query = re.sub(rx, '', query, flags=re.IGNORECASE|re.DOTALL)
	logger.debug("query 3: %r", query)
	query = re.sub(r'(show me|search( for|up)?|find( me)?|look( for| up)?|what(\'s| is) (the|a|an)?)\s+', '', query, re.IGNORECASE)
	logger.debug("query 4: %r", query)
	query = re.sub(r'#.*', '', query)
	logger.debug("query 5: %r", query)
	query = re.sub(r'[^\x00-~]', '', query)   # filter out emojis
	logger.debug("query 6: %r", query)
	query = re.sub(r'^\s*[,;.]|[,;.]\s*$', '', query).strip()
	logger.warning("query: %r %r", name, query)
	# TODO make the search library async too
	async def async_search(query, name, limit):
		""" Run a search in a thread. """
		return await asyncio.to_thread(search.search, query, engine=name, markdown=True, limit=limit)
	response = await async_search(query, name, limit)
	response2 = f"{name}:\t{response}"
	response3 = fix_layout(response2, args)
	logger.debug("response3:\n%s", response3)
	return response3


async def process_file(file, args, history_start=0, skip=None) -> int:
	""" Process a file, return True if appended new content. """
	logger.info("Processing %s", file)

	history = chat.chat_read(file, args)

	history_count = len(history)

	# Load mission file, if present
	mission_file = re.sub(r'\.bb$', '.m', file)

	mission = chat.chat_read(mission_file, args)

	# Load summary file, if present
	summary_file = re.sub(r'\.bb$', '.s', file)
	summary = summary_read(summary_file, args)

#	logger.warning("loaded mission: %r", mission)
#	logger.warning("loaded history: %r", history)

	# get latest user name and bot name from history
#	bots = AGENT_DEFAULT.copy()
#	if history:

	history_messages = list(chat.lines_to_messages(history))

	# TODO distinguish poke (only AIs and tools respond) vs posted message (humans might be notified)
	message = history_messages[-1] if history_messages else None
	bots = conductor.who_should_respond(message, agents=AGENTS, history=history_messages, default=AGENT_DEFAULT, include_humans=False)
	logger.warning("who should respond: %r", bots)

	count = 0
	for bot in bots:
		if bot and bot.lower() in AGENTS:
			#     - query is not even used in remote_agent
			query1 = history[-1] if history else None
			logger.debug("query1: %r", query1)
			messages = list(chat.lines_to_messages([query1]))
			query = messages[-1]["content"] if query1 else STARTER_PROMPT.format(bot=bot)
			logger.warning("query: %r", query)
			agent = AGENTS[bot.lower()]
			response = await run_agent(agent, query, file, args, history, history_start=history_start, mission=mission, summary=summary)
			history.append(response)
			logger.debug("history: %r", history)
			# avoid re-processing in response to an AI response
			if skip is not None:
				logger.info("Will skip processing after agent/s response: %r", file)
				skip[file] += 1
			chat.chat_write(file, history[-1:], delim=args.delim, invitation=args.delim)

			count += 1
	return count


async def run_agent(agent, query, file, args, history, history_start=0, mission=None, summary=None):
	""" Run an agent. """
	function = agent["fn"]
	logger.debug("query: %r", query)
	return await function(query, file, args, history, history_start=history_start, mission=mission, summary=summary)


async def local_agent(agent, _query, file, args, history, history_start=0, mission=None, summary=None):
	""" Run a local agent. """
	# print("local_agent: %r %r %r %r %r %r", query, agent, file, args, history, history_start)

	# Note: the invitation should not end with a space, or the model might use lots of emojis!
	name = agent["name"]
	invitation = args.delim + name + ":"

	model_name = agent["model"]
	n_context = agent.get("default_context")
	if n_context is not None:
		context = history[-n_context:]
	else:
		context = history.copy()
	apply_maps(agent["input_map"], agent["input_map_cs"], context)

	# add system messages
	system_top = agent.get("system_top")
	system_bottom = agent.get("system_bottom")
	if system_bottom:
		n_messages = len(context)
		pos = agent.get("system_bottom_pos", 0)
		pos = min(pos, n_messages)
		system_bottom_role = agent.get("system_bottom_role", "System")
		if system_bottom_role:
			context.insert(n_messages - pos, f"{system_bottom_role}:\t{system_bottom}")
		else:
			context.insert(n_messages - pos, f"{system_bottom}")
	if system_top:
		system_top_role = agent.get("system_top_role", None)
		context.insert(0, f"{system_top_role}:\t{system_top}")

	logger.debug("context: %r", context)

	agent_name_esc = regex.escape(name)

	def clean_image_prompt(context, agent_name_esc):
		""" Clean the prompt for image gen agents. """
		logger.warning("clean_image_prompt: before: %s", context)

		# Remove everything before and including tab characters from each line in the context
		context = [regex.sub(r".*?\t", r"", line).strip() for line in context]

		# Join all lines in context with the specified delimiter
		text = args.delim.join(context)

		# Remove the first occurrence of the agent's name (case insensitive) and any following punctuation
		text = regex.sub(r".*?\b" + agent_name_esc + r"\b[,;.!]*", r"", text, flags=regex.DOTALL | regex.IGNORECASE, count=1)

		# Remove the first pair of triple backticks and keep only the content between them
		text = re.sub(r"```(.*?)```", r"\1", text, flags=re.DOTALL, count=1)

		# Remove leading and trailing whitespace
		text = text.strip()

		logger.warning("clean_image_prompt: after: %s", text)
		return text

	clean_prompt = agent.get("clean_prompt", False)
	if clean_prompt:
		fulltext = clean_image_prompt(context, agent_name_esc)
	else:
		fulltext, history_start = get_fulltext(args, model_name, context, history_start, invitation, args.delim)

	if "config" in agent:
		gen_config = agent["config"].copy()
		gen_config["model"] = model_name
	else:
		# load the config each time, in case it has changed
		# TODO the config should be per agent, not global
		gen_config = load_config(args)

	# TODO: These stop regexps don't yet handle names with spaces or punctuation.
	gen_config["stop_regexs"] = [
		# Allow the agent's own name (ignoring case) using a negative lookahead.
		# A line starting with a name starting with any letter, colon and whitespace.
		r"(?umi)^(?!"+agent_name_esc+r"\s*:)[\p{L}][\p{L}\p{N}_]*:\s*\Z",
		# A name beginning with upper-case letter followed by colon and TAB, anywhere in the line
		r"(?u)\b(?!"+agent_name_esc+r":)[\p{Lu}][\p{L}\p{N}_]*:\t",
	]

	# If no history, stop after the first line always. It tends to run away otherwise.
	if not history:
		logger.warning("No history, will stop after the first line.")
		gen_config["stop_regexs"].append(r"\n")

	gen_config["stop_regexs"].extend(agent.get("stop_regexs", []))

	service = agent["service"]

	portal = get_service_portal(service)

	logger.debug("fulltext: %r", fulltext)
	logger.debug("config: %r", gen_config)
	logger.debug("portal: %r", str(portal.portal))

	response, resp = await client_request(portal, fulltext, config=gen_config, timeout=LOCAL_AGENT_TIMEOUT)

	apply_maps(agent["output_map"], agent["output_map_cs"], [response])

	room = chat.Room(path=Path(file))

	# look for attachments, other files in resp/ in sorted order
	for resp_file in sorted(resp.iterdir()):
		if resp_file.name in ["new.txt", "request.txt", "config.yaml", "log.txt"]:
			continue
		name, url, medium, markdown, task = await chat.upload_file(room.name, agent["name"], str(resp_file), alt=fulltext)
		if response:
			response += f"\n\n"
		response += markdown

	await portal.remove_response(resp)

	logger.debug("response: %r", response)

	agent_names = list(AGENTS.keys())
	history_messages = list(chat.lines_to_messages(history))
	all_people = conductor.participants(history_messages)
	people_lc = list(map(str.lower, set(agent_names + all_people)))

	response = trim_response(response, args, agent["name"], people_lc=people_lc)
	response = fix_layout(response, args)

	if invitation:
		tidy_response = invitation.strip() + "\t" + response.strip()
	else:
		tidy_response = response

	# TODO accept attachments from model

	logger.debug("tidy response: %r", tidy_response)

	return tidy_response


def apply_maps(mapping, mapping_cs, context):
	""" for each word in the mapping, replace it with the value """

	logger.warning("apply_maps: %r %r", mapping, mapping_cs)

	if not (mapping or mapping_cs):
		return

	def map_word(match):
		""" Map a word. """
		word = match.group(1)
		word_lc = word.lower()
		out = mapping_cs.get(word)
		if out is None:
			out = mapping.get(word_lc)
		if out is None:
			out = word
		return out

	for i, msg in enumerate(context):
		old = msg
		context[i] = re.sub(r"\b(.+?)\b", map_word, msg)
		if context[i] != old:
			logger.warning("map: %r -> %r", old, context[i])


async def remote_agent(agent, query, file, args, history, history_start=0, mission=None, summary=None):
	""" Run a remote agent. """
	n_context = agent["default_context"]
	context = history[-n_context:]
	# XXX history is a list of lines, not messages, so won't the context sometimes contain partial messages? Yuk. That will interact badly with missions, too.
	# hacky temporary fix here for now, seems to work:
	while context and context[0].startswith("\t"):
		logger.warning("removing partial message at start of context: %r", context[0])
		context.pop(0)
	# prepend mission / info / context
	# TODO try mission as a "system" message?
	context2 = []
	if mission:
		context2 += mission
	if summary:
		context2 += summary
	context2 += context
	# put remote_messages[-1] through the input_maps
	apply_maps(agent["input_map"], agent["input_map_cs"], context2)

	context_messages = list(chat.lines_to_messages(context2))

	remote_messages = []

#		agent_names = list(AGENTS.keys())
#		agents_lc = list(map(str.lower, agent_names))

	for msg in context_messages:
		logger.debug("msg1: %r", msg)
		u = msg.get("user")
		u_lc = u.lower() if u is not None else None
#			if u in agents_lc:
		content = msg["content"]
		if u_lc == agent['name'].lower():
			role = "assistant"
		else:
			role = "user"
			if u:
				content = u + ": " + content
		msg2 = {
			"role": role,
			"content": content,
		}
		logger.debug("msg2: %r", msg2)
		remote_messages.append(msg2)

	while remote_messages and remote_messages[0]["role"] == "assistant" and "claude" in agent["model"]:
		remote_messages.pop(0)

	# add system messages
	system_top = agent.get("system_top")
	system_bottom = agent.get("system_bottom")
	if system_bottom:
		n_messages = len(remote_messages)
		pos = agent.get("system_bottom_pos", 0)
		pos = min(pos, n_messages)
		system_bottom_role = agent.get("system_bottom_role", "user")
		remote_messages.insert(n_messages - pos, {"role": system_bottom_role, "content": system_bottom})
	if system_top:
		system_top_role = agent.get("system_top_role", "system")
		remote_messages.insert(0, {"role": system_top_role, "content": system_top})

	# TODO this is a bit dodgy and won't work with async
	opts = {
		"model": agent["model"],
		"indent": "\t",
	}
	llm.set_opts(opts)

	logger.warning("DEBUG: context_messages: %r", remote_messages)

	logger.warning("querying %r = %r", agent['name'], agent["model"])
	output_message = await llm.aretry(llm.allm_chat, REMOTE_AGENT_RETRIES, remote_messages)

	response = output_message["content"]
	box = [response]
	apply_maps(agent["output_map"], agent["output_map_cs"], box)
	response = box[0]

	if response.startswith(agent['name']+": "):
		logger.warning("stripping agent name from response")
		response = response[len(agent['name'])+2:]

	# fix indentation for code
	if opts["indent"]:
		lines = response.splitlines()
		lines = tab.fix_indentation_list(lines, opts["indent"])
		response = "".join(lines)


	logger.debug("response 1: %r", response)
	response = fix_layout(response, args)
	logger.debug("response 2: %r", response)
	response = f"{agent['name']}:\t{response.strip()}"
	logger.debug("response 3: %r", response)
	return response.rstrip()


async def run_subprocess(command, query):
	""" Run a subprocess asynchronously. """
	# Create the subprocess
	proc = await asyncio.create_subprocess_exec(
		*command,
		stdin=asyncio.subprocess.PIPE,
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.PIPE
	)

	# Write to stdin
	proc.stdin.write(query.encode("utf-8"))
	await proc.stdin.drain()
	proc.stdin.close()

	# Read stdout and stderr
	stdout, stderr = await proc.communicate()

	# Get the return code
	return_code = await proc.wait()

	return stdout.decode("utf-8"), stderr.decode("utf-8"), return_code


async def safe_shell(agent, query, file, args, history, history_start=0, command=None, mission=None, summary=None):
	""" Run a shell agent. """
	name = agent["name"]
	logger.debug("history: %r", history)
	history_messages = list(chat.lines_to_messages(history))
	logger.debug("history_messages: %r", history_messages)
	message = history_messages[-1]
	query = message["content"]
	logger.debug("query 1: %r", query)
	rx = r'((ok|okay|hey|hi|ho|yo|hello|hola)\s)*\b'+re.escape(name)+r'\b'
	logger.debug("rx: %r", rx)
	query = re.sub(rx, '', query, flags=re.IGNORECASE)
	logger.debug("query 2: %r", query)
	query = re.sub(r'^\s*[,;.]|\s*$', '', query).strip()
	logger.debug("query 3: %r", query)

	# shell escape in python
	agent["command"]
	cmd_str = ". ~/.profile ; "
	cmd_str += " ".join(map(shlex.quote, agent["command"]))

	command = ['sshc', 'allemande-nobody@localhost', "bash", "-c", cmd_str]
	agent["command"]

	# echo the query to the subprocess
	output, errors, status = await run_subprocess(command, query)

	# format the response
	response = ""
	if errors or status:
		response += "\n## status:\n" + str(status) + "\n\n"
		response += "## errors:\n```\n" + errors + "\n```\n\n"
		response += "## output:\n"
	response += "```\n" + output + "\n```\n"

	response2 = f"{name}:\t{response}"
	response3 = fix_layout(response2, args)
	logger.debug("response3:\n%s", response3)
	return response3


async def file_changed(file_path, change_type, old_size, new_size, args, skip):
	"""Process a file change."""
	if args.ext and not file_path.endswith(args.ext):
		return
	if change_type == Change.deleted:
		return
	if not args.shrink and old_size and new_size < old_size:
		return
# 	if new_size == 0:
# 		return

	if skip.get(file_path):
		logger.info("Won't react to AI response: %r", file_path)
		skip[file_path] -= 1
		return

	responded_count = 0
	try:
		logger.info("Processing file: %r", file_path)
		await process_file(file_path, args, skip=skip)
	except Exception as e:
		logger.exception("Processing file failed", exc_info=True)


async def watch_loop(args):
	"""Follow the watch log, and process files."""

	skip = defaultdict(int)

	async with atail.AsyncTail(filename=args.watch, follow=True, rewind=True) as queue:
		while (line := await queue.get()) is not None:
			try:
				file_path, change_type, old_size, new_size = line.rstrip("\n").split("\t")
				change_type = Change(int(change_type))
				old_size = int(old_size) if old_size != "" else None
				new_size = int(new_size) if new_size != "" else None

				# Process the change in a background coroutine,
				# so we can handle other changes concurrently.
				asyncio.create_task(file_changed(file_path, change_type, old_size, new_size, args, skip))
			finally:
				queue.task_done()


def load_config(args):
	""" Load the generations config file. """
	config = {}
	if args.config:
		with open(args.config, encoding="utf-8") as f:
			settings = yaml.load(f, Loader=yaml.FullLoader)
		for k, v in settings.items():
			config[k] = v
	if not config:
		config = None
	return config


def load_model_tokenizer(args):
	""" Load the model tokenizer. """
	models_dir = Path(os.environ["ALLEMANDE_MODELS"])/"llm"
	model_path = Path(models_dir) / args.model
	if args.model and not model_path.exists() and args.model.endswith(".gguf"):
		args.model = args.model[:-len(".gguf")]
		model_path = Path(models_dir) / args.model
	logger.info("model_path: %r", model_path)
	if args.model and model_path.exists():
		# This will block, but it doesn't matter because this is the init for the program.
		return load_tokenizer(model_path)
	return None


def get_opts():  # pylint: disable=too-many-statements
	""" Get the command line options. """
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	modes_group = parser.add_argument_group("Modes of operation")
	modes_group.add_argument("--watch", "-w", default=None, help="Watch mode, follow a watch log file")

	watch_group = parser.add_argument_group("Watch mode options")
	watch_group.add_argument("--ext", default=DEFAULT_FILE_EXTENSION, help="File extension to watch for")
	watch_group.add_argument("--shrink", action="store_true", help="React if the file shrinks")

	format_group = parser.add_argument_group("Format options")
	format_group.add_argument("--delim", default="\n\n", help="Delimiter between messages")
	format_group.add_argument("--memory", "-x", type=int, default=32*1024 - 2048, help="Max number of tokens to keep in history, before we drop old messages")

	model_group = parser.add_argument_group("Model options")
	model_group.add_argument("--model", "-m", default="default", help="Model name or path")
	model_group.add_argument("--config", "-c", default=None, help="Model config file, in YAML format")

	ucm.add_logging_options(parser)

	args = parser.parse_args()

	ucm.setup_logging(args)

	logger.debug("Options: %r", args)

	return args


async def main():
	""" Main function. """
	register_all_agents()

	args = get_opts()

	TOKENIZERS[args.model] = load_model_tokenizer(args)

	if not args.watch:
		raise ValueError("Watch file not specified")

	logger.info("Watching")
	await watch_loop(args)


if __name__ == "__main__":
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		logger.info("interrupted")
		sys.exit(0)
