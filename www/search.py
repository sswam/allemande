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

from bs4 import BeautifulSoup
import requests
import tabulate
from youtube_search import YoutubeSearch

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
    safe: str = "off",
) -> list[dict[str, str]]:
    """Search DuckDuckGo for `query` and return a list of results"""
    url = "https://html.duckduckgo.com/html/"
    kp = {
        "off": -2,
        "moderate": -1,
        "strict": 1,
        "on": 1,
    }
    params = {
        "q": query,
        "kl": "us-en",
        "kp": kp[safe],
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
    safe: str = "off",  # pylint: disable=unused-argument
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

    search_results = []
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

        next_page = soup.find("a", string="NEXT LIST")
        if not next_page:
            break

        params["f"] = "toc"
        params["state"] = "GETPAGE"
        params["page"] = next_page["href"].split("page=")[1]

    return search_results


def bing_search(
    query: str,
    num: int = 12,  # pylint: disable=unused-argument
    detailed: bool = False,  # pylint: disable=unused-argument
    safe: str = "off",
) -> list[dict[str, str]]:
    """Search Bing for `query` and return a list of results"""
    url = "https://www.bing.com/search"
    params = {
        "q": query,
        "safeSearch": safe,
    }
    headers = {
        "User-Agent": user_agent,
    }
    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    search_results = []
    search_results2 = soup.find_all("li", class_="b_algo")
    search_results2 = [{"title": result.find("h2").text.strip(), "url": result.find("a").get("href")} for result in search_results2]
    search_results2 = [result for result in search_results2 if result["url"] is not None]

    for res in search_results2:
        if res not in search_results:
            search_results.append(res)

    return search_results


def youtube_search(query: str, num: int = 12, detailed: bool = False, safe: str = "off") -> list[dict[str, str]]:
    """Search YouTube for `query` and return a list of results"""
    if safe != "off":
        logger.warning("Safe search not implemented for YouTube")
    search_results2 = YoutubeSearch(query, max_results=num).to_dict()

    for result in search_results2:
        result["url"] = "https://www.youtube.com" + result["url_suffix"]

    search_results = []

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
    query: str,
    num: int = 12,  # pylint: disable=unused-argument
    safe: str = "off"  # pylint: disable=unused-argument
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
        params=params,
        time_limit=timeout,
        scroll_limit=None,
        scroll_wait=1,
        retry_each_scroll=3,
        script=None,
        exe=None,
        script_wait=1,
        retry_script=3,
        facebook=False,
    )
    content = ostream.getvalue()
    ostream.close()

    if not content:
        return []

    soup = BeautifulSoup(content, "html.parser")

    image_results = []
    image_tags = soup.find_all("img", class_="tactile-search-thumbnail-raster")

    for img_tag in image_tags:
        img_src = img_tag.get("src")
        if img_src:
            image_results.append({"image_url": img_src})

    return image_results


def pornhub_search(
    query: str,
    num: int = 10,  # pylint: disable=unused-argument
    detailed: bool = False,  # pylint: disable=unused-argument
    safe: str = "off"  # pylint: disable=unused-argument
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

    search_results = container.find_all("a", class_="linkVideoThumb")

    return [
        {"title": result.text, "url": site + result["href"], "thumbnail": result.find("img")["src"]}
        for result in search_results
        if not result["href"].startswith("javascript:")
    ]


engines = {
    "Google": google_search,
    "GoogleImages": google_images,
    # 	'DuckDuckGo': duckduckgo_search,
    # 	'Bing': bing_search,
    "YouTube": youtube_search,
    # 	'GoogleMapsImages': google_maps_image_search,
    "PornHub": pornhub_search,
    #    "TESS": uspto_tess_search,
}


agents = {
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


def list_to_markdown_table(items: list[dict[str, str]], engine: str) -> str:  # pylint: disable=too-many-branches, too-many-locals
    """Convert search results to markdown table format."""
    engine = engine_caps.get(engine.lower(), engine)
    i = 1
    for item_in in items:
        item = {"#": i}
        item.update(item_in)
        i += 1
        url_enc = esc(item["url"])
        title = item["title"]
        if engine == "YouTube":
            title = f"{title} - {item['channel']} - {item['duration']}"
        title_enc = esc(title)
        item["page"] = f"""<a href="{url_enc}">{title_enc}</a>"""
        if engine not in ("YouTube", "PornHub"):
            item["site"] = urllib.parse.urlparse(item["url"]).netloc
        if "thumbnail" in item:
            # convert to markdown image
            if "thumb_width" in item and "thumb_height" in item:
                width_height = f" width={item['thumb_width']} height={item['thumb_height']}"
            else:
                width_height = ""
            image = f"""<img class="thumb" src="{esc(item['thumbnail'])}" alt="{title_enc}"{width_height}>"""
            if "image" in item:
                image_enc = esc(item["image"])
                image = f"""<a href="{image_enc}">{image}</a>"""
            item["thumbnail"] = image
        if engine in ("YouTube", "PornHub"):
            video_id = None
            params = urllib.parse.parse_qs(urllib.parse.urlparse(item["url"]).query)
            video_id = params.get("v", [None])[0]
            if not video_id:
                video_id = params.get("viewkey", [None])[0]
            if not video_id:
                # Try shorts URL format
                # https://www.youtube.com/shorts/pbU5lUon9AU
                if re.match(r"^/shorts/", urllib.parse.urlparse(item["url"]).path):
                    video_id = urllib.parse.urlparse(item["url"]).path.split("/")[-1]
            if not video_id:
                logger.warning("Could not parse YouTube video ID from URL %s", item["url"])
            if video_id:
                img = item["thumbnail"]
                video = (
                    f"""<div class="embed" data-site="{engine.lower()}" data-videoid="{video_id}">"""
                    + img
                    + f"""<br><div class="caption">{item['page']}</div></div>"""
                )
                item["video"] = video
                del item["thumbnail"]
                del item["page"]
        for key in "url", "title", "width", "height", "thumb_width", "thumb_height":
            if key in item:
                del item[key]

    # check all items have video
    if engine in ("YouTube", "PornHub") and all("video" in item for item in items):
        return "<br><div>" + ("\n".join([item["video"] for item in items])) + "</div>"
    return tabulate.tabulate(items, tablefmt="pipe", headers="keys")


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


def format_json(
    obj,
    header: bool = False  # pylint: disable=unused-argument
) -> str:
    """Format `obj` as JSON"""
    return json.dumps(obj, indent=4)


def format_python(
    obj,
    header: bool = False  # pylint: disable=unused-argument
) -> str:
    """Format `obj` as Python code"""
    return pprint.pformat(obj, indent=4)


def format_tabulate(obj: list[dict[str, str]], header: bool = False) -> str:
    """Format `obj` as a table"""
    if not obj:
        return ""
    kwargs = {"headers": "keys"} if header else {}
    return tabulate.tabulate(obj, **kwargs)


formatters = {
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
    engine: str = None,
    markdown: bool = False,
    limit: int = None,
    num: int = 10,
    safe: str = "off",
    fmt: str = "table",
    header: bool = False,
    out: str = None,
    details: bool = False,
):  # pylint: disable=too-many-arguments, too-many-locals, too-many-branches
    """Search for `query` using `engine` and return a list of results"""
    all_results = []
    lc_keys_to_keys = {k.lower(): k for k in list(engines.keys()) + list(agents.keys())}

    if engine is None:
        engine = dict_first(engines)

    key = lc_keys_to_keys[engine.lower()]
    eng = engines.get(key, agents.get(key))

    for query in queries:
        # check if it's async
        if asyncio.iscoroutinefunction(eng):
            results = await eng(query, num=num, safe=safe, detailed=details)
        else:
            # run in a thread
            results = await asyncio.to_thread(eng, query, num=num, safe=safe, detailed=details)

        if limit:
            results = results[:limit]

        if out:
            if markdown:
                formatted_results = list_to_markdown_table(results, engine)
            else:
                formatter = formatters[fmt]
                formatted_results = formatter(results, header=header).rstrip()

            print(formatted_results, file=out)
        else:
            all_results.append(results)

    if not out:
        if markdown:
            out = []
            for res in all_results:
                formatted_results = list_to_markdown_table(res, engine)
                out.append(formatted_results)
            return "\n".join(out)
        return all_results


def search_sync(
    *queries: str,
    engine: str = None,
    markdown: bool = False,
    limit: int = None,
    num: int = 10,
    safe: str = "off",
    fmt: str = "table",
    header: bool = False,
    out: str = None,
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
            out=out,
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
    parser.add_argument("-s", "--safe", help="Safe search", default="off", choices=["off", "moderate", "strict"])
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
        format=args.format,
        header=args.header,
        out=args.out,
        details=args.details,
    )


if __name__ == "__main__":
    main()
