# Allemande

## What is this?

This is a work-in-progress AI software toolkit in the UNIX tradition.

## Screenshots

![Multi-user AI chat](pix/ally1.png)

![There was a bug where the AI chat used too many emojis!](pix/emotional.png)

![AI software tools](pix/fortune-poem.png)

## What's in the box?

- Voice and in-editor text chat with an AI model (e.g. point-alpaca).
- Shell tools for ChatGPT 3.5 and GPT-4.
- WebUI for multi-user, multi-bot, multi-agent chat
- a local API service for core AI models, based on directories and files not sockets
- An OCR script that uses GPT for proofreading.
- video-to-flashcards: Automatically generate Anki flashcards from YouTube videos (up to 15 minutes or so).
- API servers for alpaca LLM and whisper STT models
- chatgpt-model-switcher: switch models mid-chat in the ChatGPT web app, install it [from GreasyFork](https://greasyfork.org/en/scripts/463362-chatgpt-model-switcher).
- An away script: try to keep an AI chatbot active while you're away, without it going insane!

## Requirements

- GNU/Linux
- python3 < 3.11
- perl 5
- bash
- LLaMA 7B
- point.alpaca
- whisper
- Coqui TTS
- nginx

- apt install soundstretch amixer tesseract yt-dlp ffmpeg

- pip install -r requirements.txt

- segment-anything

- Make sure your API keys are defined in the envioronment, e.g. source a keys script from your bashrc:
```
export OPENAI_API_KEY=....
```
- Edit and source `env.sh` and `config.sh`
- For the WebUI, set up hostnames and SSL, and use the config files in webui/nginx
- Try running everything:
```
make
```

## Consulting

<details>
<summary>
I offer extremely affordable AI consulting and software development. The first consult is free. This is a <i>limited time offer</i>, while I get the business up and running. See my website for details: <a href="https://sam.ucm.dev/">sam.ucm.dev</a>.
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

<p>Take advantage of this timely and exclusive offer while it lasts! Together, we can revolutionize your business to new heights and harness the limitless potential of AI. Remember, the first consultation is <i>FREE</i> with absolutely no strings attached. Don't let this opportunity slip away! Schedule your consult today!</p>
</details>
