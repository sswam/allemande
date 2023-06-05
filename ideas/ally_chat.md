# NOTE XXX

# json, itertools, bisect, gc
# from accelerate import Accelerator
# import accelerate

# TODO use functools.cache or functools.lru_cache decorator?  https://docs.python.org/3/library/functools.html

# Ideally I would prefer a generic solution not all this hackery and complexity...
# A better approach might be to implement the simplest possible generic client-server forking singleton thing for the command line, to accelerate loading.
# Let's get this working here and now, then switch to that method for modularity.

# BUGS

# - raw mode still adds spacing, if anything it should strip the spacing.

# TODO

# ✓ pass model as a parameter
# ✓ specify invitations, i.e. human and assistant names
# ✓ readline for interactive, and allow to edit prompts
# ✓ allow to specify a file to read history from, and append to it
# ✓ non-interactive mode on a single file
#   ✓ not very useful but a foundation for watching files
# ✓ watch multiple files
# ✓ use previous names in interactive edit mode
# ✓ use previous names in process_file mode
# ✓ raw mode, don't insert invitations
# ✓ option to forget old history so can continue chatting
# ✓ 8-bit quantization option
#   - not working?
# ✓ allow dynamic config, reload each time we run the model

# - options to insert a system message at the start of the chat, or just before the user's message
# - could do a virtual or real group chat I suppose
# - object oriented
# - use plugins
# - allow to go back in interactive
# - allow to edit history
# - allow to remove first lines when run out of space
# - try using it in a notebook
# - try running with aliases instead of standard invitations
# - system prompt or whatever
# - reload python code without quitting
# - or run a pure model service that I don't need to restart
# - what sort of API?
# - try it with llama.cpp
# - run it on my webservers?


- missions
- personas
- breakout rooms
- augmentations
	- raise temperature / avoid repetition
	- general vector DB
	- personal vector DB
	- LoRA
	- multi predict & choose
	- self-assessment and refinement
