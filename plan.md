- fix major issues with Ally Chat before launch
	- login is clunky
		- I like using basic auth
		- main chat room can be readable by anyone, with login fields at top-right
		- use cookies, I have a plan!
	- logout is clunky?
	- create a Linux account for each user?
	- log in with name and password (capitalized name preferably)

	- sign up
		- via login
		- email confirmation
			- do we need it?  Claude thinks so.
		- need username, password, email, fullname, default display name

	- proper access control, encryption if possible

	- custom display names per room


	- restore Ally using client-server to Beorn (my home PC)
		- avoid infinite
	- async API calls
		✓ the llm module is updated for asyncio
	- add Perplexity models
	- add Google models

	- remove, disable or fix any shonky features
		- dangerous code execution
			- could run in a docker container

	- full documentation, use AI to help

	- accounting
	- Stripe payments


	- speech
	- images
		- image to text
		- text to image
		- video
		- talking head

	- roles / character sheets
	- memory
		- could use a 3rd party plugin, or DIY
		- efficiency of memory recollection on active multiple chat
	- files
		- plan
		- working files

	- select scope of input to respond to


- live-learning
	- experiment with live-learning for simple models
		- image classifier
		- compare to regular "rote learning"
	- identify likely bad training data
	- experiment with fine-tuning LLMs (7GB size or so)
	- experiment with live-learning with full fine-tuning
		- might need access to original training set or something similar
	- experiment with live-learning via LoRAs
	- deploy a live-learning model on Ally Chat


- random choice
    - LLM's aren't good at "choose a random letter" for example
    - I should fix that for my LLMs somehow.
        - needs a different type of assessment, based on the distribution of multiple responses
        - related to creativity, variety


- other ideas
	- plain text / markdown notebook system, with editor UI
	- how to run a cell?  hotkeys in editor?


- visual / textual planner tool


- kind behaviour
	- For our API, if the client drops the connection before we send the response, we don't charge them anything. That should be rare and feasible, barring abuse or client bugs which we can detect.
