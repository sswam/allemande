def clean_prompt(context, name, delim):
    """Clean the prompt for image gen agents and tools."""
    # No longer needed, replaced with trivial version for now.
    return "".join(context)

    # The following shouldn't be needed now:

    logger.info("clean_prompt: before: %s", context)

    agent_name_esc = regex.escape(name)

    # Remove speaker name at start
    if context:
        context[0] = re.sub(r"^\w.*?:\t", "\t", context[0])

    # Remove one initial tab from each line in the context, if all lines start with a tab
    if all(line.startswith('\t') for line in context):
        context = [regex.sub(r"(?m)^\t", "", line) for line in context]

    # Join all lines in context with the specified delimiter
    text = delim.join(context)

    logger.info("clean_prompt: 1: %s", text)

    # Remove up to the first occurrence of the agent's name (case insensitive) and any following punctuation, with triple backticks
    text1 = regex.sub(
        r".*?```\w*\s*@?" + agent_name_esc + r"\b[,;.!:]*(.*?)```.*", r"\1", text, flags=regex.DOTALL | regex.IGNORECASE, count=1
    )

    logger.info("clean_prompt: 2: %s", text1)

    # # Remove up to the first occurrence of the agent's name (case insensitive) and any following punctuation, with triple backticks after the name
    # if text1 == text:
    #     text1 = regex.sub(
    #         r".*?\b?" + agent_name_esc + r"\b[,;.!:]*\s*```\w*\s*(.*?)```.*", r"\1", text, flags=regex.DOTALL | regex.IGNORECASE, count=1
    #     )

    # Remove up to the first occurrence of the agent's name (case insensitive) and any following punctuation, with single backticks
    if text1 == text:
        text1 = regex.sub(
            r".*?`\s*@?" + agent_name_esc + r"\b[,;.!:]*(.*?)`.*", r"\1", text, flags=regex.DOTALL | regex.IGNORECASE, count=1
        )

    logger.info("clean_prompt: 3: %s", text1)

    # Remove up to the first occurrence of the agent's name (case insensitive) at start of line, and any following punctuation
    if text1 == text:
        text1 = regex.sub(r".*?^\s*@?" + agent_name_esc + r"\b[,;.!:]*", r"", text, flags=regex.DOTALL | regex.IGNORECASE | regex.MULTILINE, count=1)
        text1 = re.sub("```\w*", "", text1)

        logger.info("clean_prompt: 4: %s", text1)

        original = text1
        text1 = re.sub(r".*```(?:\w*\n)?(.*?)```.*", r"\1", text1, flags=re.DOTALL, count=1)
        if text1 == original:  # If no change, try single backticks
            text1 = re.sub(r".*`(.*?)`.*", r"\1", text1, flags=re.DOTALL, count=1)
        if text1 == original:  # If no change, remove anything after a blank line
            text1 = re.sub(r"\n\n.*", r"", text1, flags=re.DOTALL)

        logger.info("clean_prompt: 5: %s", text1)

    text = text1

    # Remove leading and trailing whitespace
    text = text.strip()

    # Decode &lt; &gt; &amp;
    text = html.unescape(text)

    logger.info("clean_prompt: after: %s", text)
    return text
