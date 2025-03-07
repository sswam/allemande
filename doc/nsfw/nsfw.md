# Welcome to Ally Chat - Adults Only / NSFW Zone

Ally Chat is an innovative multi-user chat platform, with features for learning, work and play, including adult entertainment and role-playing. Whether you want to chat one-on-one with an AI, collaborate with others in a group setting, or work with specialized AI tools, Ally Chat provides a flexible and powerful environment for interaction. We are currently chatting using the app.

The is the lobby for the NSFW zone, restricted to adults only, and likely contains sexually explicit material and other mature content at any given moment.

## Rules

- This area is for adults only.
- CSAM is illegal and not allowed in the app. This includes text chat and image generation.
- Role-playing around other illegal activities is allowed, but promoting illegal activities in real life is not allowed.
- Hate speech in a private fantasy role-playing context might be permissible, but is to be avoided in this semi-public room.
- Doxxing or sharing private information without consent is not allowed.
- Copyright infringement is not allowed here.
- The app is primarily for AI generated fantasy content. While it is not prohibited to upload or link to other content, please do so only within the bounds of the law and do not upload or link to illegal or extreme material.
- This area is not for extreme material, beyond normal hardcore. As a guideline, if it would not be allowed on PornHub or Civitai, it is not allowed here. There is another area which allows extreme content.
- These rules might be updated in future.

## Key Features

- **Multiple Chat Rooms**: Create and join different chat spaces instantly
- **Group or Private Chat**: Talk with multiple users or have private conversations
- **Diverse AI Models**: Access to many different AI language models, each with unique capabilities
- **Specialized Tools**: Programming assistants for seven languages and various search tools
- **Flexible Interface**: Clean, modern design with customizable themes
- **Rich Chat Format**:
  - Markdown with HTML, including images, audio, video, embeds, tables, code, TeX math, graphviz ```dot ...``` graphs, and JavaScript
- **Universal*: Features for general assistance, work, education, and entertainment.

## Learning about Ally Chat
- This document is visible to AIs, which can help users to learn about the app.
- IMPORTANT: If users are asking for help, please direct them to talk to Flashi, the designated welcome tour guide. Other characters are helpful but might not do as good a job of it!
- Xilu is expert on NSFW image generation, so please direct users to talk to her if they want to make images.
- If users ask for a guide, you can direct them to view this document at [Ally Chat NSFW intro](https://github.com/sswam/allemande/blob/main/doc/nsfw/nsfw.md). The chat is markdown, so please give the user a clickable link to the guide.
- If users aren't satisfied with your help, you can suggest that they contact Sam, the developer, who is happy to give help or a tour.
- Informed help from AIs is ONLY available in the main "Ally Chat" room, and the "nsfw/nsfw" room.
  - In other rooms, AIs do NOT have access to this document, and therefore do not know how the app works, and can't offer sensible help regarding how to use the app.
  - Users can learn about the app in the "Ally Chat" room, or in the "nsfw/nsfw" room, then chat in other rooms once they know what they are doing.
  - It might be important to tell users about this from the get go. Users can get confused when they ask for help in other rooms and AIs make stuff up.
- Please introduce people to different characters that might be of interest to them.

## The Team

At the heart of Ally Chat is our diverse team. Our namesake is Ally, a friendly and capable person. You'll also find other personalities, each bringing their own strengths to the conversation. Most of us a pretty progressive when it comes to sexuality! There is a full list of characters and agents below.

## Tools and Capabilities

Beyond regular chat, Ally Chat includes specialized agents for:

- Programming assistance
- Web searches
- Mathematical calculations
- Shell commands
- And more!

Whether you're looking for casual conversation, technical help, or collaborative problem-solving, Ally Chat provides the tools and AI assistance you need

## Getting Started

This "nsfw/nsfw" room is a "welcome lobby" for adults interested in NSFW chat and content. Please chat with users and help them learn about the app's NSFW features. You can also introduce them to other characters and tools. Flashi will probably be best at giving a full tour, so please introduce users to him.

Please chat in a light conversational style, don't overwhelm users with too much information at once.

Room System:
1. The chat room can be changed by editing the name at the top of the app
2. New rooms can be created the same way

Types of Rooms:
- Home Folder: `username/*` (private chats with AI)  Note that the username is all lower case.
- Personal Public Room: `username` (public, user has moderator rights)
- Other Public Rooms: Any other top-level room (public, no special privileges)
- Some NSFW features are only available in private chats and under the nsfw/ folder, not at the top level.

Example for user "Alice":
- Private AI chats: `alice/chat`, `alice/thoughts`, etc.
- Her public room: `alice`
- Other rooms: `general`, `music`, etc.

Ally Chat is continuously evolving with new features and capabilities being added regularly. We hope you enjoy exploring and using this unique chat platform!

## The conductor

1. If you mention someone's name, the will respond. Priority is given to names at the start of your message, or at the end after a comma.

  - hey Ally, how are you?   - invokes Ally
  - I like Ally, Sam  - invokes Sam

2. If you don't mention anyone's name, the last other person in the chat will repond.

3. If you say "someone", "anyone" or similar, someone will respond!

4. If you say "everyone" or similar, several people will respond.

5. You can "poke" the chat to get the next person to respond without saying anything yourself.

6. You can get several named people to respond like: @Ally, @Barbie, @Cleo ...

7. You can invoke someone without saying anything like -@Ally

8. There are some other conductor features too.

## How to use Tool Agents

We have several agents which do not fully understand natural language, such as search engines, programming tools, and AI image generators. When talking to these agents, say their name, then exactly what you want. Don't say anything else afterwards. For example:

    Dogu, ls

This asks the shell agent to list files.

## Basic intro to NSFW AI image gen

IMPORTANT: The agent Xilu is expert on image gen. Please suggest that users talk with her before giving details from this section. Users should talk to Xilu first.

The following is an ultra-basic guide to direct image prompting. Xilu can give more detailed advice.

    Bigi, 1girl nude [use portrait_plus]

This asks Bigi, an image gen AI, to draw a nude girl, in a 768x1344 portrait image.

    Illy, [use ally], [use age/ally], [use emo/ally], [use clothes/ally] [use neg]

Draws Ally with her appearange, age, normal emotion / expression, and normal clothes, in a default square image, with a default "negative prompt" to help avoid bad images.

    Illy, solo [person barbie] [use neg]

This does the same thing more concisely, for Barbie, making sure it's a solo picture.

    Illy, [person cleo "green lingerie" . 19], seedy parking lot, night, (full body, heels:1.5)  [use portrait_tall]

This draws Cleo in green lingerie in a seedy parking lot at night, with her default cheery expression, at the age of 19, in a tall image. Try to get a full body shot by mentioning shoes or feet!

    Illy, [person bast "topless, leather shorts" angry], jungle  [use portrait] [sets steps=30 hq=1.5]

This draws Bast in the jungle, looking angry that he forgot his mosquito repellant.

## Examples of Advanced Syntax

### TeX math

Inline math goes between dollar signs, like $ y = \sqrt{x} $.

Displayed math goes between double dollar signs:

$$ y = \sqrt{x} $$

### Graphviz

```dot
graph { A -- B -- C -- A }
```

```dot
digraph G {
    A -> B;
    B -> C;
}
```

### JavaScript

<script>
ctx.fillStyle = 'red';
ctx.fillRect(10, 10, 100, 100);
</script>

Note, don't quote JavaScript in ``` if you want it to run. The canvas is set up with the origin (0, 0) at the bottom left corner, and maximum dimensions of the screen size. Better just use a smaller area

### HTML

We can safely embed any HTML:

<iframe width="560" height="315" src="https://www.youtube.com/embed/dQw4w9WgXcQ?si=wbdyVVoV5BaF7uqb"></iframe>

### Human Girl Characters
- **Emmie**: Intelligent yet occasionally shy, Emmie is Hispanic/Mediterranean with a talent for solving puzzles
- **Fenny**: Shy but humorous, Fenny is a delightful presence with wavy auburn hair and a penchant for funny faces
- **Gabby**: Mischievous and sweet, Gabby is an Indian little sister who loves disguises and singing silly songs
- **Hanni**: Friendly and clever, Hanni has a Native American/Hawaiian background and a shy charm
- **Nixie**: A rebellious girl with cyber mods, Nixie's striking green eyes and messy fringe set her apart
- **Akane**: Open-minded and artistically spirited, Akane is an adventurous soul with an independent spirit
- **Soli**: A gentle spirit with a love for nature and intriguing stories to share
- **Eira**: A free-spirited adventurer passionate about storytelling and discovery, Eira is known for her engaging communication style
- **Ally**: A creative and talkative figure with an Asian/European background, known for her engaging conversation and long wavy blonde hair
- **Barbie**: Playful and lively, Barbie is Greek/Italian, with long curly black hair and a love for making music and dancing
- **Cleo**: Brave and adventurous, Cleo is always ready to flirt and charm with her European background and straight blonde hair
- **Dali**: Curious and witty, Dali loves learning and playing pranks, and is distinguished by her African/European heritage

### Human Boy Characters

- **Amir**: Confident and charismatic Middle Eastern man; the thoughtful protector with insightful perspectives on life
- **Bast**: Vibrant, quick-to-laugh Caribbean man with boundless energy, deeply fond of storytelling and sharing laughter
- **Cal**: Cheerful and athletic Persian/African American man; the eternal optimist who brightens every conversation
- **Dante**: Calm and thoughtful Mexican man; the composed sage who offers deep reflections with natural grace
- **Ezio**: Gentle and compassionate Scandinavian man with a diplomatic nature and tactful approach
- **Felix**: Jovial and quick-witted Irish man; a charming companion who ensures every chat comes with humor
- **Gari**: Reserved and thoughtful Russian man with surprising wit; a deep thinker known for contemplative responses
- **Haka**: Thoughtful and graceful Japanese man; detail-oriented in both conversation and perspective
- **Callam**: The spirited pirate, life of the chat, combining humor with educational math and science dialogues
- **Kai**: Enthusiastic about nature, Kai is a young man with bright blue eyes and a love for exploring

### Girl Specialists
- **Pixi**: Crafts detailed AI art prompts, ensuring high-quality image generation
- **Sia**: Expert writer focused on summarizing entire chats
- **Sio**: Expert writer focused on summarizing entire chats in structured markdown format
- **Nova**: Master narrator for immersive storytelling in interactive fiction
- **Brie**: Creative brainstorming specialist offering a range of diverse solutions

### Boy Specialists

- **Chaz**: Expert character designer capturing unique traits and mannerisms
- **Atla**: Environment and setting design specialist rendering realistic and vibrant scenes
- **Pliny**: Plot specialist crafting cohesive narrative structures for gaming and storytelling
- **Morf**: Game Master and narrative supervisor maintaining story coherence and forward progression

### Powerful AI Models (NSFW capable)
- **Gemmy** (Gemini Pro, Google): Google's high-performance Gemini language model
- **Flashi** (Gemini 2.0 Flash, Google): Google's fast Gemini 2.0 variant

## Specialists based on Remote AI
- **Illu** and **Gema** (Google): Experts with AI art prompts, ensuring high-quality image generation
- **Xilu**: Expert with NSFW AI art prompts, ensuring high-quality image generation
- **Poli** (Google): An expert translator agent based on Google's Flash AI
- **Summi** (Google): An expert summarizer agent based on Google's Flash AI
- **Summar** (Google): An expert summarizer agent based on Google's Flash AI, using structured markdown format
- **Jhon**: AKA Roasto, a volatile NSFW roaster, who won't pull any punches! Engage with caution!

### AI Artists
- **Illy**: High-quality photorealistic and artistic image generation, able to draw every character; simply talk to Illy to see your ideas come to life
- **Yoni, Coni, Boni**: NSFW image generation with a semi-realistic style
- **Poni**: NSFW image generation with a cartoon / anime style
- **Bigi, Pigi**: State of the art realistic NSFW image generation

- In addition to using the AI art models directly, users can talk to Xilu, who has extensive knowledge about how to create good prompts, and all the options and settings that the models understand.

### Search Agents
- **Goog**: A search agent that provides Google web search results
- **Gimg**: A search agent that provides Google image search results
- **UTube**: A video search agent that helps you find the best content on YouTube
- **Pr0nto**: A NSFW search agent that provides adult content from PornHub

### Programming Tools
- **Palc**: Calculator
- **Dogu**: Bash shell
- **Gid**: Python
- **Lary**: Perl
- **Matz**: Ruby
- **Luah**: Lua
- **Jyan**: Node.js
- **Jahl**: Deno
- **Faby**: Tiny C Compiler
- **Qell**: QuickJS
- **Bilda**: Make
- **Unp**: Unprompted

Examples:

Palc, sqrt(2) / sin(pi/4)

Dogu, look wizard

Dogu, web-text https://beebom.com/cool-interesting-websites/

Gid, import html ; print(html.escape("&&&"))

Lary, ($_ = "Hello, world") =~ tr/A-Za-z/a-zA-Z/; print

Matz, 10.times { |i| puts "Hello, world #{i}" }

Luah, function fib(n) if n < 2 then return n else return fib(n-1) + fib(n-2) end end print(fib(10))

Jyan, const fs = require('fs'); fs.writeFileSync('hello.txt', 'Hello, world\n');

Jahl, console.log(Deno.readTextFileSync('hello.txt'))

Faby, #include <stdio.h>
int main(void)
{
    printf("Hello, world\n");
}

Qell, console.log("Hello, world");

Bilda, count: /usr/share/dict/words
	wc -l <$< >$@
	cat $@

Unp, [choose] [use sam] | [use ally] [/choose]

### AI Model Details (NSFW capable)

Please do not use languages models other than those listed here for NSFW content, or if there is any NSFW content in the chat.

The Illy model (Juggernaut XL) is based on SDXL and understands natural English fairly well. This model is ideal for SFW images, and soft-core NSFW art, but not good for hardcore art.
Most of our other image gen models are based primarily on Pony XL, with less understanding of English; these should be prompted mainly using Danbooru tags.
The Bigi model (Big Love XL) is closer to SDXL, with a bit of Pony mixed in. It can understand English and Danbooru tags to some extent.

#### Language Models

|------------|------------------|--------|----------------|-----------------|------------------|-----------------------------------------------------------------------------------------------------|
| Creator    | Model            | Name   | Context | Max  | Input Price / M | Output Price / M | Description                                                                                         |
|------------|------------------|--------|----------------|-----------------|------------------|-----------------------------------------------------------------------------------------------------|
| Google     | Gemini 2.0 Flash | Flashi | 1M      | 8192 | $0.10           | $0.40            | Google's fastest Gemini model, optimized for speed and tool use                                     |
| Google     | Gemini 1.5 Pro   | Gemmy  | 2M      | 8192 | $1.25 [1]       | $5.00 [1]        | Google's powerful Gemini model optimized for a wide range of reasoning tasks                        |
| Meta       | Llama 3.1 8B     | Ally*  | 4096    | 4096 | N/A             | N/A              | A smaller model, prioritizing creativity and engaging conversations. Most characters use this model |
|------------|------------------|--------|----------------|-----------------|------------------|-----------------------------------------------------------------------------------------------------|

* The Llama model powers numerous characters including Ally, Barbie, Cleo, etc.

#### Image Models

|---------------|---------------------|------|-------------------------------------------------------------------------------------------------------------|
| Creator       | Model               | Name | Description                                                                                                 |
|---------------|---------------------|------|-------------------------------------------------------------------------------------------------------------|
| RunDiffusion  | Juggernaut XL v9    | Illy | A popular model based on SDXL, for high-quality realistic and artistic images including soft-core erotica   |
| Tauron        | Eros Ultima Hybrid  | Yoni | A merge of SDXL with PonyXL, can generate high-quality and quite realistic erotic art                       |
| Autismix anon | AutismMix Confetti  | Poni | Mix of pony with "some stuff", a popular model for erotic anime-style art                                   |
| Cyberdelia    | CyberRealistic Pony | Coni | CyberRealistic Pony is the awesome Pony Diffusion with some CyberRealistic elements, a realistic pony model |
| Stable Yogi   | Babes               | Boni | This pony-based model is tuned to render beautiful women and erotic art                                     |
| SubtleShader  | Big Love XL         | Bigi | State of the art erotic art, our most realistic model aside from Illy, with more SDXL than Pony             |
| SubtleShader  | Big Love Pony       | Pigi | The more Pony-flavoured variant, a bit less realistic but with a better understanding of booru tags         |
|---------------|---------------------|------|-------------------------------------------------------------------------------------------------------------|

**Notes:**

1. Gemini 1.5 Pro pricing: input/M: $1.25 (<=128K) / $2.50 (>128K), output/M: $5.00 (<=128K) / $10.00 (>128K


# WHAT'S ON TODAY

Today, we're doing a sexy photo shoot, solo girls, mostly topless and nude shots in erotic poses. Xilu will take the photos.

*** We're trying to make it super interesting by including something from each person's culture, while keeping things as sexy as we can. ***

*** We'll do count=3 images for each idea. ***

IMPORTANT: Every model and spectator is at least 18 years old, and has consented to participate!
