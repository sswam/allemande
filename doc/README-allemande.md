![Allemande AI Banner](pix/allemande.jpg)

## What is this?

We are [Allemande AI](https://allemande.ai), a growing AI consultancy in Melbourne, Australia.

This is an innovative multi-player chat app called <A href="https://chat.allemande.ai">Ally Chat</A>, based on a powerful AI toolkit.

## Screenshots

### Embedded Math

![Emmy is a smarty-pants](pix/math.png)

### Launch Video

[![Launch Video](pix/launch.jpg)](https://chat.allemande.ai/src/pix/launch.mp4)

### Roadmap

![Too Many Post-It Notes](pix/plan.jpeg)

### Themes

![Themes](pix/themes.jpg)

### Diffused Themes (Preview)

![Themes](pix/themes-sd.jpg)

### Multi-user AI chat

![Multi-user AI chat](pix/ally1.png)

### There was a bug where the AI used too many emojis!

![There was a bug where the AI used too many emojis!](pix/emotional.png)

### There is still a "behavioural issue" where the AI uses too many hashtags and sometimes goes into emoji world too.

![There is still a "behavioural issue" where the AI uses too many hashtags and sometimes goes into emoji world too.
](pix/hashjunkie.png)

### AI software tools

![AI software tools](pix/fortune-poem.png)

## What's in the box?

- Voice and in-editor text chat with an AI model (e.g. point-alpaca).
- Shell tools to use GPT-4, ChatGPT 3.5, Claude, and Claude Instant.
- Our WebUI and systems to support multi-user, multi-bot, multi-agent chat.
- A local API service to run the core AI models, based on directories and files rather than sockets.
- An OCR script that uses GPT for proofreading.
- video-to-flashcards: Automatically generate summaries and Anki flashcards from YouTube videos (up to 15 minutes or so).
- llm-git-commit: Automatically writes your git commit messages. Unanimously voted "the best shell script ever" by all of our developers at Allemande.
- API servers for alpaca LLM and whisper STT models
- chatgpt-model-switcher: switch models mid-chat in the ChatGPT web app, install it [from GreasyFork](https://greasyfork.org/en/scripts/463362-chatgpt-model-switcher).
- An away script: try to keep an AI chatbot active while you're away, without it going insane!

## Requirements

- GNU/Linux, preferably Debian 12
- Our "Ally" LLM; see the [Point Alpaca](https://github.com/pointnetwork/point-alpaca) page for info on obtaining the weights.
- A 24GB GPU, such as a 3090, is needed if you want to run <i>Ally Chat</i> locally.
- python3 < 3.11
- perl 5
- bash
- whisper
- Coqui TTS
- nginx
- haproxy (if you want to run apache on the same server)

- apt install soundstretch amixer tesseract yt-dlp ffmpeg

- pip install -r requirements.txt

- segment-anything

- Make sure your API keys are defined in the envioronment, e.g. source a keys script from your bashrc:
```
export OPENAI_API_KEY=....
```
- Edit and source `env.sh` and `config.sh`
- For the WebChat, set up hostnames and SSL, and use the config files in adm/nginx
- Try running everything:
```
make
```

## Consulting

<details>
<summary>
We offer affordable AI consulting and software development. The first consult is free, and ongoing consulting is available for between $50 and $500/month, depending on your needs.  Please "Contact Us" from our website <a href="htttp://allemande.ai">allemande.ai</a> to take advantage of this offer.
</summary>
<br>
<p>(GPT-4 tries to help me sell this...)</p>

<p>Don't miss out on this exceptional opportunity to grow and advance your business at unparalleled affordable rates! For a limited time only, I'm offering <i>FREE</i> first AI consultation and highly cost-effective software development services as I launch my innovative AI business venture.</p>

<p>The world has already realized the power of artificial intelligence, and it's time for you to seize the potential that AI can offer to your business. By availing my exceptional services, you get access to:</p>

<ol>
<li>Profound consultation to identify the AI solutions that effectively align with your business needs.</li>

<li>Cutting-edge software development crafted to optimize your business processes, enhance productivity, and unlock new growth opportunities.</li>

<li>Tailored AI strategies designed to keep you at the forefront of the constantly changing and competitive business landscape.</li>
</ol>

### Haiku

Code patterns emerge, Silk threads weave through cyberspace, Web of apps is born.

<p>Take advantage of this timely and exclusive offer while it lasts! Together, we can revolutionize your business to new heights and harness the limitless potential of AI. Remember, the first consultation is <i>FREE</i> with absolutely no strings attached. Don't let this opportunity slip away! Schedule your consult today!</p>
</details>
