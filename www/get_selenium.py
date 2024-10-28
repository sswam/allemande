#!/usr/bin/env python3

"""
Fetches a web page using Selenium, runs the JavaScript,
and writes the output to stdout or a file.
"""

import sys
import time
from typing import TextIO
from pathlib import Path
from urllib.parse import urlencode

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

from ally import main, logs

__version__ = "0.3.4"

logger = logs.get_logger()

user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/58.0.3029.110 Safari/537.3"
)


def scroll_page(
    wd,
    selector: str | None = None,
    time_limit=30,
    scroll_limit=100000,
    scroll_wait=1,
    retry_each_scroll=3,
):
    """Scroll a specific element or the whole page."""
    # pylint: disable=too-many-arguments
    start_time = time.time()

    if selector:
        # Get the element and its maximum scrollTop
        element_info_script = f"""
            const el = document.querySelector('{selector}');
            if (el) {{
                return {{
                    scrollHeight: el.scrollHeight,
                    clientHeight: el.clientHeight,
                    scrollTop: el.scrollTop
                }};
            }} else {{
                return null;
            }}
        """
        element_info = wd.execute_script(element_info_script)
        if element_info is None:
            logger.warning("Element with selector '%s' not found", selector)
            return
        max_scroll_top = element_info['scrollHeight'] - element_info['clientHeight']
        scrolled = element_info['scrollTop']
        logger.info("Starting scroll for element '%s', max scrollTop: %s", selector, max_scroll_top)
        scroll_script = f"""
            const el = document.querySelector('{selector}');
            el.scrollBy(0, window.innerHeight);
            return el.scrollTop;
        """
    else:
        max_scroll_top = wd.execute_script("return document.body.scrollHeight - window.innerHeight")
        scrolled = wd.execute_script("return window.pageYOffset")
        logger.info("Starting scroll, max scrollTop: %s", max_scroll_top)
        scroll_script = "window.scrollBy(0, window.innerHeight); return window.pageYOffset;"

    while True:
        scrolled_pre = scrolled
        for _ in range(retry_each_scroll):
            if not selector:
                ActionChains(wd).key_down(Keys.PAGE_DOWN).perform()
            scrolled = wd.execute_script(scroll_script)
            time.sleep(scroll_wait)
            if scroll_limit and scrolled >= scroll_limit:
                logger.info("Reached scroll limit: %d", scroll_limit)
                return
            if scrolled >= max_scroll_top:
                logger.info("Reached bottom, scrolled: %d", scrolled)
                return
        if scrolled == scrolled_pre:
            logger.info("No more scrolling possible, scrolled: %d", scrolled)
            return
        elapsed_time = time.time() - start_time
        if elapsed_time > time_limit:
            logger.warning("Reached time limit: %d seconds", time_limit)
            return


def get_selenium(
    wd: webdriver.Chrome,
    url: str,
    sleep: int = 0,
    ostream: TextIO = sys.stdout,
    time_limit: int = 30,
    scroll_limit: int | None = None,
    scroll_wait: float = 1,
    retry_each_scroll: int = 3,
    exe: str | None = None,
    script_wait: float = 1,
    retry_script: int = 3,
    scroll_selector: str | None = None,
) -> None:
    """Fetch a web page using Selenium and write the output to the specified stream."""
    # pylint: disable=too-many-arguments
    logger.info("Loading page: %s", url)
    wd.get(url)
    logger.info("Page loaded successfully")

    if sleep:
        logger.debug("Sleeping for %d seconds", sleep)
        time.sleep(sleep)

    if exe:
        logger.info("Executing script")
        for attempt in range(retry_script):
            logger.debug("Script execution attempt %d", attempt + 1)
            status = wd.execute_script(exe)
            if script_wait:
                time.sleep(script_wait)
            if not status:
                break
            logger.warning("Script returned status: %s", status)
        else:
            logger.warning("Script failed after %d retries", retry_script)

    if scroll_limit:
        scroll_page(wd, scroll_selector, time_limit, scroll_limit, scroll_wait, retry_each_scroll)

    print(wd.page_source, file=ostream)


def selenium_get(
    ostream: TextIO,
    url: str,
    sleep: int = 0,
    images: bool = False,
    screenshot: str | None = None,
    time_limit: int = 30,
    scroll_limit: int | None = None,
    scroll_wait: float = 1,
    retry_each_scroll: int = 3,
    script: str | None = None,
    exe: str | None = None,
    script_wait: float = 1,
    retry_script: int = 3,
    facebook: bool = False,
    params: list[str] | None = None,
    scroll_selector: str | None = None,
) -> None:
    """
    Fetch a web page, run the JavaScript, and write the output to stdout or a file.
    """
    # pylint: disable=too-many-arguments,too-many-locals
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument(f"user-agent={user_agent}")

    if not images:
        opts.add_argument("--blink-settings=imagesEnabled=false")

    program = Path(sys.argv[0])
    prog_dir = program.parent

    exe_text = exe or ""

    if script:
        exe_text += "\n" + Path(script).read_text(encoding="utf-8") + "\n"

    if facebook:
        exe_text += "\n" + (prog_dir / "facebook_scroller.js").read_text(encoding="utf-8") + "\n"

    if params:
        url += "?" + urlencode(dict(param.split("=") for param in params))

    with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts) as wd:
        get_selenium(
            wd,
            url,
            sleep=sleep,
            ostream=ostream,
            time_limit=time_limit,
            scroll_limit=scroll_limit,
            scroll_wait=scroll_wait,
            retry_each_scroll=retry_each_scroll,
            exe=exe_text,
            script_wait=script_wait,
            retry_script=retry_script,
            scroll_selector=scroll_selector,
        )

        if screenshot:
            wd.save_screenshot(screenshot)


def setup_args(arg):
    """Set up command-line arguments."""
    arg("url", help="URL of page to load")
    arg("-s", "--sleep", help="seconds to sleep before dumping DOM as HTML")
    arg("-i", "--images", help="enable images", action="store_true")
    arg("-S", "--screenshot", help="save screenshot to file")
    arg("-t", "--time-limit", help="Maximum time for scrolling, in seconds")
    arg("-l", "--scroll-limit", help="Maximum number of pixels to scroll down")
    arg("-w", "--scroll-wait", help="Time to wait after each scroll, in seconds")
    arg("-r", "--retry-each-scroll", help="Number of times to retry each scroll")
    arg("-c", "--script", help="JavaScript file to run before scrolling")
    arg("-e", "--exe", help="JavaScript to run before scrolling")
    arg("-T", "--script-wait", help="Time to wait after running script, in seconds")
    arg("-R", "--retry-script", help="Number of times to retry running script")
    arg("-f", "--facebook", help="Download from Facebook", action="store_true")
    arg("-p", "--params", help="URL parameters", nargs="+")
    arg("-E", "--scroll-selector", help="CSS selector for element to scroll")


if __name__ == "__main__":
    main.go(selenium_get, setup_args)
