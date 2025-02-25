#!/usr/bin/env python3-allemande

"""search: Search the web from the command line"""

import asyncio
import argparse
import csv
import html
import io
import json
import logging
import pprint
import re
import sys
import urllib
from typing import Callable

from bs4 import BeautifulSoup
import requests
import tabulate
from youtube_search import YoutubeSearch  # type: ignore

from google_images import google_images
from google_search import google_search
from selenium_get import selenium_get


logger = logging.getLogger(__name__)

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"

timeout = 30


def duckduckgo_search(
    query: str,
    num: int = 12,  # pylint: disable=unused-argument
    detailed: bool = False,  # pylint: disable=unused-argument
    safe: bool = False,
) -> list[dict[str, str]]:
    """Search DuckDuckGo for `query` and return a list of results"""
    url = "https://html.duckduckgo.com/html/"
    params = {
        "q": query,
        "kl": "us-en",
        "kp": 1 if safe else -2,
    }
    headers = {
        "User-Agent": user_agent,
    }
    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    search_results = []
    search_results2 = soup.find_all("h2", class_="result__title")

    for res in search_results2:
        res2 = {"title": res.a.text.strip(), "url": res.a["href"]}
        if res2 not in search_results:
            search_results.append(res2)

    return search_results


def uspto_tess_search(  # pylint: disable=too-many-locals
    query: str,
    num: int = 100,
    detailed: bool = False,  # pylint: disable=unused-argument
    safe: bool = False,  # pylint: disable=unused-argument
) -> list[dict[str, str]]:
    """Search USPTO TESS database for trademarks matching query."""
    url = "https://tmsearch.uspto.gov/bin/gate.exe"
    params = {
        "f": "toc",
        "state": "extr",
        "p_search": "searchss",
        "p_L": "50",
        "BackReference": "&p_plural=yes&p_s_PARA1=&p_tagrepl~:=PARA1$LD&expr=PARA1 AND PARA2&p_s_PARA2=",
        "p_s_PARA1": query,
        "p_operator": "AND",
        "p_s_PARA2": "",
        "p_tagrepl": "PARA1$COMB",
        "p_op_ALL": "AND",
        "a_default": "search",
        "a_search": "Submit Query",
    }
    headers = {"User-Agent": user_agent}

    search_results: list[dict[str, str]] = []
    response = None
    soup = None

    while len(search_results) < num:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        results = soup.find_all("tr", class_="tr-main")
        for res in results:
            serial_num = res.find("td", class_="wd").text.strip()
            mark = res.find("a", class_="trademark-title").text.strip()
            result = {"serial_number": serial_num, "mark": mark}
            if result not in search_results:
                search_results.append(result)

        next_page = soup.select_one("a:contains('NEXT LIST')")
        if not next_page:
            break
        href = next_page.get(
            "href"
        )  # FIXME lint error here: Item "NavigableString" of "Tag | NavigableString" has no attribute "get"  [union-attr]
        if not isinstance(href, str):
            break
        # Use the last occurrence so that even if the URL format changes we get something.
        params["page"] = href.split("page=")[-1]

    return search_results


def bing_search(
    query: str,
    num: int = 12,  # pylint: disable=unused-argument
    detailed: bool = False,  # pylint: disable=unused-argument
    safe: bool = False,
) -> list[dict[str, str]]:
    """Search Bing for `query` and return a list of results"""
    url = "https://www.bing.com/search"
    params = {
        "q": query,
    }
    if not safe:
        params["safeSearch"] = "off"
    headers = {
        "User-Agent": user_agent,
    }
    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    search_results: list[dict[str, str]] = []
    # Explicitly cast the result list to avoid type issues.
    results_list = list(soup.find_all("li", class_="b_algo"))
    search_results2 = [{"title": result.find("h2").text.strip(), "url": result.find("a").get("href")} for result in results_list]
    search_results2 = [result for result in search_results2 if result["url"] is not None]

    for res in search_results2:
        if res not in search_results:
            search_results.append(res)

    return search_results


def youtube_search(query: str, num: int = 12, detailed: bool = False, safe: bool = False) -> list[dict[str, str]]:
    """Search YouTube for `query` and return a list of results"""
    if safe:
        logger.warning("Safe search not implemented for YouTube")
    search_results2 = YoutubeSearch(query, max_results=num).to_dict()

    for result in search_results2:
        result["url"] = "https://www.youtube.com" + result["url_suffix"]

    search_results: list[dict[str, str]] = []

    for res in search_results2:
        # remove junk from thumbnail URL
        if "thumbnails" in res and len(res["thumbnails"]) > 0:
            res["thumbnail"] = re.sub(r"\?.*", "", res["thumbnails"][0])

        # remove junk from the main URL
        if re.match(r"https?://www.youtube.com/watch\?v=", res["url"]):
            res["url"] = re.sub(r"&.*", "", res["url"])

        if res not in search_results:
            search_results.append(res)

    if detailed:
        return search_results

    return [
        {
            "title": result["title"],
            "url": result["url"],
            "thumbnail": result["thumbnail"],
            "channel": result["channel"],
            "duration": result["duration"],
        }
        for result in search_results
    ]


def google_maps_image_search(
    query: str, num: int = 12, detailed: bool = False, safe: bool = False  # pylint: disable=unused-argument
) -> list[dict[str, str]]:
    """Search Google Maps for images matching query."""
    base_url = "https://www.google.com/maps"
    search_url = base_url + "/search/"

    params = {
        "q": query,
    }

    # create a string io object to store the content of the page
    ostream = io.StringIO()
    selenium_get(
        ostream,
        search_url,
        params=params,  # type: ignore[arg-type]
        time_limit=timeout,
        scroll_limit=None,
        scroll_wait=1,
        retry_each_scroll=3,
        script=None,
        exe="",  # provided empty string instead of None
        script_wait=1,
        retry_script=3,
        facebook=False,
    )
    content = ostream.getvalue()
    ostream.close()

    if not content:
        return []

    soup = BeautifulSoup(content, "html.parser")

    search_results: list[dict[str, str]] = []
    image_tags = soup.find_all("img", class_="tactile-search-thumbnail-raster")

    for img_tag in image_tags:
        img_src = img_tag.get("src")
        if img_src:
            search_results.append({"image_url": img_src})

    return search_results


def pornhub_search(  # pylint: disable=too-many-locals
    query: str,
    num: int = 10,  # pylint: disable=unused-argument
    detailed: bool = False,  # pylint: disable=unused-argument
    safe: bool = False,  # pylint: disable=unused-argument
    ) -> list[dict[str, str]]:
    """Search PornHub for videos matching query."""
    site = "https://www.pornhub.com"
    url = site + "/video/search"

    params = {
        "search": query,
    }

    headers = {
        "User-Agent": user_agent,
    }
    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    container = soup.find("ul", id="videoSearchResult")
    if not container or not hasattr(container, "find_all"):
        return []

    a_tags = container.find_all("a", class_="linkVideoThumb")

    search_results: list[dict[str, str]] = []

    for a_tag in a_tags:
        duration_element = a_tag.find("var", class_="duration")
        duration = duration_element.text if duration_element else ""
        search_results.append({
            "title": a_tag.get("title"),
            "url": "https://pornhub.com" + a_tag.get("href"),
            "thumbnail": a_tag.find("img")["src"],
            "duration": duration,
        })

    return search_results


engines: dict[str, Callable] = {
    "Google": google_search,
    "GoogleImages": google_images,
    # 	'DuckDuckGo': duckduckgo_search,
    # 	'Bing': bing_search,
    "YouTube": youtube_search,
    # 	'GoogleMapsImages': google_maps_image_search,
    "PornHub": pornhub_search,
    #    "TESS": uspto_tess_search,
}

agents: dict[str, Callable] = {
    "Goog": google_search,
    "Gimg": google_images,
    # 	'DuckDuckGo': duckduckgo_search,
    # 	'Bing': bing_search,
    "UTube": youtube_search,
    "Pr0nto": pornhub_search,
    # 	'Guma': google_maps_image_search,
    # 	'Tessa': uspto_tess_search,
}

engine_caps = {
    "goog": "Google",
    "gimg": "GoogleImages",
    "utube": "YouTube",
    "pr0nto": "PornHub",
    #    "guma": "GoogleMapsImages",
    "google": "Google",
    "googleimages": "GoogleImages",
    "youtube": "YouTube",
    "pornhub": "PornHub",
    #    "googlemapsimages": "GoogleMapsImages",
    #    "tess": "TESS",
    #    "tessa": "TESS",
}


def esc(s: str) -> str:
    """Escape special characters in `s` for HTML."""
    s = html.escape(s)
    s = s.replace("|", "&#124;")
    s = s.replace("\n", "&#10;")
    return s


def format_video_result_markdown(item: dict[str, str], engine: str) -> dict[str, str]:
    """Format video search results for display."""
    video_id = None
    params_parsed = urllib.parse.parse_qs(urllib.parse.urlparse(item["url"]).query)
    video_id = params_parsed.get("v", [None])[0]
    if not video_id:
        video_id = params_parsed.get("viewkey", [None])[0]
    if not video_id:
        # Try shorts URL format
        # https://www.youtube.com/shorts/pbU5lUon9AU
        if re.match(r"^/shorts/", urllib.parse.urlparse(item["url"]).path):
            video_id = urllib.parse.urlparse(item["url"]).path.split("/")[-1]
    if not video_id:
        logger.warning("Could not parse YouTube video ID from URL %s", item["url"])
    if video_id:
        thumb = item["thumbnail"]
        video = (
            f"""<div class="embed" data-site="{engine.lower()}" data-videoid="{video_id}">"""
            + thumb
            + f"""<br><div class="caption">{item['page']}</div></div>"""
        )
        item["video"] = video
        del item["thumbnail"]
        del item["page"]
    return item


def format_image_result_markdown(item: dict[str, str], engine: str) -> dict[str, str]:
    """Format image search results for display."""
    thumb = item["thumbnail"]
    image_url = item["image_url"]
    image = (
        f"""<div class="image" data-site="{engine.lower()}" data-image="{image_url}">"""
        + thumb
        + f"""<br><div class="caption">{item['page']}</div></div>"""
    )
    item["image"] = image
    del item["thumbnail"]
    del item["page"]
    return item


def format_search_result_markdown(i: int, item: dict[str, str], engine: str) -> dict[str, str]:
    """Format search result for display."""
    item["#"] = str(i)
    i += 1
    url_esc = esc(item["url"])
    title = item["title"]
    if engine == "YouTube":
        title = f"{title} - {item['channel']} - {item['duration']}"
    elif engine == "PornHub":
        title = f"{title} - {item['duration']}"
    item["title"] = title_esc = esc(title)
    item["page"] = f"""<a href="{url_esc}">{title_esc}</a>"""
    if engine not in ("YouTube", "PornHub"):
        item["site"] = urllib.parse.urlparse(item["url"]).netloc
    if "thumbnail" in item:
        # convert to markdown image
        if "thumb_width" in item and "thumb_height" in item:
            width_height = f" width={item['thumb_width']} height={item['thumb_height']}"
        else:
            width_height = ""
        image = f"""<img class="thumb" src="{esc(item['thumbnail'])}" alt="{title_esc}"{width_height}>"""
        if "image_url" in item:
            image_esc = esc(item["image_url"])
            image = f"""<a href="{image_esc}">{image}</a>"""
        item["thumbnail"] = image
    if engine in ("YouTube", "PornHub"):
        item = format_video_result_markdown(item, engine)
    elif engine in ("GoogleImages", "GoogleMapsImages"):
        item = format_image_result_markdown(item, engine)
    for key in "url", "title", "width", "height", "thumb_width", "thumb_height":
        if key in item:
            del item[key]

    # reorder the keys
    item = (
        {
            "#": item["#"],
        }
        | ({"page": item["page"]} if "page" in item else {})
        | ({"site": item["site"]} if "site" in item else {})
        | item
    )
    return item


def list_to_markdown_table(items: list[dict[str, str]], engine: str) -> str:  # pylint: disable=too-many-branches, too-many-locals
    """Convert search results to markdown table format."""
    engine = engine_caps.get(engine.lower(), engine)

    items = [format_search_result_markdown(i, item, engine) for i, item in enumerate(items, 1)]

    logger.warning("items: %s", json.dumps(items, indent=4))

    # check all items have video
    if engine in ("YouTube", "PornHub") and all("video" in item for item in items):
        return "<div>" + ("\n".join([item["video"] for item in items])) + "</div>"

    if engine in ("GoogleImages", "GoogleMapsImages"):
        return "<div>" + ("\n".join([item["image"] for item in items])) + "</div>"

    return tabulate.tabulate(items, tablefmt="pipe", headers="keys")  # type: ignore[arg-type]


# output formatters ----------------------------------------------------------


def format_csv(obj: list[dict[str, str]], delimiter=",", header: bool = False) -> str:
    """Format `obj` as CSV"""
    if not obj:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=obj[0].keys(), delimiter=delimiter, dialect="unix", quoting=csv.QUOTE_MINIMAL)
    if header:
        writer.writeheader()
    writer.writerows(obj)
    return output.getvalue()


def format_tsv(obj: list[dict[str, str]], header: bool = False) -> str:
    """Format `obj` as TSV"""
    return format_csv(obj, delimiter="\t", header=header)


def format_json(obj, header: bool = False) -> str:  # pylint: disable=unused-argument
    """Format `obj` as JSON"""
    return json.dumps(obj, indent=4)


def format_python(obj, header: bool = False) -> str:  # pylint: disable=unused-argument
    """Format `obj` as Python code"""
    return pprint.pformat(obj, indent=4)


def format_tabulate(obj: list[dict[str, str]], header: bool = False) -> str:
    """Format `obj` as a table"""
    if not obj:
        return ""
    kwargs = {"headers": "keys"} if header else {}
    return tabulate.tabulate(obj, **kwargs)  # type: ignore[arg-type]


formatters: dict[str, Callable] = {
    "tsv": format_tsv,
    "csv": format_csv,
    "json": format_json,
    "py": format_python,
    "txt": format_tabulate,
}


def dict_first(d: dict) -> str:
    """Return the first key in a dictionary"""
    return next(iter(d))


async def search(
    *queries: str,
    engine: str | None = None,
    markdown: bool = False,
    num: int = 10,
    limit: bool = False,
    safe: bool = False,
    fmt: str = "table",
    header: bool = False,
    ostream: io.TextIOWrapper | None = None,
    details: bool = False,
):  # pylint: disable=too-many-arguments, too-many-locals, too-many-branches
    """Search for `query` using `engine` and return a list of results"""
    if not engine:
        raise ValueError("No search engine specified")

    all_results = []
    lc_keys_to_keys = {k.lower(): k for k in list(engines.keys()) + list(agents.keys())}

    key = lc_keys_to_keys[engine.lower()]
    eng = engines.get(key, agents.get(key))

    if eng is None:
        raise ValueError(f"Unknown search engine: {engine}")

    for query in queries:
        # check if it's async
        if asyncio.iscoroutinefunction(eng):
            results = await eng(query, num=num, safe=safe, detailed=details)
        else:
            # run in a thread
            results = await asyncio.to_thread(eng, query, num=num, safe=safe, detailed=details)

        if limit:
            results = results[:num]

        if ostream:
            if markdown:
                formatted_results = list_to_markdown_table(results, engine)
            else:
                formatter = formatters[fmt]
                formatted_results = formatter(results, header=header).rstrip()

            print(formatted_results, file=ostream)
        else:
            all_results.append(results)

    if not ostream:
        if markdown:
            rows = []
            for res in all_results:
                formatted_results = list_to_markdown_table(res, engine)
                rows.append(formatted_results)
            return "\n".join(rows)
        return all_results


def search_sync(
    *queries: str,
    engine: str | None = None,
    markdown: bool = False,
    num: int = 10,
    limit: bool = False,
    safe: bool = False,
    fmt: str = "table",
    header: bool = False,
    ostream: io.TextIOWrapper | None = None,
    details: bool = False,
):  # pylint: disable=too-many-arguments
    """Search for `query` using `engine` and return a list of results"""
    return asyncio.run(
        search(
            *queries,
            engine=engine,
            markdown=markdown,
            limit=limit,
            num=num,
            safe=safe,
            fmt=fmt,
            header=header,
            ostream=ostream,
            details=details,
        )
    )


def main():
    """Parse command line arguments and run search"""
    parser = argparse.ArgumentParser(description="Search `query` using `engine` and return a list of results")
    parser.add_argument(
        "-e", "--engine", help="Search engine to use", default=dict_first(engines), choices=list(map(str.lower, engines.keys()))
    )
    parser.add_argument("-f", "--format", help="Output formatter", default="tsv", choices=formatters.keys(), dest="fmt")
    parser.add_argument("-n", "--num", help="Maximum number of results to return", type=int, default=10)
    parser.add_argument("-s", "--safe", help="Safe search", action="store_true")
    parser.add_argument("-l", "--limit", help="Limit to specified max results", type=int)
    parser.add_argument("-H", "--header", help="Show the table header", action="store_true")
    parser.add_argument("--markdown", help="Output as Markdown", action="store_true")
    parser.add_argument("--out", help="Output file", type=argparse.FileType("w"), default=sys.stdout)
    parser.add_argument("queries", nargs="*", help="Search queries")
    parser.add_argument("-D", "--details", help="Show detailed results", action="store_true")

    parser.set_defaults(log_level=logging.WARNING)
    logging_group = parser.add_mutually_exclusive_group()
    logging_group.add_argument(
        "-d", "--debug", dest="log_level", action="store_const", const=logging.DEBUG, help="show debug messages"
    )
    logging_group.add_argument(
        "-v", "--verbose", dest="log_level", action="store_const", const=logging.INFO, help="show verbose messages"
    )
    logging_group.add_argument(
        "-q", "--quiet", dest="log_level", action="store_const", const=logging.ERROR, help="show only errors"
    )
    logging_group.add_argument(
        "-Q", "--silent", dest="log_level", action="store_const", const=logging.CRITICAL, help="show nothing"
    )
    logging_group.add_argument("--log", default=None, help="log file")

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, filename=args.log, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    search_sync(
        *args.queries,
        engine=args.engine,
        markdown=args.markdown,
        limit=args.limit,
        num=args.num,
        safe=args.safe,
        fmt=args.fmt,
        header=args.header,
        ostream=args.out,
        details=args.details,
    )


if __name__ == "__main__":
    main()
