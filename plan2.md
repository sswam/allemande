- I am fixing auth to be more user friendly and secure, I've done log in nicely but not sign up.
- fixed an issue where a bot will decide to take over all roles in the conversation and talk to itself for a few thousand words. I seem to be able to avoid that with a sort of "floating system prompt* that follows the conversation rather than sitting at the top.
- Upgraded "Ally", the namesake bot to use Llama 3.1 8B instruct, optionally the 8-bit gguf version, on GPU or CPU.
- Using asyncio throughout, which is important for supporting concurrent users and chats obviously
- Fixed a bug with slow TeX math rendering in some cases.
- Trying out some different component including insanely-fast-whisper and parler TTS. Parler is more stable than the other open-source TTS I was using, but it's still not 100%. Perhaps I can run the output through whisper and check that it matches more or less, and retry a few times if not.
- A couple of the source code files are too big and complicated, I need to break them up to be more maintainable, and clean out the rubbish.

Next steps:

- usage tracking / credit system
- sign up and necessary parts of an auth system
- add extra models (Google Gemini, perplexity; I already have the code)
- try to get a few users (free is okay)
- add voice chat (I've done it before)
- add image generation
- add role-playing capabilities, i.e. "character sheets" for different people in a chat; "mission sheets" for the chat as a whole, etc. Similar to a system message.
- add simple memory
- add RAG memory
- LoRA fine tuning
- live learning



I'm working on it, on and off. It's in a bit of a "clean up" phase at the moment. I wrote a longer response, can PM you if you like. Or I can set up access again and make sure it works for you. The feature set is similar to last time, auth is a bit better, and Ally is on llama 3.1 8B, online most of the time (runs on my local PC). It's still free of charge with access to GPT4 and Claude Sonnet, as I don't have any heavy users.
I have some ambitious goals and ideas for it, including voice chat, AI taking initiative to start a chat, AI-mediated flashcard learning, illustrated stories / role-playing-games, users can share models and GPU time with occasional correctness auditing for untrusted users, different subdomains for different types of users that wouldn't want to talk to each-other, and efficient per-user / role / org live-learning and training, using LoRAs and spaced repetition. The architecture is a single small VPS per region, plus commercial APIs for strong models, and home PCs for anything we can run at home, just my PC so far. The front-end is a vanilla JS PWA preferring simple old tech over complex stuff. Chats are stored in plain text files, and rendered on the server to HTML files for display. I also intend to include API access to all services and models in the package, including at the free tier. 
