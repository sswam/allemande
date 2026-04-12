        if context_format_is_messages:
            query_list = list(bb_lib.messages_to_lines(query_list))

            if context_format_is_messages:
                recall_message = next(bb_lib.lines_to_messages([recall_message]))
