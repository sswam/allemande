# REMOVED: NSFW and private agent preloading
# NSFW agents (~17) and private agents will be loaded per-room via load_local_agents()
# This prevents leaking private/NSFW agents to unauthorized users
# for agents_dir in Path(settings.PATH_ROOMS).rglob('agents'):
#     if agents_dir == rooms_public_agents:
#         continue
#     if agents_dir.is_dir():
#         agents.load(agents_dir, private=True)
