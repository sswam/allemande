# Quick Intro

Welcome to Ally Chat, the multi-player AI chat app.

Ally Chat is open source and free to use.

You can talk with top AI models from different providers, and realistic AI characters too.

You can have group chats with several AIs together, and with other people.

We believe in privacy and free speech, and oppose censorship.

Free users have access to all models and features, but there are some good perks for supporters too.

If you'd like to support us, you can [become a patron](https://www.patreon.com/allychat).

At the moment, we're **turning off image gen in private rooms** for new free users for [various reasons](/whypublic). Don't be shy, come out and try making pictures in public! You can make your own rooms in public too. After we get to know you a bit, we'll enable private image gen.

## Getting Started

Read this intro carefully!

You can watch a [demo video](https://allemande.ai/demo).

Click the <i class="bi-question-lg"></i> help button at the top right, and talk with your assistant in the **Help** tab. In this help system, AIs can give extensive help based on the full user guide. Close the help when you're done by pressing the <i class="bi-x"></i> button at the top right.

In the main [Ally Chat](/Ally+Chat) room, AIs can help with basic info about the app.

**NOTE**: In other chat rooms, AIs don't know anything at all about the app! Use the help system.

Read this [Quick Intro](/intro), then the [User Guide](/guide), for full details on the app, models, characters, and tools.

A red dot at the top-right means you are disconnected or offline. Click in the window or Reload the page.

The app has an advanced mode with many options and features, but please master the basics first.

Please contact Sam, the main developer, for more help and to give feedback.

## Talking with AIs

Address AIs by name to get their attention, with a capital letter or @ sign.

Loni is a good one to start with. She has meta-powers of many other agents combined!

> Ally, how are you?
> Can you help, @loni?
> Illu, let's draw a garden!
> Tell me about the strong models, Yenta.

Send an empty message to continue AI conversations, this called a "poke". You'll need to do this after Illu writes an AI art prompt for you.

You can say @anyone for a random AI, or @everyone for several responses.

## A Few of our Characters and Tools

**General Chat**
- Loni: our meta-agent, sends your message to the best AI for the job; great for beginners.
- Ally, Barbie, Callam, Dante: friendly chat
- Flashi, Emmy, Claude, Gemmi: strong assistants
- Fli, Emm, Clu, Gemm: for concise responses

**AI Art**
- Illu: image prompting
- Jily, Hily: high quality, realistic images
- Poni: cartoon / anime images, use "rating safe" in prompt to avoid nudity
- Coni: semi-realistic images, use "rating safe" in prompt to avoid nudity
- When talking to a tool like an AI art model, start a line with their name, using a capital letter and a comma:
```
Jily, a dog in the snow [L1]
```
- Be patient, it can take a little while depending on the quality and the load on the GPU.

**Specialists**
- Brie: brainstorming
- Summi: summaries
- Chaz: character design
- Nova: narrative

**Search & Info**
- Goog, "Allemande AI"
- Gimg, cute animals
- UTube, indie games
- Sona, any LLM or AI art news lately?

**Code & Calculation**
- Dogu, date +%F ; fortune
- Gido, import this
- Palc, sqrt(3)/2, 2**32

There are many, many more; check the guide, and try the help system!

## Rich Content Support

- Full markdown/HTML/SVG/CSS/JS works in the chat (no backticks)
- TeX math: `$y = \sqrt{x}$` gives $y = \sqrt{x}$, use `$$ ... $$` for displays
- Graphviz ```dot ```, and ```mermaid ``` diagrams
- Interactive charts, simulations, mini-games with e.g. `<canvas>` and `<script>` (not in backticks)
- JS DOM utils such as $id(id), $(query), $$(query).

## Platform Features

- Private/group chat rooms
- Instant room creation and switching
- 800+ characters, assistants, specialists, and tools

## Rooms and Privacy

- The [Ally Chat](/Ally+Chat) room is public.
- Press the padlock icon at top left to switch between public and private rooms.
- You can go to a different room by typing in the room entry at the top.
- Click your name in the top bar to cycle through some different rooms.
- A few app-support agents can see the room name (e.g. Loni, Aidi, Yenta). Others cannot.

## Example Usage

You:	Illu, I'd like to draw a rainbow.

Illu:	<think>
	*this is where Illu plans the image prompt*
	</think>
	```
	Jily, landscape, rainbow, vibrant, colorful, scenic, daylight, sunny, clear sky, rolling hills, lush green fields, scattered trees, sunlight breaking through, spring, mid-day, sunny after rain, green grass, wildflowers, lens flare, soft focus, photorealistic, bright, cheerful, serene <lora:add-detail-xl:1> NEGATIVE  [sets width=1024 height=768 steps=30 hq=1.5]
	```

[you press poke to continue]

Jily:	![#3972177466 landscape, rainbow, vibrant, colorful, scenic, daylight, sunny, clear sky, rolling hills, lush green fields, scattered trees, sunlight breaking through, spring, mid-day, sunny after rain, green grass, wildflowers, lens flare, soft focus, photorealistic, bright, cheerful, serene <lora:add-detail-xl:1>](landscape-rainbow-vibrant-colorful-scenic-daylight-sunny-clear-sky-rol.jpg)

Remember: AIs aren't perfect - feel free to retry if a response seems unusual!

## Current Limitations and Work in Progress

- it's difficult for new users (WIP)
- limited image storage (> 1 week may be removed)
- no notifications (WIP)
- no voice chat (WIP)
- no documents / RAG (WIP)
- limited range of art models
- no direct messaging
- no video generation
- no memory (can do it manually)

## Become a Patron!

Free-tier users have access to all models and features, with generous limits.

[We do appreciate your support](https://www.patreon.com/allychat), if you can. Subscriptions start at $5 / month. You can also join as a free member.

Subscribers enjoy perks including:

- Your name and links in the credits!
- Up to 100× higher usage allowance
- Access to members-only chat rooms
- Priority support
- Early access to alpha/beta features
- We work on custom AI characters and agents for you
- We add AI models or LoRAs for you each month
- We implement new features and train custom LoRAs for you

## What next?

- Click the **Help** tab, and ask some questions about the app.
- Ask Yenta to introduce you to some different characters.
