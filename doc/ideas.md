hierarchical selection / spreadsheet / markdown
column selection / spreadsheet / tables
assemble prompt / context in the entry

list agents above the entry

accounting:
- tokens and prices
- show estimate for query before the query
	- Claude: While not exact, dividing character count by 4 gives a rough estimate of tokens. More accurate: split text into words and multiply by 1.3.
- output options, e.g. markdown, plain text

- download files and rooms and zips

- avoid case issues when browsing to an existing folder / room

- text zoom, easy UI (enter font size)

✓ limit context

- filer features: move, mkdir, rmdir, etc.

- add titles to explain UI elements

- use 100dhv to adjust for keyboard issues on mobile
	- tried, not working
	- I got it working but causes other issues
	- try with position: fixed or something?
	- I'd like to be able to zoom in the image viewer, maybe
	- How to allow reload by drag down, which used to work?

- set up a dev instance



✓ remember input bar height

- transferring data message is annoying
	- use a better method not HTTP streaming

✓ image input
	- unfortunately censored re. identifying people, even celebs

- file copy-paste and drag and drop to upload

- having a little 3-dot menu icon on past messages with the option to delete just that message would be great, too


- "fork chat" idea, from a message, how many messages to copy
	- can copy back to original chat too
	- basic idea is to copy select messages to another chat room, either new or existing
	- maybe show connections between chats in a "map view" somehow

- edit single message

- bookmark chat messages
	- possible bookmarks side-pane

- import instructions from a file

- UI for base and mission files
	- view what mission is active in the chat

- agent to improve LLM prompts, or help people improve their prompts interactively

- paste plain code in, auto detect and wrap in backticks


--------------

- prevent talk to self without explicit name?!
- fix chat / escape_indents restore_indents, use only during code blocks I guess maybe? But shouldn't be needed in code blocks!
- also audio input, gpt-4o-audio-preview supports, clever Emmy!
- Fix to allow multiple image prompts in a message, to be run sequentialy.
- <think keep=1> option to make thinking available in future context

✓ move agents code to its own file
	✓ support base / inheritance at use time

- Start self talk only with "@Sam" not "Sam". Double user message should not trigger self talk.

- fast and smart agent for voice chat: wrap up a fast agent together with a slower agent, fast agent can reply for a bit first while slow agent is thinking.
	- or just accept thinking pauses in conversation
	- or use fast agent for normal chat and slow for difficult stuff


--------------

maybe make the models answer when they are tagged with @
like the average chats
it's more user-friendly
Yeah maybe better not to do it without the @. I could try that or make it an option.
make them profiles in the chat , so one can press on their names if they wanna chat privately or know information about 
and make the usernames colorful like in whatsapp groups

--------------

voice chat and talking heads, from any image

--------------

Fix Deseri and Perplexity models alternating context.

Error code: 400 - {'error': {'message': 'deepseek-reasoner does not support successive user or assistant messages (messages[1] and messages[2] in your input). You should interleave the user/assistant messages in the message sequence.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}

We can combine multiple user messages together, and multiple AI messages together. Hopefully it will work!


Fix all the themes so all text is high contrast and readable, need to test with multi-media content like the demo.

--------------

Edit tabular data, at least basic editing. Doesn't have to be a spreadsheet!

--------------

✓ Option to use or not to use mission, in chat options.
- Consider whether chat options should be user specific, they likely should be.
