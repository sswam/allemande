#!/usr/bin/env python3

import sys
import logging
import email
from email.parser import BytesParser
from email.policy import default
import email
import html

import argh


logger = logging.getLogger(__name__)


"""
email_clean.py - A script to process .eml files, removing non-text attachments
and unnecessary headers.

This script can be used as a module:
    from email_clean import email_clean
"""


def email_clean(eml_content, keep_html=False):
    """
    Processes the given .eml content, removing non-text attachments and unnecessary headers.

    Args:
        eml_content (bytes): The content of the .eml file.
        keep_html (bool): Whether to keep HTML content if no plain text is available.

    Returns:
        str: Processed .eml content as a string.
    """
    msg = BytesParser(policy=default).parsebytes(eml_content)

    logger.debug(f"Original headers: {list(msg.keys())}")

    # Keep only essential headers
    essential_headers = ['From', 'To', 'Subject', 'Date']
    new_msg = email.message.EmailMessage()
    for header in essential_headers:
        if header in msg:
            new_msg[header] = msg[header]

    logger.debug(f"Remaining headers: {list(new_msg.keys())}")

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
                    new_msg.add_alternative(part.get_payload(decode=True).decode('utf-8', errors='ignore'), subtype='html')
    else:
        # If the message is not multipart, copy the content
        content_type = msg.get_content_type()
        if content_type == 'text/plain':
            payload = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            if not payload.strip().startswith('<html>'):
                new_msg.set_content(payload)
        elif content_type == 'text/html' and keep_html:
            new_msg.set_content(msg.get_payload(decode=True).decode('utf-8', errors='ignore'), subtype='html')

    return convert_email_to_plain_text(new_msg.as_string())


def convert_email_to_plain_text(email_content):
    # Parse the email content
    msg = email.message_from_string(email_content)

    # Extract headers
    headers = []
    for header, value in msg.items():
        if header.lower() not in ('content-type', 'mime-version'):
            headers.append(f"{header}: {value}")

    # Extract the plain text parts
    plain_text_parts = []
    for part in msg.walk():
        if part.get_content_type() == 'text/plain':
            payload = part.get_payload(decode=True)
            charset = part.get_content_charset() or 'utf-8'

            # Decode the payload using the correct charset
            decoded_text = payload.decode(charset, errors='replace')

            plain_text_parts.append(decoded_text)

    # Combine all plain text parts
    combined_text = '\n'.join(plain_text_parts)

    # Unescape HTML entities
    unescaped_text = html.unescape(combined_text)

    # Combine headers and body
    result = '\n'.join(headers) + '\n\n' + unescaped_text.strip() + '\n'

    return result


@argh.arg('--keep-html', help='keep HTML content if no plain text is available')
@argh.arg('--debug', help='enable debug logging')
@argh.arg('--verbose', help='enable verbose logging')
def main(keep_html=False, debug=False, verbose=False):
    """
    email_clean.py - A script to process .eml files, removing non-text attachments
    and unnecessary headers.

    This script reads an .eml file from stdin and writes the processed .eml to stdout.

    Usage:
        cat input.eml | python3 email_clean.py [--keep-html] [--debug] [--verbose]
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    input_content = sys.stdin.buffer.read()
    output_content = email_clean(input_content, keep_html=keep_html)
    sys.stdout.write(output_content)

if __name__ == '__main__':
    try:
        argh.dispatch_command(main)
    except Exception as e:
        raise(e)
        logger.error(repr(e))
        sys.exit(1)
