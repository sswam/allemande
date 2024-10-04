def register_agents_local():
	""" Register LLM local agents """
	def make_agent(agent_base):
		agent = agent_base.copy()
		agent["fn"] = lambda *args, **kwargs: asyncio.create_task(local_agent(agent, *args, **kwargs))
		agent["type"] = "local"
		if "name" not in agent:
			agent["name"] = agent_name
		return agent

	for agent_name, agent_base in AGENTS_LOCAL.items():
		agent_lc = agent_name.lower()
		agent = AGENTS[agent_lc] = make_agent(agent_base)
		name_lc = agent["name"].lower()
		if name_lc != agent_lc:
			AGENTS[name_lc] = agent


def register_agents_search():
	""" Register search engines """
	def make_agent(agent_base):
		agent = agent_base.copy()
		agent["fn"] = lambda *args, **kwargs: asyncio.create_task(run_search(agent, *args, **kwargs))
		agent["type"] = "tool"
		if "name" not in agent:
			agent["name"] = agent_name
		return agent

	for agent_name in search.agents:
		agent_lc = agent_name.lower()
		agent_base = { "name": agent_name }
		AGENTS[agent_lc] = make_agent(agent_base)
	if not ADULT:
		del AGENTS["Pr0nto"]
#	AGENTS["duck"] = AGENTS["duckduckgo"]


def register_agents_remote():
	""" Register LLM API agents """
	def make_agent(agent_base):
		agent = agent_base.copy()
		agent["fn"] = lambda *args, **kwargs: asyncio.create_task(remote_agent(agent, *args, **kwargs))
		agent["type"] = "remote"
		if "name" not in agent:
			agent["name"] = agent_name
		return agent

	for agent_name, agent_base in AGENTS_REMOTE.items():
		agent_lc = agent_name.lower()
		agent = AGENTS[agent_lc] = make_agent(agent_base)
		name_lc = agent["name"].lower()
		if name_lc != agent_lc:
			AGENTS[name_lc] = agent


def register_agents_programming():
	""" Register programming language agents """
	def make_agent(agent_base):
		agent = agent_base.copy()
		agent["fn"] = lambda *args, **kwargs: asyncio.create_task(safe_shell(agent, *args, **kwargs))
		agent["type"] = "tool"
		if "name" not in agent:
			agent["name"] = agent_name
		return agent

	for agent_name, agent_base in AGENTS_PROGRAMMING.items():
		agent_lc = agent_name.lower()
		agent = AGENTS[agent_lc] = make_agent(agent_base)
		name_lc = agent["name"].lower()
		if name_lc != agent_lc:
			AGENTS[name_lc] = agent




	with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
		proc.stdin.write(query.encode("utf-8"))
		proc.stdin.close()
		# read the output and stderr
		output = proc.stdout.read().decode("utf-8")
		errors = proc.stderr.read().decode("utf-8")
		status = proc.wait()


def find_files(folder, ext=None, maxdepth=inf):
	""" Find chat files under a directory. """
	# FIXME this sync function is potentially slow
	if not os.path.isdir(folder):
		print("?", file=sys.stderr, end="", flush=True)
		return
	try:
		for subdir in os.scandir(folder):
			if subdir.is_dir():
				if subdir.name.startswith("."):
					continue
				if maxdepth > 0:
					yield from find_files(subdir.path, ext, maxdepth - 1)
			elif subdir.is_file():
				if not ext or subdir.name.endswith(ext):
					yield subdir.path
	except (PermissionError, FileNotFoundError) as e:
		logger.warning("find_files: %r", e)

