#!/usr/bin/env python3-allemande

"""
Makes HTTP GET/POST/PUT/HEAD requests with bearer token authentication from environment.
"""

import os
import sys
from typing import Any

import requests

from ally import main, logs  # type: ignore

__version__ = "0.1.2"

TIMEOUT = 600

logger = logs.get_logger()


def make_request(method: str, url: str, authvar: str | None = None, data: str | None = None) -> str:
    """Make an HTTP request using the specified method, URL, and optional bearer token and data."""
    headers: dict[str, str] = {}

    if authvar:
        api_key = os.environ[authvar]
        headers["Authorization"] = f"Bearer {api_key}"

    request_args: dict[str, Any] = {
        "headers": headers,
        "timeout": TIMEOUT
    }
    if data:
        request_args["data"] = data

    response = requests.request(method, url, **request_args)
    response.raise_for_status()

    if method == "HEAD":
        return str(response.headers)
    return response.text


def request(method: str, url: str, authvar: str | None = None):
    """Make an HTTP request, CLI entry point."""
    if method not in ("GET", "POST", "PUT", "HEAD"):
        raise ValueError(f"Invalid method: {method}")
    if method in ("POST", "PUT"):
        data = sys.stdin.read()
    else:
        data = None
    text = make_request(method, url, authvar, data)
    print(text, end="")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("method", help="HTTP method to use")
    arg("url", help="URL to request")
    arg("-a", "--authvar", help="Environment variable containing the bearer token")


if __name__ == "__main__":
    main.go(request, setup_args)
