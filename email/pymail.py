#!/usr/bin/env python3-allemande

"""
Send emails with optional HTML content and attachments, reading body from stdin.
"""

import sys
import logging
import smtplib
from pathlib import Path
from email.message import EmailMessage
import argparse

__version__ = "0.1.1"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_message(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    sender: str,
    recipients: list[str],
    subject: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
) -> EmailMessage:
    """Create an email message with the given parameters."""
    msg = EmailMessage()
    msg.set_charset("utf-8")
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)

    return msg


def add_attachments(msg: EmailMessage, files: list[str]) -> None:
    """Add attachments to the email message."""
    for filepath in files:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Attachment not found: {filepath}")

        with open(path, "rb") as f:
            content = f.read()
            msg.add_attachment(
                content,
                maintype="application",
                subtype="octet-stream",
                filename=path.name,
            )
        logger.debug("Added attachment: %s", path.name)


def send_mail(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    sender: str,
    recipients: list[str],
    subject: str = "No subject",
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    attachments: list[str] | None = None,
    html: bool = False,
    host: str = "localhost",
    port: int = 25,
) -> None:
    """Send an email with content from stdin and optional attachments."""

    # Read email body from stdin
    body = sys.stdin.read()
    if not body:
        raise ValueError("Email body cannot be empty")

    # Create message
    msg = create_message(sender, recipients, subject, cc, bcc)

    # Set content type and body
    content_type = "html" if html else "plain"
    msg.set_content(body, subtype=content_type)

    # Add attachments if any
    if attachments:
        add_attachments(msg, attachments)

    if not recipients:
        return

    # Send email
    try:
        with smtplib.SMTP(host, port=port) as server:
            server.send_message(msg)
            logger.info("Email sent successfully")
    except Exception as e:
        logger.error("Failed to send email: %s", e)
        raise


def send_mail_cli() -> None:
    """Command-line interface for sending emails."""
    parser = argparse.ArgumentParser(description="Send an email with content from stdin")

    # Add arguments
    parser.add_argument("-f", "--from", dest="sender",
                    required=True, help="sender email address")
    parser.add_argument("-t", "--to", dest="recipients",
                    required=True, nargs="*", help="recipient email addresses")
    parser.add_argument("-s", "--subject", default="No subject",
                    help="email subject")
    parser.add_argument("-c", "--cc", nargs="*",
                    help="CC recipients")
    parser.add_argument("-b", "--bcc", nargs="*",
                    help="BCC recipients")
    parser.add_argument("-a", "--attach", dest="attachments", nargs="*",
                    help="files to attach")
    parser.add_argument("--html", action="store_true",
                    help="treat body as HTML")
    parser.add_argument("--host", default="localhost",
                    help="SMTP server hostname")
    parser.add_argument("--port", type=int, default=25,
                    help="SMTP server port")

    # Parse arguments
    args = parser.parse_args()

    # Call send_mail with parsed arguments
    try:
        send_mail(
            sender=args.sender,
            recipients=args.recipients,
            subject=args.subject,
            cc=args.cc,
            bcc=args.bcc,
            attachments=args.attachments,
            html=args.html,
            host=args.host,
            port=args.port
        )
    except Exception as e:  # pylint: disable=broad-except
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    send_mail_cli()
