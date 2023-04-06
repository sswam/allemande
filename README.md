# Electric Barbarella

## What is this?

This is a work-in-progress AI chat system based on [point-alpaca](https://github.com/pointnetwork/point-alpaca).

See that page for info on obtaining the weights.

I am also including some of my other AI tools.

## What's in the box?

- Voice and in-editor text chat with an AI model Barbarella (point-alpaca), or you can call her whatever you like.
- Shell tools for ChatGPT 3.5 and GPT-4.
- An OCR script that uses GPT for proofreading.
- video-to-flashcards: Automatically generate Anki flashcards from YouTube videos (up to 15 minutes or so).
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

- apt install soundstretch amixer tesseract yt-dlp ffmpeg

- pip install -r requirements.txt

- Add to your ~/.bashrc:
```
export BARBARELLA=$HOME/barbarella   # or wherever you put it
export PATH=$PATH:$BARBARELLA:$BARBARELLA/x:$BARBARELLA/voice
export OPENAI_API_KEY=....
```

- Run the voice chat:
```
bbv
```

## Video demo

[![Electric Barbarella: AI Voice Chat and shell tools](https://img.youtube.com/vi/q8Cl2fZTyOs/0.jpg)](http://www.youtube.com/watch?v=q8Cl2fZTyOs "Electric Barbarella: AI Voice Chat and shell tools")

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

## Mildly NSFW cyborg concept art

<details>
<summary>
This captivating and mildly NSFW cyborg concept art is an enthralling blend of technology and desire, making it impossible for the viewer not to be enveloped in its world. The unparalleled attention to detail, as well as the thought-provoking themes presented, make this image a perfect representation of the artist's incredible talent and insight into the future of human evolution (spoiler blurb by GPT-4).
</summary>
<br>
<img style="border-radius: 1em; padding: 1em;" src="pix/barbarella.jpg" height="512" width="256">
</details>
