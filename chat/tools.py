import re
from pathlib import Path

import ally_room
import rag


def python_tool_agent_yaml(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None, responsible_human: str | None=None) -> str:
    """Return a YAML definition for a python_tool agent, optionally filtered by grep pattern."""

    # Split args as agent names
    args = query.split()
    grep_pattern = None

    # Extract grep pattern if present
    for i, arg in enumerate(args):
        if arg.startswith('-g='):
            grep_pattern = arg[3:]
            args.pop(i)
            break

    result: list[str] = []

    for name in args:
        name = name.replace("_", " ")
        agent = agents.get(name) if agents else None
        if not agent:
            result.append(f"Agent '{name}' not found")
            continue

        file_content = agent.get_file().rstrip()

        # Apply grep filter if pattern specified
        if grep_pattern:
            filtered_lines = []
            for line in file_content.split('\n'):
                if re.search(grep_pattern, line):
                    filtered_lines.append(line)
            file_content = '\n'.join(filtered_lines)

        result.append(file_content)

    return "\n\n".join(result)


def python_tool_rag(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None, responsible_human: str | None=None) -> str:
    """Run RAG queries against a vector database."""
    # Split args
    args = query.strip().split()

    db_name = None
    do_import = False

    # Extract db name if specified with -d and check for -i flag
    i = 0
    while i < len(args):
        if args[i].startswith('-d='):
            db_name = args[i][3:]
        elif args[i] == '-i':
            do_import = True
        else:
            i += 1
            continue
        args.pop(i)

    if not args:
        return "No query provided"

    # Get query string
    query_text = " ".join(args)

    # If no db specified, use stem of file as db name
    if not db_name:
        db_name = Path(file).stem

    # Do access control check
    room = ally_room.Room(path=Path(file))
    db_access = room.check_access(responsible_human)

    access_needed = ally_room.Access.WRITE if do_import else ally_room.Access.READ

    if not db_access.value & access_needed == access_needed:
        return f"Access denied for database {db_name}"

    try:
        # Create RAG instance
        rag_db = rag.FaissRAG(db_name)

        if do_import:
            # Import texts if -i flag specified
            rag_db.add_entry(query_text)
            results = []

        else:
            # Get results
            results = rag_db.query(query_text)

        # Format as blank-line delimited text
        return "\n\n".join(results)

    except Exception as e:  # pylint: disable=broad-except
        return f"Error accessing RAG database: {str(e)}"


def python_tool_self_block(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None, responsible_human: str | None=None, nsfw: bool=False) -> str:
    """Enable a user to block themself from the app or from the NSFW zone and features, for a certain period of time."""

    if responsible_human is None:
        return "Error: unable to identify responsible user"

    # Split args as agent names
    time_spec = query.strip()

    result: list[str] = []

    result.append(f"Self-blocking {'NSFW features' if nsfw else 'the app'} for user {responsible_human}: {time_spec}")

    # for name in args:
    #     name = name.replace("_", " ")
    #     agent = agents.get(name) if agents else None
    #     if not agent:
    #         result.append(f"Agent '{name}' not found")
    #         continue

    #     file_content = agent.get_file().rstrip()

    #     # Apply grep filter if pattern specified
    #     if grep_pattern:
    #         filtered_lines = []
    #         for line in file_content.split('\n'):
    #             if re.search(grep_pattern, line):
    #                 filtered_lines.append(line)
    #         file_content = '\n'.join(filtered_lines)

    #     result.append(file_content)

    return "\n\n".join(result)


def python_tool_self_block_nsfw(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None, responsible_human: str | None=None) -> str:
    """Enable a user to block themself from the NSFW zone and features, for a certain period of time."""
    return python_tool_self_block(agent, query, file, args, history, history_start, mission, summary, config, agents, responsible_human, nsfw=True)


python_tools = {
    "agent_yaml": python_tool_agent_yaml,
    "rag": python_tool_rag,
    "self_block": python_tool_self_block,
    "self_block_nsfw": python_tool_self_block_nsfw,
}
