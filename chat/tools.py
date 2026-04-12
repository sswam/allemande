import re
from pathlib import Path
import logging
import tempfile

import ally_room
import rag
import bb_lib
import conductor
import ally_chat_cli

from settings import SUMMARY_PROMPT_DEFAULT


logger = logging.getLogger(__name__)


async def python_tool_agent_yaml(c, agent, query) -> str:
    """Return a YAML definition for a python_tool agent, optionally filtered by grep pattern."""

    # Split args as agent names
    args = query.split()
    grep_pattern = None

    flat = False

    # Extract grep pattern if present
    for i, arg in enumerate(args):
        if arg.startswith('-g='):
            grep_pattern = arg[3:]
            args.pop(i)
            break
        if arg == "-f":
            flat = True
            args.pop(i)
            break

    result: list[str] = []

    for name in args:
        name = name.replace("_", " ")
        agent = c.agents.get(name) if c.agents else None
        if not agent:
            result.append(f"Agent '{name}' not found")
            continue

        if flat:
            file_content = agent.to_yaml(flat=True).rstrip()
        else:
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


async def python_tool_rag(c, agent, query) -> str:
    """Run RAG queries against a vector database."""
    # Split args
    args = query.strip().split()

    db_name = None
    do_import = False
    limit = 10

    # Extract db name if specified with -d and check for -i flag
    i = 0
    while i < len(args):
        if args[i].startswith('-d='):
            db_name = args[i][3:]
        elif args[i] == '-i':
            do_import = True
        elif args[i].startswith('-n='):
            limit = int(args[i][3:])
        else:
            i += 1
            continue
        args.pop(i)

    if not args:
        return "No query provided"

    # Get query string
    query_text = " ".join(args)

    # If no db specified, use "db" in the file's folder
    if not db_name:
        db_name = "db"

    # Find absolute path to DB
    db_path, db_name_abs = ally_room.relname_to_path(db_name, c.room)

    # Do access control check:  XXX this is privacy risk as responsible_human is not always right
    db_access = ally_room.check_access(c.responsible_human, db_name_abs + ".db")

    access_needed = ally_room.Access.WRITE if do_import else ally_room.Access.READ

    if not db_access.value & access_needed.value == access_needed.value:
        return f"Access denied for database {db_name_abs}"

    logger.info("Using RAG database: %s", db_name_abs)

    try:
        # Create RAG instance
        rag_db = rag.FaissRAG([str(db_path)])

        if do_import:
            # Import texts if -i flag specified
            rag_db.add_entry(query_text)
            results = []

        else:
            # Get results
            results = rag_db.query(query_text, k=limit)

        # Format as blank-line delimited text
        return "\n\n".join(results)

    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error accessing RAG database: {str(e)}", exc_info=True)
        return f"Error accessing RAG database: {str(e)}"


async def python_tool_self_block(c, agent, query, nsfw: bool=False) -> str:
    """Enable a user to block themself from the app or from the NSFW zone and features, for a certain period of time."""

    if c.responsible_human is None:
        return "Error: unable to identify responsible user"

    # Split args as agent names
    time_spec = query.strip()

    result: list[str] = []

    result.append(f"Self-blocking {'NSFW features' if nsfw else 'the app'} for user {c.responsible_human}: {time_spec}")

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


async def python_tool_self_block_nsfw(c, agent, query) -> str:
    """Enable a user to block themself from the NSFW zone and features, for a certain period of time."""
    return python_tool_self_block(c, agent, query, nsfw=True)


async def python_tool_summaries(c, agent, query) -> str | None:
    """Run summaries for each agent in the chat where summary is enabled"""
    history_messages = list(bb_lib.lines_to_messages(c.history))
    participants = conductor.get_all_participants(history_messages)

    summary_agents = []

    config = c.config
    if "agents" not in config:
        config["agents"] = {}

    for user in participants:
        agent = c.agents.get(user)
        if not agent or agent.get("dumb") or agent.get("type") == "human":
            continue
        agent = agent.apply_config(config)
        if agent.get("summary"):
            summary_agents.append(agent)

    contexts = [None, str(c.room.path)]
    rooms_dir = c.room.path.parent

    # TODO could run these in parallel
    for agent in summary_agents:
        with tempfile.NamedTemporaryFile(mode='w') as temp:
            summary_start = agent.get("summary_start", "")
            summary_lines = agent.get("summary_lines", 3)
            summary_stop_regexs = agent.get("summary_stop_regexs", [])
            logger.info("summaries, name %s summary_stop_regexs: %r", agent.name, summary_stop_regexs)

            # FIXME this tempfile stuff sucks...
            temp.write(summary_start)
            temp.flush()

            contexts[0] = temp.name

            name = agent.name.lower()
            summary_role = agent.get("summary_role") or ""
            query = agent.get("summary_prompt") or SUMMARY_PROMPT_DEFAULT
            query = query.replace("$AGENT", agent.name)

            # Apply a long context limit and single line limit
            if name not in config["agents"]:
                config["agents"][name] = {}
            config["agents"][name]["context"] = 1000
            config["agents"][name]["lines"] = summary_lines
            config["agents"][name]["stop_regexs"] = summary_stop_regexs
            config["agents"][name]["forward"] = False
            config["agents"][name]["summary"] = False
            config["agents"][name]["recap"] = False
            config["agents"][name]["recall"] = False
            config["agents"][name]["system_bottom_pos"] = 1200

            # TODO this won't include room missions yet

            responses, _temp_dir = await ally_chat_cli.ally_chat_cli_async(summary_role, agent.name, query, contexts, keep=True, options=config, rooms_dir=rooms_dir)
            if not responses:
                logger.error("summaries, no response from agent: %s", name)
                continue

            user, content = responses[0]
            user = str(user).lower()

            if user != name:
                logger.error("summaries, wrong agent responded for agent: %s -> %s", name, user)
                continue

            # filter out summary_stop_regexs, needed for remote models if prompted to use it
            logger.info("summaries, summary_stop_regexs: %r", summary_stop_regexs)
            if summary_stop_regexs:
                logger.info("summaries, content before filter out STOP: %r", content)
                lines = content.split('\n')
                lines = [line for line in lines if not any(re.search(pattern, line) for pattern in summary_stop_regexs)]
                content = '\n'.join(lines).strip()
                logger.info("summaries, content after filter out STOP: %r", content)

            summary_file = c.room.path.with_suffix(f".{name}.s")

            logger.info("summary from %s:\n%s", name, content)

            # TODO options to save chat file name and timestamp/s
            with open(summary_file, "w") as f:
                f.write(content)

            # run RAG ingest - TODO separate function / module for this?
            if agent.get("remember"):
                recall_file = agent.get("recall_file", agent.name.lower())
                db_path, db_name_abs = ally_room.relname_to_path(recall_file, c.room)
                db_access = ally_room.check_access(c.responsible_human, db_name_abs + ".index")

                if not db_access.value & ally_room.Access.WRITE.value:
                    logger.error("summaries, permission denied to update RAG DB: %s.index", db_name_abs)
                    continue

                try:
                    # Create RAG instance
                    logger.info(f"Saving Faiss DB: %s", str(db_path))
                    rag_db = rag.FaissRAG([str(db_path)])
                    rag_db.add_entry(content)
                    rag_db.save()
                except Exception as e:  # pylint: disable=broad-except
                    logger.error(f"Error accessing RAG database: {str(e)}", exc_info=True)

    return None
    # return [x.name for x in summary_agents]
    # return len(history_messages), history_messages[0], len(participants), participants


python_tools = {
    "agent_yaml": python_tool_agent_yaml,
    "rag": python_tool_rag,
    "self_block": python_tool_self_block,
    "self_block_nsfw": python_tool_self_block_nsfw,
    "summaries": python_tool_summaries,
}
