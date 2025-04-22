# Ally Chat &mdash; Quick Intro

Ally Chat is a multi-user chat platform with access to numerous AI models. It's open source, free to use, and lets you chat with multiple AIs and humans together.

## Getting Help

Click the `i` help icon and talk to Flashi. In the help system, AIs have access to the full user guide and can give very detailed help.

In the main public [Ally Chat](/Ally Chat) room, AIs can help with some basic info about the app.

**In other chat rooms, the AIs don't know anything at all about the app!**

Please reach out to Sam, the main developer, for support, to report bugs, and please tell him your ideas to improve Ally Chat.

You can check out the [User Guide](guide) for full details on the app, AI
models, characters, and tools. The advanced mode of the app has many options
and features, you can try that when you've mastered the basics.

## How to Talk with AIs

To talk with a specific AI character, call them by name:
   - "Ally, how are you?"
   - "Can you help, Flashi?"
   - "@Illu, let's draw a garden!"

Send an empty "poke" message to continue AI conversations. You'll need to do this after Illu writes an AI art prompt for you.

You can say "someone" for a random AI, or "everyone" for several responses.

## Select Characters and Tools

**General Chat**
- Ally, Barbie: friendly chat
- Flashi, Emmy, Claude, Gemmi: strong assistants
- Fli, Emm, Clu, Gemm: concise responses from the above

**AI Art**
- Illu, Gema: prompting
- Illy: generation

**Specialists**
- Brie: brainstorming
- Summi: summaries
- Chaz: character design
- Nova: narrative

**Search & Info**
- Goog, "Allemande AI"
- Gimg, cute animals
- UTube, indie games
- Sona, any LLM news today?

**Code & Calculation**
- Dogu, date +%F ; fortune
- Gido, import this
- Palc, sqrt(3)/2, 2**32

There are many, many more; check the guide, or try the help system!

## Rich Content Support

- Full markdown/HTML/SVG/CSS/JS runs in the chat (no backticks)
- TeX math: $y = \sqrt{x}$  and  $$ ... $$ displays
- Graphviz ```dot ```, and ```mermaid ``` diagrams
- Interactive charts, simulations, mini-games with JavaScript

## Privacy

The [Ally Chat](Ally+Chat) room is public. Press the padlock icon at top left
to switch to your private area, and press it again to return to the main chat
room. You can also click your name in the top bar to cycle through different
rooms and views.

## Example Usage

You:	Illu, I'd like to draw a rainbow.

Illu:	<think>
	## 1. Request Analysis
	
	- Summary: The user wants an image of a rainbow.
	- Safety: This is a SFW request.
	- Subject Category: Landscape
	- Primary Focus: The rainbow
	- Mood Target: Cheerful, vibrant
	- Special Requirements: None
	
	## 2. Planning
	
	- Concept: A vibrant rainbow in a scenic landscape.
	- Template Choice: Landscape, because the focus is on the rainbow within a broader scene.
	- Composition: The rainbow should be the central element, spanning across the sky with a scenic landscape below.
	  - Is regional prompting needed? No, the rainbow is the primary element, regional prompting is unnecessary.
	- Key Elements:
	    - Rainbow
	    - Landscape (e.g., fields, hills, trees)
	    - Sky (clouds, sunlight)
	- Choose which AI artist to use:
	  - Illy - For photorealistic landscape.
	
	## 3. The Main Prompt
	
	- Booru tags: landscape, rainbow, vibrant, colorful, scenic, daylight, sunny, clear sky
	- Named characters: None
	- Things to Emphasise: The vividness and clarity of the rainbow, the beauty of the landscape.
	
	### Characters (if any)
	- No characters
	
	### Objects/Focus (if any)
	- Main subject matter: Rainbow
	- Key features: Vivid colors, clear arc
	- Details/properties: Translucent, ethereal
	
	## View hints
	- facing:
	  - facing viewer
	- from:
	  - from ground level
	- looking:
	  - looking up
	
	### Detailed Scene (optional)
	- Setting description: Rolling hills, lush green fields, scattered trees
	- Environmental details: Clear sky with scattered clouds, sunlight breaking through
	- Season, Time of day, Weather: Spring, mid-day, sunny after rain
	- Flora, Fauna: Green grass, wildflowers
	
	## 4. Creative Development
	
	- Artistic Style: Photorealistic
	- The Atmosphere: Bright, cheerful, serene
	- Color Approach: Vibrant, full spectrum of colors
	- Special Effects: Lens flare, soft focus
	- LoRA Selection:
	  - <lora:add-detail-xl:1> for enhancing details
	
	## 5. Settings
	
	- The default is fast, low quality, square: [sets width=768 height=768 steps=15 hq=0]
	- Increase quality and resolution.
	- Quality settings: [sets steps=30 hq=1.5]
	
	## 6. Negative Prompt
	- None needed, as the focus is on positive elements.
	</think>
	
	```
	Illy, landscape, rainbow, vibrant, colorful, scenic, daylight, sunny, clear sky, rolling hills, lush green fields, scattered trees, sunlight breaking through, spring, mid-day, sunny after rain, green grass, wildflowers, lens flare, soft focus, photorealistic, bright, cheerful, serene <lora:add-detail-xl:1> NEGATIVE  [sets width=1024 height=768 steps=30 hq=1.5]
	```

[you poke to continue]

Illy:	![#3972177466 landscape, rainbow, vibrant, colorful, scenic, daylight, sunny, clear sky, rolling hills, lush green fields, scattered trees, sunlight breaking through, spring, mid-day, sunny after rain, green grass, wildflowers, lens flare, soft focus, photorealistic, bright, cheerful, serene <lora:add-detail-xl:1>](landscape-rainbow-vibrant-colorful-scenic-daylight-sunny-clear-sky-rol.jpg)

