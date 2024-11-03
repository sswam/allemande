#!/usr/bin/env python3

"""
Fetches a web page using Selenium, runs the JavaScript,
and writes the output to stdout or a file.
"""

import sys
import time
import json
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

__version__ = "0.3.6"

logger = logs.get_logger()

user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/58.0.3029.110 Safari/537.3"
)

DEFAULT_COOKIE_DIR = Path.home() / ".local/share/selenium"
DEFAULT_COOKIE_FILE = DEFAULT_COOKIE_DIR / "cookies.json"
CLOSE_WINDOW_POLL_INTERVAL = 0.1


def set_cookies(wd, cookies):
    """Set cookies in the browser session before visiting the site."""
    # Enable network tracking for CDP
    wd.execute_cdp_cmd("Network.enable", {})

    # Set each cookie using CDP
    for cookie in cookies:
        # Handle expiry/expires key conversion
        if "expiry" in cookie:
            cookie["expires"] = cookie["expiry"]
            del cookie["expiry"]
        wd.execute_cdp_cmd("Network.setCookie", cookie)

    # Disable network tracking
    wd.execute_cdp_cmd("Network.disable", {})


def get_cookies(driver: webdriver.Chrome) -> list[dict[str, str]]:
    """Get cookies from the browser session after visiting the site."""
    cookies = driver.execute_cdp_cmd("Network.getAllCookies", {})["cookies"]
    return cookies


def save_cookies(
    cookie_file: Path | None = None, cookies: list[dict[str, str]] | None = None
) -> None:
    """Save cookies from the browser session to file."""
    if not cookie_file:
        return

    cookie_file.parent.mkdir(parents=True, exist_ok=True)
    with cookie_file.open("w") as f:
        json.dump(cookies, f)
    logger.info("Saved cookies to %s", cookie_file)


def load_cookies(cookie_file: Path | None = None) -> list[dict[str, str]]:
    """Load cookies from file to the browser session."""
    if not cookie_file:
        return []

    with cookie_file.open("r") as f:
        cookies = json.load(f)
    logger.info("Loaded cookies from %s", cookie_file)
    return cookies


def scroll_page(
    wd,
    selector: str | None = None,
    time_limit=30,
    scroll_limit=None,
    scroll_wait=1,
    retry_each_scroll=3,
):
    """Scroll a specific element or the whole page."""
    logger.info(
        f"Scrolling page: {selector=}, {time_limit=}, {scroll_limit=}, {scroll_wait=}, {retry_each_scroll=}"
    )

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
        max_scroll_top = element_info["scrollHeight"] - element_info["clientHeight"]
        scrolled = element_info["scrollTop"]
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
        #             if scrolled >= max_scroll_top:
        #                 logger.info("Reached bottom, scrolled: %d", scrolled)
        #                 return
        if scrolled == scrolled_pre:
            logger.info("No more scrolling possible, scrolled: %d", scrolled)
            return
        elapsed_time = time.time() - start_time
        if elapsed_time > time_limit:
            logger.warning("Reached time limit: %d seconds", time_limit)
            return


def run_script(wd, exe, retry_script=1, script_wait=1):
    logger.info("Executing script")
    for attempt in range(retry_script):
        logger.debug("Script execution attempt %d", attempt + 1)
        status = wd.execute_script(exe)
        if not status:
            break
        if script_wait:
            time.sleep(script_wait)
        logger.warning("Script returned status: %s", status)
    else:
        logger.warning("Script failed after %d retries", retry_script)


def selenium_get(
    wd: webdriver.Chrome,
    url: str,
    sleep: int = 0,
    ostream: TextIO = sys.stdout,
    time_limit: int = 30,
    scroll_limit: int | None = None,
    scroll_wait: float = 1,
    retry_each_scroll: int = 3,
    exe: str | None = None,
    scroll_exe: str | None = None,
    script_wait: float = 1,
    retry_script: int = 3,
    scroll_selector: str | None = None,
    save_incremental: bool = False,
) -> None:
    """Fetch a web page using Selenium and write the output to the specified stream."""
    logger.info("Loading page: %s", url)
    wd.get(url)
    logger.info("Page loaded successfully")

    if sleep:
        logger.debug("Sleeping for %d seconds", sleep)
        time.sleep(sleep)

    if exe:
        run_script(wd, exe, retry_script=retry_script, script_wait=script_wait)

    seen_content = set()
    scroll_params = dict(
        wd=wd,
        selector=scroll_selector,
        scroll_wait=scroll_wait,
        retry_each_scroll=retry_each_scroll,
        time_limit=time_limit,
        scroll_limit=scroll_limit,
    )

    if scroll_limit and save_incremental:
        start_time = time.time()
        scrolled = 0
        while scrolled < scroll_limit:
            time_elapsed = time.time() - start_time
            time_limit_remaining = max(0, time_limit - time_elapsed)
            if time_limit_remaining == 0:
                break
            scroll_params['time_limit'] = time_limit_remaining
            scroll_params['scroll_limit'] = min(scrolled + 1000, scroll_limit)
            scroll_page(**scroll_params)
            run_script(wd, scroll_exe)
            content = wd.page_source
            if content not in seen_content:
                seen_content.add(content)
                print(content, file=ostream)
            scrolled += 1000
    elif scroll_limit:
        scroll_page(**scroll_params)
        run_script(wd, scroll_exe)
        print(wd.page_source, file=ostream)
    else:
        print(wd.page_source, file=ostream)


def selenium_get_cli(
    ostream: TextIO,
    url: str,
    sleep: int = 0,
    images: bool = False,
    screenshot: str | None = None,
    time_limit: int = 30,
    scroll_limit: int = 100000,
    scroll_wait: float = 1,
    retry_each_scroll: int = 3,
    script: str | None = None,
    post_scroll_script: str | None = None,
    exe: str = "",
    script_wait: float = 1,
    retry_script: int = 3,
    facebook: bool = False,
    params: list[str] | None = None,
    scroll_selector: str | None = None,
    headless: bool = True,
    wait_for_user: bool = False,
    cookie_file: str | None = None,
    incremental: bool = False,
) -> None:
    """
    Fetch a web page, run the JavaScript, and write the output to stdout or a file.
    """
    opts = Options()

    if wait_for_user:
        headless = False
    if headless:
        opts.add_argument("--headless")
    opts.add_argument(f"user-agent={user_agent}")

    if not images:
        opts.add_argument("--blink-settings=imagesEnabled=false")

    program = Path(sys.argv[0]).resolve()
    prog_dir = program.parent

    if cookie_file and cookie_file == "-":
        cookie_file = DEFAULT_COOKIE_FILE
    cookie_path = Path(cookie_file) if cookie_file else None

    if script:
        exe += "\n" + Path(script).read_text(encoding="utf-8") + "\n"

    if facebook:
        exe += "\n" + (prog_dir / "facebook_scroller.js").read_text(encoding="utf-8") + "\n"
        incremental = True
    if facebook and not post_scroll_script:
        # TODO I was trying to get the post timestamps to show up, but they still don't
        post_scroll_script = prog_dir / "svg_realiser.js"

    scroll_exe = ""
    if post_scroll_script:
        scroll_exe = Path(post_scroll_script).read_text(encoding="utf-8") + "\n"

    if params:
        url += "?" + urlencode(dict(param.split("=") for param in params))

    with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts) as wd:
        cookies = load_cookies(cookie_path)
        set_cookies(wd, cookies)
        cookies = get_cookies(wd)

        selenium_get(
            wd,
            url,
            sleep=sleep,
            ostream=ostream,
            time_limit=time_limit,
            scroll_limit=scroll_limit,
            scroll_wait=scroll_wait,
            retry_each_scroll=retry_each_scroll,
            exe=exe,
            scroll_exe=scroll_exe,
            script_wait=script_wait,
            retry_script=retry_script,
            scroll_selector=scroll_selector,
            save_incremental=incremental,
        )

        # Take a screenshot if requested
        if screenshot:
            wd.save_screenshot(screenshot)

        # Wait for user input before closing the browser, and save cookies when they change
        while len(wd.window_handles) > 0:
            cookies_new = get_cookies(wd)
            if cookies_new != cookies:
                cookies = cookies_new
                save_cookies(cookie_path, cookies)
            if not wait_for_user:
                break
            time.sleep(CLOSE_WINDOW_POLL_INTERVAL)


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
    arg("-j", "--script", help="JavaScript file to run before scrolling")
    arg("-J", "--post-scroll-script", help="JavaScript file to run each time after we scroll")
    arg("-e", "--exe", help="JavaScript to run before scrolling")
    arg("-T", "--script-wait", help="Time to wait after running script, in seconds")
    arg("-R", "--retry-script", help="Number of times to retry running script")
    arg("-f", "--facebook", help="Download from Facebook, uses special scripts", action="store_true")
    arg("-p", "--params", help="URL parameters", nargs="+")
    arg("-E", "--scroll-selector", help="CSS selector for element to scroll")
    arg(
        "-H",
        "--head",
        help="Run browser in non-headless mode with a visible window",
        action="store_false",
        dest="headless",
        default=True,
    )
    arg(
        "-W",
        "--wait-for-user",
        help="Wait for user input before closing browser (implies --head)",
        action="store_true",
    )
    arg(
        "-C",
        "--cookie-file",
        help="Path to cookie file (default None, use '-' for ~/.local/share/selenium/cookies.json)",
    )
    arg("-I", "--incremental", help="Save content incrementally", action="store_true")


if __name__ == "__main__":
    main.go(selenium_get_cli, setup_args)
