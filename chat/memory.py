import logging
import re
import asyncio
from copy import deepcopy
import tempfile

import ally_room
import rag
from util import uniqo
from ally import stopwords
import bb_lib
from settings import REMOTE_AGENT_RETRIES, PATH_ROOMS, PATH_HOME, AGENT_CONTEXT_DEFAULT
import ally_chat_cli


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_recap_locks = {}


async def apply_recall(agent, context, c):
    """
    Enable the agent to recall summaries of recent chats,
    and relevant summaries of less recent chats.
    TODO: use async
    """
    recall_file = agent.get("recall_file", agent.name.lower())
    recall_recent = agent.get("recall_recent", 3)
    recall_limit = agent.get("recall_limit", 3)
    recall_pos = agent.get("recall_pos", -1)
    recall_role = agent.get("recall_role", agent.name)
    recall_prefix = agent.get("recall_prefix", None)
    recall_suffix = agent.get("recall_suffix", None)
    recall_context = agent.get("recall_context", 3)
    recall_strip = agent.get("recall_strip", False)

    db_path, db_name_abs = ally_room.relname_to_path(recall_file, c.room)
    db_access = ally_room.check_access(c.responsible_human, db_name_abs + ".index")

    if not db_access.value & ally_room.Access.READ.value:
        return

    try:
        # Create RAG instance
        rag_db = rag.FaissRAG([str(db_path)])
        n = len(rag_db)

        query_list = []
        for i in range(min(recall_context, len(context))):
            query_list.append(context[-1-i])

        # Look up relevant memories

        results_ix = []

        for query in query_list:
            # Remove quoted code such as image prompts. Might sometimes want to keep it, though.
            query = re.sub(r"```.*?```|`.*?`", "", query, flags=re.DOTALL)
            if recall_strip:
                query = stopwords.strip_stopwords(query, strict=True)
            logger.info("RAG query: %s", query)

            results_ix += rag_db.query_indices(query, k=recall_limit)

        logger.debug("apply_recall 1: n, results_ix: %s, %r", n, results_ix)

        if results_ix:
            # get unique result indices in order (~chronological)
            results_ix = sorted(set(results_ix))

            logger.debug("apply_recall 2:    results_ix:     %r", results_ix)

            # get texts
            results = [rag_db[i] for i in results_ix]

            # Format as blank-line delimited text
            # recall_text = "\n\n".join(reversed(uniqo(reversed(results))))
            recall_text = "\n\n".join(results)

            if recall_prefix:
                recall_prefix = recall_prefix.replace("$NAME", agent.name)
                recall_text = recall_prefix + "\n\n" + recall_text
            if recall_suffix:
                recall_suffix = recall_suffix.replace("$NAME", agent.name)
                recall_text = recall_text + "\n\n" + recall_suffix

            logger.info("recall_text:\n%s\n", recall_text)

            n_messages = len(context)
            pos = min(recall_pos, n_messages)
            if recall_role:
                recall_message = f"{recall_role}:\t{recall_text}"
            else:
                recall_message = recall_text
            context.insert(n_messages - pos, recall_message)

            logger.debug("recall_text: %r", recall_text)

        # Add a few recent memories
        recent_ix = [i for i in range(max(0, n-recall_recent), n) if i not in results_ix]
        if recent_ix:
            results = [rag_db[i] for i in recent_ix]
            recall_text = "\n\n".join(results)
            if recall_role:
                recall_message = f"{recall_role}:\t{recall_text}"
            else:
                recall_message = recall_text
            context.insert(0, recall_message)

            logger.debug("recent recall_text: %r", recall_text)

    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error accessing RAG database: {str(e)}", exc_info=True)


def get_recap_lock(chat_id, agent_id):
    """ Get a lock to prevent concurrent access / update for an agent's recap of a chat """
    key = (chat_id, agent_id)
    if key not in _recap_locks:
        lock = _recap_locks[key] = asyncio.Lock()
        return lock
    return _recap_locks[key]


async def apply_and_update_recap(agent, context, c):
    """
    Enable the agent to recall a summary of earlier parts of the current chat,
    that are (partly) out of context - the recap. This also updates the "recap"
    as needed (if enabled).
    """
    n_context = agent.get("context", AGENT_CONTEXT_DEFAULT)
    recap_min_context = agent.get("recap_min_context", AGENT_CONTEXT_DEFAULT)
    if n_context < recap_min_context:
        return

    room_name = c.room.name
    agent_name = agent.name.lower()
    logger.info("apply_and_update_recap for: %r, %r", room_name, agent_name)
    lock = get_recap_lock(room_name, agent_name)
    recall_role = agent.get("recall_role", agent.name)
    recap_keep_old = agent.get("recap_keep_old", False)

    async with lock:
        # find recap file
        room_path = c.room.path
        pattern = f"{room_path.stem}.{agent_name}.*.r"
        recap_files = list(room_path.parent.glob(pattern))
        recap_file = None
        count = None
        room_len = len(c.history)
        logger.info("  room_len: %s", room_len)
        logger.info("  n_context: %s", n_context)
        logger.info("  found recap_files: %r", recap_files)
        for f in recap_files:
            match = re.search(r'(\d+)\.r$', str(f))
            if not match:
                logger.error("apply_and_update_recap: unexpected filename without count: %s", str(f))
                continue
            count2 = int(match.group(1))
            if count2 > room_len:
                # room shrunk and summary is out of date, remove it
                logger.info("apply_and_update_recap: removing overlapping recap file: %s", str(f))
                (room_path.parent / f).unlink()
                continue
            if count is None or count2 > count:
                recap_file = f
                count = count2
        if recap_file is not None:
            logger.info("  found recap file: %r", recap_file)
            logger.info("  count: %s", count)
        else:
            logger.info("apply_and_update_recap: no recap file")

        recap_text = None
        if recap_file:
            recap_text = recap_file.read_text(encoding="utf-8")

        # (re-)create recap file if needed; and set recap_text
        if not recap_file:
            count = 0
        if count + n_context < room_len:
            count2 = count
            while count2 + n_context < room_len:
                count2 += n_context
            logger.info("apply_and_update_recap: building recap file of length: %s (was %s)", count2, count)
            # remove any old file
            recap_file_new, recap_text_new = await build_recap_file(agent, c, recap_text, count, count2)
            if recap_file_new and recap_file and not recap_keep_old:
                (room_path.parent / recap_file).unlink()
            if recap_file_new:
                recap_file, recap_text = recap_file_new, recap_text_new
            # If it failed, proceed with previous recap for now (if any)

        if recap_text:
            if recall_role:
                recap_message = f"{recall_role}:\t{recap_text}"
            else:
                recap_message = recap_text
            logger.info("recap_message:\n%s", recap_message)
            context.insert(0, recap_message)


async def build_recap_file(agent, c, recap_text, start, end):
    """ Build a recap file """

    # For "full" mode, make a new summary of the whole chat
    if agent.get("recap_type") == "full":
        recap_text = None
        start = 0

    # Get context for new summary and reformat it neatly
    context = c.history[start:end]
    context_messages = list(bb_lib.lines_to_messages(context))
    context = list(bb_lib.messages_to_lines(context_messages))

    text = "\n".join(context) + "\n"

    logger.info("build_recap_file: text:\n[%s]", text)

    summary_start = agent.get("summary_start", "")
    summary_lines = agent.get("summary_lines", 3)
    summary_stop_regexs = agent.get("summary_stop_regexs", [])
    recap_min_length = agent.get("recap_min_length", 0)

    with tempfile.NamedTemporaryFile(mode='w') as temp:
        context_text = "\n\n".join([x for x in [summary_start, recap_text, text] if x])
        temp.write(context_text)
        temp.flush()

        contexts = [temp.name]

        config = deepcopy(c.config)
        if "agents" not in config:
            config["agents"] = {}

        rooms_dir = c.room.path.parent

        name = agent.name.lower()
        summary_role = agent.get("summary_role") or ""  # no separate recap_summary_role
        query = agent.get("recap_prompt") or agent.get("summary_prompt") or SUMMARY_PROMPT_DEFAULT
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

        responses, _temp_dir = await ally_chat_cli.ally_chat_cli_async(summary_role, agent.name, query, contexts, keep=True, options=config, rooms_dir=rooms_dir)
        if not responses:
            logger.error("build_recap_file, no response from agent: %s", name)
            return None, ""

        user, content = responses[0]
        user = str(user).lower()

        # filter out summary_stop_regexs, needed for remote models if prompted to use it
        if summary_stop_regexs:
            lines = content.split('\n')
            lines = [line for line in lines if not any(re.search(pattern, line) for pattern in summary_stop_regexs)]
            content = '\n'.join(lines).strip()

        if user != name:
            logger.error("build_recap_file, wrong agent responded for agent: %s -> %s", name, user)
            return None, ""

        if len(content) < recap_min_length:
            logger.error("build_recap_file, response too short: %s < %s", len(content), recap_min_length)
            return None, ""

        recap_file = c.room.path.with_suffix(f".{name}.{end}.r")

        logger.info("recap from %s:\n%s", name, content)

        # TODO options to save chat file name and timestamp/s
        with open(recap_file, "w") as f:
            f.write(content)

        return recap_file, content
