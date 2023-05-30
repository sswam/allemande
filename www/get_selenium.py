#!/usr/bin/env python3
""" get_selenium.py	Uses Selenium to fetch the content of a web page. """

import sys
import logging
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import argh

logger = logging.getLogger(__name__)


def scroll_to_bottom(wd, time_limit=30, scroll_limit=100000, scroll_wait=1, retry_each_scroll=3, exe=None, script_wait=1, retry_script=3):
    """ Scroll to the bottom of the page. """
    start_time = time.time()
    last_height = wd.execute_script("return document.body.scrollHeight")
    scrolled = 0

    if exe:
        for _ in range(retry_script):
            if script_wait:
                time.sleep(script_wait)
            status = wd.execute_script(exe)
            if status:
                logger.warning("Script returned status: %s", status)
                continuec
            break
        else:
            logger.warning("Script failed after %d retries", retry_script)

    while True:
        # Scroll down
        for _ in range(retry_each_scroll):
            ActionChains(wd).key_down(Keys.PAGE_DOWN).perform()
            time.sleep(scroll_wait)
            if scroll_limit and scrolled >= scroll_limit:
                return
            # get scroll offset from page
            scrolled = wd.execute_script("return window.pageYOffset;")

        new_height = wd.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            logger.warning("Reached bottom of page, height: %d", new_height)
            break

        last_height = new_height
        elapsed_time = time.time() - start_time
        if elapsed_time > time_limit:
            logger.warning("Reached time limit, elapsed time: %d", elapsed_time)
            break


@argh.arg("url", help="URL of the web page to fetch content")
@argh.arg("--time-limit", '-t', help="Maximum time for scrolling, in seconds", type=int, default=30)
@argh.arg("--scroll-limit", '-h', help="Maximum number of pixels to scroll down", type=int)
@argh.arg("--scroll-wait", '-w', help="Time to wait after each scroll, in seconds", type=int, default=1)
@argh.arg("--retry-each-scroll", '-r', help="Number of times to retry each scroll", type=int, default=3)
@argh.arg("--script", '-s', help="JavaScript file to run before scrolling")
@argh.arg("--exe", '-e', help="JavaScript to run before scrolling")
@argh.arg("--script-wait", '-T', help="Time to wait after running script, in seconds", type=int, default=1)
@argh.arg("--retry-script", '-R', help="Number of times to retry running script", type=int, default=3)
@argh.arg("--headless", '-H', help="Run in headless mode", action='store_true')
@argh.arg("--facebook", '-f', help="Download from Facebook", action='store_true')
def get_selenium(url, time_limit=30, scroll_limit=None, scroll_wait=1, retry_each_scroll=3, script=None, exe=None, script_wait=1, retry_script=3, headless=True, facebook=False):
    """ Uses Selenium to fetch the content of a web page. """
    program = Path(sys.argv[0])
    prog_dir = program.parent

    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless")

    exe = exe or ''
    if script:
        exe += "\n" + open(script).read() + "\n"

    if facebook:
        exe += "\n" + (prog_dir/"facebook_scroller.js").read_text() + "\n"

    with webdriver.Chrome(service=Service(), options=opts) as wd:
        wd.get(url)
        scroll_to_bottom(wd, time_limit=time_limit, scroll_limit=scroll_limit, scroll_wait=scroll_wait, retry_each_scroll=retry_each_scroll, exe=exe, script_wait=script_wait)
        page_source = wd.page_source

    return page_source


if __name__ == "__main__":
    argh.dispatch_command(get_selenium)
