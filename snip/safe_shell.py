# format the response
response = ""
if errors or status: # or not eol:
    info = []
    if status:
        info.append(f"status: {status}")
    # if not eol:
    #     info.append("no EOL")
    if info:
        response += ", ".join(info) + "\n\n"
    if errors:
        response += "## errors:\n```\n" + errors + "\n```\n\n"
    response += "## output:\n"
