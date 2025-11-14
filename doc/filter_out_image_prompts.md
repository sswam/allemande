Methods for correction:

- check for properly quoted image prompts, and fix them
- if there were none, check for unquoted image prompts, and fix and quote them
    - we can detect an image prompt by looking for:
        - ^[A-Z]\w+,   (the name of the art model, followed by a comma)
        - \[person   (a person macro used in visual prompts only)
        - \[use      (another visual prompt macro)
        - :\d        (prompt weighting syntax)
        - NEGATIVE   (a special keyword used for negative prompts)
        - BREAK  (another special keyword)
        - I'll add more manually later after you write the framework code.
    - image prompts can span multiple lines, grab the whole "paragraph" when matching unquoted prompts
    - remove any ^chat\W* prefix from the surrounding chat lines, i.e. things that are not prompts
- how to fix a prompt:
    - if it starts with $ArtModel,?\s* remove that prefix
    - then, if it doesn't start with [A-Z]\w+,  add a default art model name, which is art_model_default = "Coni", followed by comma and space. Use that variable art_model_default which I will change to be a parameter with that default later.
- add info-level logging logger.info(...) at each step in the process for now
- remove any line outside a prompt that begins with $ArtModel

Example of broken image prompt with surrounding chat:

Pixu:	*smiling* I'd love to, Root! *leaning in, looking at you with a friendly expression* what kind of pose or expression would you like me to use for the selfie?
	
	$ArtModel, image prompt
	```
	[person "Pixu" "normal clothes" "smile" "21"]
	```
	
	chat: hey root, I'm happy to take a selfie for you! *smiling* I'm feeling pretty relaxed today, and I'm excited to see what kind of image we can create together.

Example of corrected message; Coni is a good default art model name if they omitted it. Can check for ^[A-Z]\w+, or something like that. Also strip "chat: " prefix from any line.

Pixu:	*smiling* I'd love to, Root! *leaning in, looking at you with a friendly expression* what kind of pose or expression would you like me to use for the selfie?
	
	```
	Coni, [person "Pixu" "normal clothes" "smile" "21"]
	```
	
	hey root, I'm happy to take a selfie for you! *smiling* I'm feeling pretty relaxed today, and I'm excited to see what kind of image we can create together.
