def check_file_type(path):

    if ext == ".yml" and path.startswith(str(settings.PATH_ROOMS)+"/") and "agents" in Path(path).parts and not Path(path).is_symlink():
        return "agent_private"


async def watch_loop(args):

                elif file_type == "agent_private":
                    room = ally_room.Room(path=(Path(file_path).parent)/"chat.bb")
                    agents1 = load_local_agents(room, agents)
                    agents1.handle_file_change_private(file_path, change_type)
