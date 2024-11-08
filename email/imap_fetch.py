#!/usr/bin/env python3-allemande

import sys
import logging
import os
import argh
from imapclient import IMAPClient
import email
from email.header import decode_header

logger = logging.getLogger(__name__)

"""
imap_fetch.py - A command-line tool to fetch unread emails from an IMAP server.

This script can be used as a module:
    from imap_fetch import fetch_emails
"""

def connect_to_imap():
    host = os.environ.get('IMAP_HOST')
    username = os.environ.get('IMAP_USER')
    password = os.environ.get('IMAP_PASSWORD')

    if not all([host, username, password]):
        raise ValueError("IMAP_HOST, IMAP_USER, and IMAP_PASSWORD environment variables must be set")

    server = IMAPClient(host, use_uid=True)
    server.login(username, password)
    return server

def fetch_emails(folder="INBOX", mark_as_read=False, metadata_only=False):
    """
    Fetches unread emails from the specified IMAP folder.

    Args:
        folder (str): IMAP folder to fetch emails from.
        mark_as_read (bool): Whether to mark fetched emails as read.
        metadata_only (bool): Whether to fetch whole emails or metadata only.

    Returns:
        list of dict: List of fetched emails.
    """
    server = connect_to_imap()
    server.select_folder(folder)
    messages = server.search(['UNSEEN'])

    fetched_emails = []

    if not metadata_only:
        os.makedirs(folder, exist_ok=True)

    for msg_id in messages:
        if metadata_only:
            raw_message = server.fetch([msg_id], ['BODY.PEEK[HEADER]', 'FLAGS'])
            email_message = email.message_from_bytes(raw_message[msg_id][b'BODY[HEADER]'])
        else:
            raw_message = server.fetch([msg_id], ['BODY.PEEK[]', 'FLAGS'])
            email_message = email.message_from_bytes(raw_message[msg_id][b'BODY[]'])

        subject = decode_header(email_message['Subject'])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()

        from_ = decode_header(email_message['From'])[0][0]
        if isinstance(from_, bytes):
            from_ = from_.decode()

        if metadata_only:
            fetched_emails.append({"subject": subject, "from": from_})
        else:
            # Save the raw email to a file
            filename = f"{msg_id}.eml"
            filepath = os.path.join(folder, filename)
            with open(filepath, 'wb') as f:
                f.write(raw_message[msg_id][b'BODY[]'])
            fetched_emails.append({"subject": subject, "from": from_, "file": filepath})

        if mark_as_read:
            server.add_flags([msg_id], ['\\Seen'])
    server.logout()
    return fetched_emails


def list_folders(all=False):
    """
    Lists all folders with unread emails, and a count.

    Returns:
        list of tuple: List of (folder_name, unread_count) tuples.
    """
    server = connect_to_imap()
    try:
        folders = server.xlist()
    except:
        logger.info("server does not support xlist")
        folders = server.list_folders()
    folder_list = []

    for flags, delimiter, folder_name in folders:
        unread_count = server.folder_status(folder_name, ['UNSEEN'])[b'UNSEEN']
        folder_list.append((folder_name, unread_count))

    if not all:
        folder_list = [item for item in folder_list if item[1] > 0]

    server.logout()
    return folder_list


@argh.arg('-l', '--list', help='List all folders with unread email count', action='store_true')
@argh.arg('-a', '--all', help='When listing folders, include folders with no unread emails', action='store_true')
@argh.arg('-f', '--folder', help='IMAP folder to fetch emails from')
@argh.arg('-r', '--mark-as-read', help='Mark fetched emails as read', action='store_true')
@argh.arg('-m', '--metadata', help='Fetch only metadata (subject and from)', action='store_true')
def main(folder="INBOX", mark_as_read=False, list=False, all=False, metadata=False):
    """
    imap_fetch.py - A command-line tool to fetch unread emails from an IMAP server.

    This script fetches unread emails from the specified IMAP folder and saves them locally or prints metadata.

    Usage:
        export IMAP_HOST=imap.example.com
        export IMAP_USER=user@example.com
        export IMAP_PASSWORD=secret
        python3 imap_fetch.py [--folder FOLDER] [--mark-as-read] [--list] [-m|--metadata]
    """
    if list:
        folder_list = list_folders(all=all)
        for folder_name, unread_count in folder_list:
            print(f"{unread_count}\t{folder_name}")
    else:
        emails = fetch_emails(folder, mark_as_read, metadata)
        for email in emails:
            print(f"Subject: {email['subject']}")
            print(f"From: {email['from']}")
            if not metadata:
                print(f"Saved-To: {email['file']}")
            print()

if __name__ == '__main__':
    try:
        argh.dispatch_command(main)
    except Exception as e:
        logger.error(f"Error: %s %s", type(e).__name__, str(e))
        sys.exit(1)
