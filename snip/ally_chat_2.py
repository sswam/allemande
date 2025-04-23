async def chat_to_user(_model, args, history, history_start=0):
	""" Chat with the model. """
	invitation = args.bot + ":" if args.bot else ""
	human_invitation = args.user + ":" if args.user else ""
	if args.emo and invitation:
		invitation += " "
	# if args.emo and human_invitation:
	if human_invitation:
		human_invitation += " "
	delim = args.delim

	if args.edit:
		msg = input_with_prefill("", human_invitation)
	else:
		msg = human_invitation + input(human_invitation)

#	logger.debug(f"{history=}")
#	logger.debug(f"{history_start=}")

	if msg:
		print("")

		if ":" in msg:
			args.user = msg.split(":")[0]

		history.append(msg)
		history_write(args.file, history[-1:], delim=delim, invitation=delim)

#	logger.debug(f"{history=}")

	if args.edit:
		invitation2 = input_with_prefill("", invitation)
	else:
		invitation2 = invitation

	if ":" in invitation2:
		args.bot = invitation2.split(":")[0]

	model_name = args.model
	fulltext, history_start = get_fulltext(args, model_name, history, history_start, delim+invitation2, delim)

	args.gen_config = load_config(args)

#	logger.debug(f"{history=}")
#	logger.debug(f"{history_start=}")
#	logger.debug("fulltext: %r", fulltext)
#	logger.debug("model: %r", model)
#	logger.debug("invitation: %r", invitation)
#	logger.debug("invitation2: %r", invitation2)
#	logger.debug("delim: %r", delim)

	response = await client_request(args.portal, fulltext, config=args.gen_config)

	if args.trim:
		response = trim_response(response, args)

	print(invitation2 + response)
	print("")

	history.append(invitation2 + response)
	history_write(args.file, history[-1:], delim=args.delim, invitation=delim)

	return history_start


async def chat_loop(model, args, history, history_start=0):
	""" Chat with the model in a loop. """
	while True:
		history_start = await chat_to_user(model, args, history, history_start=history_start)


async def interactive(model, args):
	""" Interactive chat with the model. """
	history = history_read(args.file, args)

	for message in history:
		print(message + args.delim, end="")

	# get latest user name and bot name from history
	# XXX this is unreliable!
	if args.raw:
		pass
	elif args.get_roles_from_history:
		args.user, args.bot = conductor.get_roles_from_history(history, args.user, args.bot)
	else:
		# use conductor
		# TODO !!!!!!!!
		pass

	try:
		await chat_loop(model, args, history)
	except EOFError:
		pass


	modes_group.add_argument("--interactive", "-i", action="store_true", help="Interactive mode, can use --file to load history")
	modes_group.add_argument("--file", "-f", default=None, help="Process and append to a file")
	modes_group.add_argument("--stream", "-s", action="store_true", help="Stream mode")

	interactive_group = parser.add_argument_group("Interactive mode options")
	interactive_group.add_argument("--edit", "-e", action="store_true", help="Edit the names during the session")



	watch_group.add_argument("--interval", type=float, default=1.0, help="Interval between checks")



	watch_group.add_argument("--ignore", default=None, help="Ignore if this string occurs at the end")
	watch_group.add_argument("--require", default=None, help="Ignore unless this string occurs at the end")


	if args.ignore and history and history[-1].rstrip().endswith(args.ignore):
		return False
	if args.require and history and not history[-1].rstrip().endswith(args.require):
		return False


	names_group = parser.add_argument_group("User and bot names")
	names_group.add_argument("--user", "-u", default=default_user(), help="User name")
	names_group.add_argument("--bot", "-b", default=default_bot(), help="Bot name")
	names_group.add_argument("--raw", "-r", action="store_true", help="Don't auto-add names, free-form mode")
	names_group.add_argument("--get-roles-from-history", "-H", action="store_true", help="Get user and bot names from history file")


	if args.raw:
		args.user = ""
		args.bot = ""


	if args.raw:
		messages = response.split(args.delim)
		if messages and not re.search(r'\S', messages[0]):
			messages = messages[1:]
		response = messages[0] if messages else ""
	else:


	# XXX this is unreliable!
	if args.raw:
		pass
	elif args.get_roles_from_history:
		args.user, args.bot = conductor.get_roles_from_history(history, args.user, args.bot)
	else:


# 	if not args.raw and history and history[-1] != "":
# 		history.append("")
# 		history_write(file, ['', ''], delim=args.delim)


#		human_invitation = args.user + ":"
#		response = response.split(human_invitation)[0]


	human_invitation = args.delim + args.user + ":" if args.user else ""
	# if args.emo and human_invitation:
	if human_invitation:
		human_invitation += " "


def default_user():
	""" Try to get the user's name from $user in the environment, or fall back to $USER """
	user_id = os.environ["USER"]
	return os.environ.get("user", user_id).title()


def default_bot():
	""" Try to get the bot's name from the environment, or fall back to "Assistant" """
	return os.environ.get("bot", "Assistant").title()

		# model_dirs = prog_dir()/".."/"models"/"llm"

def prog_dir():
	""" Get the directory of the program. """
	return Path(sys.argv[0]).resolve().parent


	format_group.add_argument("--emo", type=bool, default=False, help="End the bot invitation with a space, which causes the bot to respond with an emoji first!")


	if args.emo and invitation:
		invitation += " "

	format_group.add_argument("--trim", action="store_true", default=True, help="Trim the bot's response (enabled by default)")
	format_group.add_argument("--no-trim", action="store_false", dest="trim", help="Don't trim the bot's response, i.e let it predict the user's speech")
	format_group.add_argument("--strip-final-newline", type=bool, default=True, help="Strip final newline from input, allows to continue lines")
	format_group.add_argument("--narrative", type=bool, default=False, help="Allow non-indented narrative text")


	# for now do just query, not the full chat
	if agent["default_context"] == 1:
		logger.debug("history: %r", history)
		logger.debug("query: %r", query)
		response = await llm.aquery(query, out=None, model=agent["model"])
	else:

#	if args.trim:
#		response = trim_response(response, args)
	logger.debug("response 2: %r", response)

	# remove up to one blank line from the end, allows to continue same line or not
	# using a normal editor that always ends the file with a newline
#	if args.strip_final_newline and history and not history[-1]:
#		history.pop()

#	model_group = parser.add_argument_group("Deluxe options")
#	model_group.add_argument("--retry", default=3, help="Number of times to retry if the bot fails to respond")
#	model_group.add_argument("--retry-temperature-boost", default=0.1, help="Temperature boost to apply when retrying")


	dev_group = parser.add_argument_group("Developer options")
	dev_group.add_argument("--no-model", "-M", action="store_false", dest="model", help="Don't load the model, for testing purposes")
	dev_group.add_argument("--dump-config", "-C", action="store_true", help="Dump the model config in YAML format, and exit")

	if args.dump_config:
		print(yaml.dump(args.gen_config, default_flow_style=False, sort_keys=False))
		sys.exit(0)

	agent_group = parser.add_argument_group("Agent options")
	agent_group.add_argument("--agents", "-a", default=["all"], nargs="*", help="Enable listed or all agents")
	agent_group.add_argument("--no-agents", "-A", dest="agents", action="store_const", const=[], help="Disable all agents")
	agent_group.add_argument("--no-ai", action="store_true", help="Disable all AI agents")  # TODO
	agent_group.add_argument("--no-tools", action="store_true", help="Disable all software tool agents")  # TODO


	# check agents are valid
	if args.agents == ["all"]:
		args.agents = AGENTS.keys()
	else:
		for a in set(args.agents) - set(AGENTS):
			logger.warning("Unknown agent: %s", a)
		args.agents = set(args.agents) & set(AGENTS)

	model_group.add_argument("--list-models", "-l", action="store_true", help="List available models")
	model_group.add_argument("--bytes", "-8", action="store_true", help="Load in 8-bit mode, to save GPU memory")
	model_group.add_argument("--max-tokens", "-n", type=int, default=2048, help="Maximum number of new tokens to generate")
	model_group.add_argument("--remote", "-R", action="store_true", help="Use remote models only, not local (for server working with a home PC)")
	model_group.add_argument("--local", "-L", action="store_true", help="Use local models only, not online (for home PC working with a server)")

	if args.max_tokens:
		config["max_new_tokens"] = args.max_tokens

	if args.remote:
		raise ValueError("local_agent called with --remote option, not an error, just avoiding to try to run it on the server")

	if args.local:
		raise ValueError("run_search called with --local option, not an error, just avoiding to run it on the home PC")


	# FIXME this function is too long
	if args.local:
		raise ValueError("remote_agent called with --local option, not an error, just avoiding to run it on the home PC")

	query = query.rstrip() + "\n"  # XXX not used

	# TODO Use a system message?

	if args.local:
		raise ValueError("safe_shell called with --local option, not an error, just avoiding to run it on the home PC")


	# check for mutually exclusive options
	mode_options = [args.interactive, args.file, args.stream, args.watch]
	if [args.file, args.stream, args.watch].count(True) > 1:
		logger.error("Only one of --file, --stream, --watch can be specified")
		sys.exit(1)

	if args.interactive and any([args.watch, args.stream]):
		logger.error("Interactive mode is not compatible with --watch or --stream")
		sys.exit(1)


	# run in the requested mode
	if args.interactive or not any(mode_options):
		logger.info("Interactive mode")
		await interactive(model, args)
	if args.watch:
		logger.info("Watch mode")
		await watch_loop(model, args)
	elif args.file:
		logger.info("File mode")
		await process_file(model, args.file, args)
	elif args.stream:
		logger.error("Stream mode, not implemented yet")
		# stream(model, args)


def load_model_tokenizer(args):
	""" Load the model tokenizer. """
	model = SimpleNamespace()
	models_dir = Path(os.environ["ALLEMANDE_MODELS"])/"llm"
	model_path = Path(models_dir) / args.model
	logger.info("model_path: %r", model_path)
	if args.model and not model_path.exists() and args.model.endswith(".gguf"):
		args.model = args.model[:-len(".gguf")]
		model_path = Path(models_dir) / args.model
	logger.info("model_path: %r", model_path)
	if args.model and model_path.exists():
		abbrev_models = [k for k, v in models.items() if v.get("abbrev") == args.model]
		if len(abbrev_models) == 1:
			args.model = abbrev_models[0]

		# This will block, but it doesn't matter because this is the init for the program.
		model.tokenizer = load_tokenizer(model_path)
		TOKENIZERS[args.model] = model.tokenizer
	else:
		model.tokenizer = None
	logger.info("tokenizer: %r", model.tokenizer)
	return model


def input_with_prefill(prompt, text):
	""" Readline input with a prefill. """
	def hook():
		readline.insert_text(text)
		readline.redisplay()
	readline.set_pre_input_hook(hook)
	result = input(prompt)
	readline.set_pre_input_hook()
	return result


#	query = query.split("\n")[0]
#	logger.debug("query 2: %r", query)

#	query = re.sub(r'(show me|search( for|up)?|find( me)?|look( for| up)?|what(\'s| is) (the|a|an)?)\s+', '', query, re.IGNORECASE)
#	logger.debug("query 4: %r", query)
#	query = re.sub(r'#.*', '', query)
#	logger.debug("query 5: %r", query)
#	query = re.sub(r'[^\x00-~]', '', query)   # filter out emojis
#	logger.debug("query 6: %r", query)
