#!/usr/bin/env python3

import sys
import logging
import email
from email.parser import BytesParser
from email.message import EmailMessage
from email import policy
import email
import html
import subprocess
import tempfile
import os

import argh


logger = logging.getLogger(__name__)


"""
email_clean.py - A script to process .eml files, removing non-text attachments
and unnecessary headers.

This script can be used as a module:
    from email_clean import email_clean
"""


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


def html_to_plain_text(html_content):
    """
    Convert HTML content to plain text using pandoc-dump.
    """
    try:
        # Create a temporary file to store the HTML content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(html_content)
            temp_file_path = temp_file.name

        # Use the temporary file path for pandoc conversion
        process = subprocess.Popen(['pandoc-dump', temp_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            logger.error(f"pandoc error: {stderr.decode('utf-8')}")
            return html_content  # Return original HTML content if pandoc fails

        plain_text = stdout.decode('utf-8')

    except Exception as e:
        logger.error(f"Error converting HTML to plain text: {e}")
        plain_text = html_content  # Return original HTML content if conversion fails

    finally:
        # Clean up the temporary file
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Error deleting temporary file: {e}")

    return plain_text


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


@argh.arg('--debug', help='enable debug logging')
@argh.arg('--verbose', help='enable verbose logging')
def main(debug=False, verbose=False):
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
    output_content = email_clean(input_content)
    sys.stdout.write(output_content)

if __name__ == '__main__':
    try:
        argh.dispatch_command(main)
    except Exception as e:
        logger.error(e)
        sys.exit(1)
