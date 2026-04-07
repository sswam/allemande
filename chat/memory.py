import logging
import re

import ally_room
import rag
from util import uniqo
from ally import stopwords
import bb_lib


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# TODO remove context_format_is_messages option
def apply_recall(agent, context, c, context_format_is_messages=False):
    recall_file = agent.get("recall_file", agent.name.lower())
    recall_limit = agent.get("recall_limit", 3)
    recall_pos = agent.get("recall_pos", -1)
    recall_role = agent.get("recall_role", None)
    recall_prefix = agent.get("recall_prefix", None)
    recall_suffix = agent.get("recall_suffix", None)
    recall_context = agent.get("recall_context", 1)
    recall_strip = agent.get("recall_strip", False)

    db_path, db_name_abs = ally_room.relname_to_path(recall_file, c.room)
    db_access = ally_room.check_access(c.responsible_human, db_name_abs + ".index")

    if not db_access.value & ally_room.Access.READ.value:
        return

    try:
        # Create RAG instance
        rag_db = rag.FaissRAG(str(db_path))

        query_list = []
        for i in range(min(recall_context, len(context))):
            query_list.append(context[-1-i])

        if context_format_is_messages:
            query_list = list(bb_lib.messages_to_lines(query_list))

        results = []

        for query in query_list:
            logger.info("RAG query 1: %r", query)
            query = re.sub(r"```.*?```|`.*?`", "", query, flags=re.DOTALL)
            logger.info("RAG query 2: %r", query)
            if recall_strip:
                query = stopwords.strip_stopwords(query, strict=True)
                logger.info("RAG query 3: %r", query)

            results += rag_db.query(query, k=recall_limit)

        if not results:
            return

        # Format as blank-line delimited text
        recall_text = "\n\n".join(uniqo(results))

        if recall_prefix:
            recall_prefix = recall_prefix.replace("$NAME", agent.name)
            recall_text = recall_prefix + "\n\n" + recall_text
        if recall_suffix:
            recall_suffix = recall_suffix.replace("$NAME", agent.name)
            recall_text = recall_text + "\n\n" + recall_suffix

        logger.info("recall_text: %r", recall_text)

        n_messages = len(context)
        pos = min(recall_pos, n_messages)
        if recall_role is None:
            recall_role = agent.name
        if recall_role:
            recall_message = f"{recall_role}:\t{recall_text}"
        else:
            recall_message = recall_text
        if context_format_is_messages:
            recall_message = next(bb_lib.lines_to_messages([recall_message]))
        context.insert(n_messages - pos, recall_message)

        logger.debug("recall_text: %r", recall_text)

    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error accessing RAG database: {str(e)}", exc_info=True)
