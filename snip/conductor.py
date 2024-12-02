

class ConductorOptions: # pylint: disable=too-few-public-methods
	""" the options for the Conductor class """
	exts = ()


class Conductor:
	""" decide which agent/s should respond to a message and invoke them """

	def __init__(self, opts, watch_log):
		""" Initialize the Conductor object """
		self.opts = opts
		self.watch_log = watch_log
		self.tail = atail.AsyncTail(filename=self.watch_log, follow=True, rewind=True).run()

	async def run(self):
		""" watch bb chat files, and invoke agents to reply to them where appropriate """
		# TODO factor this with bb2html
		logger.debug("opts: %s", self.opts)
		async for line in self.tail:
			logger.debug("line from tail: %s", line)
			bb_file, change_type, old_size, new_size = line.rstrip("\n").split("\t")
			change_type = Change(int(change_type))
			old_size = int(old_size) if old_size != "" else None
			new_size = int(new_size) if new_size != "" else None
			if not bb_file.endswith(self.opts.exts):
				continue
			html_file = str(Path(bb_file).with_suffix(".html"))
			if change_type == Change.deleted:
				Path(html_file).unlink(missing_ok=True)
				continue
			async for row in self.file_changed(bb_file, html_file, old_size, new_size):
				yield row

	async def file_changed(self, bb_file, html_file, old_size, new_size):
		""" check which agent to invoke, if any, and invoke it """
		pass

#		# assume the file was appended to ...
#		html_file_mode = "a"
#
#		# ... unless the file has shrunk
#		if old_size and new_size < old_size:
#			logger.warning("bb file was truncated: %s from %s to %s", bb_file, old_size, new_size)
#			html_file_mode = "w"
#
#		with open(bb_file, "r", encoding="utf-8") as bb:
#			with open(html_file, html_file_mode, encoding="utf-8") as html:
#				html_file_size = html.tell()
#				if old_size and html_file_size:
#					bb.seek(old_size)
#				for message in chat.lines_to_messages(bb):
#					print(chat.message_to_html(message), file=html)
#				row = [html_file]
#				yield row

async def conductor_main(opts, watch_log, out=sys.stdout):
	""" Main function """
	conductor = Conductor(opts=opts, watch_log=watch_log)
	async for row in conductor.run():
		print(*row, sep="\t", file=out)


def get_opts():
	""" Get the command line options """
	parser = argparse.ArgumentParser(description="conductor: decide which agent/s should respond to the chat and invoke them", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-w', '--watch-log', default="/dev/stdin", help="the file where changes are logged")
	parser.add_argument('-x', '--extension', nargs="*", default=("bb",), help="the file extensions to process")
	ucm.add_logging_options(parser)
	opts = parser.parse_args()
	return opts


def main():
	""" Main function """
	opts = get_opts()
	ucm.setup_logging(opts)
	exts = tuple(f".{ext}" for ext in opts.extension or ())
	opts.exts = exts
	ucm.run_async(conductor_main(opts=opts, watch_log=opts.watch_log))


if __name__ == '__main__':
	main()


# The term "agent" includes humans, AI bots, and non-AI software agents.

# We could detect vocative phrases (e.g. "Hi Name") and respond to them.

# To keep it simple, just detect if any agent is named, and the first agent
# named is the one invoked.

# TODO perhaps if the agent's name is a single letter or a common noun, we
# should not ignore case e.g. if an agent was called "C" or "And" or "Python".

# TODO distinguish human agents, AI agents, and non-AI software agents.
# "anyone" and "everyone" would refer to AI agents.
# The conductor could never force a human to respond, but it might notify the
# user more loudly than normal.

# anyone should be a random choice among AI-agents or humans maybe:
# from random import choice

# This is just a rough prototype. Going forward we could use a more
# sophisticated NLP library like spaCy or a model, if necessary.

# TODO should the conductor actually add the agent's invitation to the file?  like Foo:
# Or how will it fit in to the scheme of things?

# bb2html reads the watch.log
# I think that other independent processes can also read the watch.log, that should be okay.
# We could assume that each agent runs a core process, using port directories to communicate with clients.
# Perhaps the conductor process can tie it all together, that would make sense.
# In that case, this library might be called who instead of conductor.



regex_name = r"^[\p{L}\p{M}']+([\p{Zs}\-][\p{L}\p{M}']+)*$"

# Matches names containing letters, diacritics, apostrophes, with optional spaces/hyphens between parts. Requires minimum 1 character. Disallows consecutive spaces/hyphens or spaces/hyphens at start/end.

# \p{L} - letters
# \p{M} - marks/diacritics
# \p{Zs} - spaces
# ' - apostrophes
# \- - hyphens


# TODO lib
def uniqo(l):
	# unique in order
	return list(dict.fromkeys(l))


# obsolescent get_roles_from_history function --------------------------------------

def get_roles_from_history(history, user, bot):
	""" Get the latest user and bot names from history """

	recent = reversed(history[-20:])
	print("recent: ", recent)
	roles = map(lambda line: line.split(":")[0], recent)
	print("roles: ", roles)
	roles = uniqo(roles)
	print("roles: ", roles)
	roles = list(filter(lambda role: role and regex.match(regex_name, role), roles))
	print("roles: ", roles)
	if roles:
		user = roles[0]
#	What did this do?!
#	if len(roles) > 1 and random.random() < 0.5 and "Ally" in roles and user != "Ally":
#		return user, "Ally"
	if len(roles) > 1:
		# return a random out of the remaining roles
		bot = random.choice(roles[1:])
	print("user, bot:", user, bot)

	return user, bot


