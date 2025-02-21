#!/usr/bin/env python3

"""
Search Google Images using the Serper Dev API and return a list of results.
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


async def google_images(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-branches, too-many-statements
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
    size: str | None = None,
    larger: str | None = None,
    color: str | None = None,
    type_filter: str | None = None,
    rights: str | None = None,
) -> list[dict]:
    """Search Google Images for 'query' using the Serper Dev API and return a list of results.

    If detailed is True, the full JSON result from the API is returned.
    Otherwise, a list of dictionaries is returned with basic image information.
    
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
    size: Image size filter (i=icon, m=medium, l=large)
    larger: Larger than size filter (e.g., qsvga, vga, svga, xga, 2mp, 4mp, 6mp, 8mp, 10mp, 12mp, 15mp, 20mp, 40mp, 70mp)
    color: Color filter (color, gray, or specific color name)
    type_filter: Type of image (face, photo, clipart, lineart)
    rights: Usage rights filter (cl=Creative Commons, ol=Commercial)
    """
    if not SERPER_DEV_API_KEY:
        raise ValueError("Google search requires SERPER_DEV_API_KEY")

    if num < 1:
        raise ValueError("num must be at least 1")
    if num > 100:
        raise ValueError("num cannot be more than 100")

    url = "https://google.serper.dev/images"
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

    # Construct tbs parameter
    tbs_parts = []
    if larger:
        size = f"lt,islt:{larger}"
    if size:
        tbs_parts.append(f"isz:{size}")
    if color:
        if color in ["color", "gray"]:
            tbs_parts.append(f"ic:{color}")
        else:
            tbs_parts.append(f"ic:specific,isc:{color}")
    if type_filter:
        tbs_parts.append(f"itp:{type_filter}")
    if rights:
        tbs_parts.append(f"sur:{rights}")
    if time_filter:
        tbs_parts.append(f"qdr:{time_filter}")

    if tbs_parts:
        payload["tbs"] = ",".join(tbs_parts)

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

    images = json_response.get("images", [])

    results = []

    for item in images:
        title = item.get("title")
        link = item.get("link")
        if not (title and link):
            raise ValueError("Missing title or link in API response")
        result = {
            "title": title,
            "url": link,
            "image": item.get("imageUrl"),
            "thumbnail": item.get("thumbnailUrl"),
            "width": item.get("imageWidth"),
            "height": item.get("imageHeight"),
            "thumb_width": item.get("thumbnailWidth"),
            "thumb_height": item.get("thumbnailHeight"),
        }
        results.append(result)

    if cli:
        writer = csv.writer(sys.stdout, delimiter="\t")
        # writer.writerow(["Title", "URL", "Image URL", "Thumbnail URL", "Width", "Height"])
        for result in results:
            writer.writerow([
                result["title"], result["url"], result["image"],
                result["thumbnail"], result["width"], result["height"], result["thumb_width"], result["thumb_height"]
            ])

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
    arg("--size", help="image size (i=icon, m=medium, l=large)")
    arg("--color", help="color filter (color, gray, or color name)")
    arg("--type", dest="type_filter", help="type filter (face, photo, clipart, lineart)")
    arg("--rights", help="usage rights filter (cl=Creative Commons, ol=Commercial)")


if __name__ == "__main__":
    main.go(google_images, setup_args, cli=True, ally_output=False)
