
# TODO: remove this

def tail_f_n0_old(filename, n=0, interval=1.0):
	if n > 0:
		sh.tail(filename, n=n, _out=sys.stdout, _err=sys.stderr)
	file_pos = None
	while True:
		try:
			with open(filename, 'r') as f:
				if file_pos is None or file_pos > os.path.getsize(filename):
					f.seek(0, os.SEEK_END)
				else:
					f.seek(file_pos)
				new_lines = f.readlines()
				if new_lines:
					print(''.join(new_lines), end='')
					sys.stdout.flush()
				file_pos = f.tell()

		except FileNotFoundError:
			pass

		time.sleep(interval)


class AsyncFileFollower:
	def __init__(self, file_path, return_whole_file=False):
		self.file_path = file_path
		self.return_whole_file = return_whole_file

	async def follow(self):
		if not Path(self.file_path).exists():
			await self._wait_for_file_creation()

		async with aiofiles.open(self.file_path, mode='r') as f:
			if self.return_whole_file:
				content = await f.read()
				yield content

			watcher = aionotify.Watcher()
			watcher.watch(self.file_path, aionotify.Flags.MODIFY)
			await watcher.setup(asyncio.get_event_loop())

			while True:
				while line := await f.readline():
					yield line
				await watcher.get_event()

			watcher.close()
