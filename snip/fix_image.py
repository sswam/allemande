def process_tokens(tokens):
    nonlocal has_math
    for token in tokens:
        if token.children:
            process_tokens(token.children)
        if token.type == 'link_open':
            token.attrs['href'] = fix_link(token.attrs['href'], bb_file)
        elif token.type == 'image':
            fix_image(token, bb_file)
        logger.info("token.type: %s", token.type)


def fix_image(token: markdown_it.token.Token, bb_file: str) -> None:
    """Load image metadata: width, height, alt text"""
    src = token.attrs.get("src")
    if not src:
        return
    url = urlparse(src)
    if url.scheme or url.netloc:
        return
    logger.info("Trying to match image: %r", src)
    # relative to bb_file
    try:
        safe_path, _rel_path = safe_path_for_local_file(bb_file, src)
    except ValueError as e:
        logger.warning("Invalid path: %s", e)
        return
    if not os.path.exists(safe_path):
        logger.warning("Image file not found: %s", safe_path)
        return
    try:
        md = stamps.get_image_metadata(safe_path)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Error reading image metadata: %s: %s", safe_path, e)
        return
    if not md:
        return
    if md.width:
        token.attrs["width"] = str(md.width)
    if md.height:
        token.attrs["height"] = str(md.height)
    if md.alt_text:
        alt_old = token.attrs.get("alt")
        token.attrs["alt"] = md.alt_text + (" ---- " + alt_old if alt_old else "")
    return
