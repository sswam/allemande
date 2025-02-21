#!/usr/bin/env python3

"""
Search Google using the Serper Dev API and return a list of results.
"""

import os
import sys
import logging
import json
import csv

import aiohttp

from ally import main  # type: ignore


SERPER_DEV_API_KEY = os.environ.get("SERPER_DEV_API_KEY")
TIMEOUT = 30


logger = logging.getLogger(__name__)


async def google_search(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-branches
    query: str,
    cli=False,
    timeout: int = TIMEOUT,
    num: int = 10,
    page: int | None = None,
    detailed: bool = False,
    safe: bool | None = None,
    location: str | None = None,
    country: str | None = None,
    language: str | None = None,
    time_filter: str | None = None,
    autocorrect: bool | None = None,
) -> list[dict]:
    """Search Google for 'query' using the Serper Dev API and return a list of num results.

    If detailed is True, the full JSON result from the API is returned.
    Otherwise, a list of dictionaries is returned with keys "title", "url", and "snippet" (from organic results).

    Optional parameters:
    timeout: Timeout in seconds, default is 30
    num: Number of results to request per page, default is 10. The maximum is 100, and 100 costs the same as 11
    page: The starting page
    detailed: Whether to return the full JSON response (True/False), defaults to False
    safe: Whether to enable SafeSearch (True/False)
    location: The location to use for the search
    country: Country code for the search
    language: Language code for the search
    time_filter: Time filter (h=hour, d=day, w=week, m=month, y=year)
    autocorrect: Whether to autocorrect the query
    """
    if not SERPER_DEV_API_KEY:
        raise ValueError("Google search requires SERPER_DEV_API_KEY")

    if num < 1:
        raise ValueError("num must be at least 1")
    if num > 100:
        raise ValueError("num cannot be more than 100")

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_DEV_API_KEY,
        "Content-Type": "application/json",
    }

    payload: dict[str, object] = {"q": query, "num": num}
    if page is not None:
        payload["page"] = page
    if safe is not None:
        payload["safe"] = "active" if safe else "off"
    if location is not None:
        payload["location"] = location
    if country is not None:
        payload["gl"] = country
    if language is not None:
        payload["hl"] = language
    if time_filter is not None:
        payload["tbs"] = f"qdr:{time_filter}"
    if autocorrect is not None and not autocorrect:
        payload["autocorrect"] = False

    logger.info("Searching with payload: %s", payload)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                raise ValueError(f"Error from API: {resp.status}")
            json_response = await resp.json()

    if detailed:
        if cli:
            print(json.dumps(json_response, indent=2))
        return json_response

    organic = json_response.get("organic", [])

    results = []

    for item in organic:
        title = item.get("title")
        link = item.get("link")
        snippet = item.get("snippet")
        if not (title and link):
            raise ValueError("Missing title or link in API response")
        result = {
            "title": title,
            "url": link,
            "snippet": snippet,
        }
        results.append(result)

    if cli:
        writer = csv.writer(sys.stdout, delimiter="\t")
        for result in results:
            writer.writerow([result["title"], result["url"], result["snippet"]])

    return results


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("query", help="search query")
    arg("--timeout", help="timeout in seconds")
    arg("-n", "--num", help="maximum number of results to return")
    arg("-p", "--page", help="starting page number")
    arg("-D", "--detailed", action="store_true", help="return full JSON response")
    arg("-s", "--safe", action="store_true", help="enable SafeSearch")
    arg("-l", "--location", help="location for search results")
    arg("-c", "--country", help="country code for search")
    arg("--language", help="language code for search")
    arg("-t", "--time-filter", help="time filter (h=hour, d=day, w=week, m=month, y=year)")
    arg("-A", "--no-autocorrect", action="store_false", dest="autocorrect", help="disable autocorrect")


if __name__ == "__main__":
    main.go(google_search, setup_args, cli=True, ally_output=False)
