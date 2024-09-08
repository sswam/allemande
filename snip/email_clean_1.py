def email_clean(eml_content):
    """
    Processes the given .eml content, removing non-text attachments and unnecessary headers.

    Args:
        eml_content (bytes): The content of the .eml file.

    Returns:
        str: Processed .eml content as a string.
    """
    msg = BytesParser(policy=policy.default).parsebytes(eml_content)

    keep_html = True  # Default to True
    
    # Detect if a text/plain part is present
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                payload = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                if payload.strip():  # Check if the plain text part is not empty
                    keep_html = False
                    break
    else:
        if msg.get_content_type() == 'text/plain':
            payload = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            if payload.strip():  # Check if the plain text content is not empty
                keep_html = False

    # Keep only essential headers
    essential_headers = ['From', 'To', 'Subject', 'Date']
    new_msg = EmailMessage()
    for header in essential_headers:
        if header in msg:
            new_msg[header] = msg[header]

    # Remove all attachments except text parts
    if msg.is_multipart():
        new_msg.set_content("")  # Create an empty message
        for part in msg.walk():
            if part.get_content_maintype() == 'text':
                if part.get_content_subtype() == 'plain':
                    payload = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    if not payload.strip().startswith('<html>'):
                        new_msg.add_alternative(payload, subtype='plain')
                elif part.get_content_subtype() == 'html' and keep_html and not new_msg.is_multipart():
                    html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    plain_text = html_to_plain_text(html_content)
                    new_msg.set_content(plain_text)
    else:
        # If the message is not multipart, copy the content
        content_type = msg.get_content_type()
        if content_type == 'text/plain':
            payload = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            if not payload.strip().startswith('<html>'):
                new_msg.set_content(payload)
        elif content_type == 'text/html' and keep_html:
            html_content = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            plain_text = html_to_plain_text(html_content)
            new_msg.set_content(plain_text)

    return convert_email_to_plain_text(new_msg.as_string())
