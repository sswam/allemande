#!/usr/bin/env python3

"""
This module fetches a web page using Selenium, runs the JavaScript,
and writes the output to stdout.
"""

import sys
import time
import logging
from typing import TextIO

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

from argh import arg
from ally import main

__version__ = "0.1.1"

logger = main.get_logger()

user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/58.0.3029.110 Safari/537.3"
)

def selenium_get(wd: webdriver.Chrome, url: str, sleep: int = 0, out: TextIO = sys.stdout) -> None:
    """Fetch a web page using Selenium and write the output to the specified stream."""
    logger.info("Loading page")
    wd.get(url)
    logger.info("Page loaded")

    if sleep:
        logger.info(f"Sleeping for {sleep} seconds")
        time.sleep(sleep)
        logger.info("Sleep completed")

    html = wd.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
    print(html, file=out)


@arg('url', help='URL of page to load')
@arg('--sleep', '-s', type=int, default=0, help='seconds to sleep before dumping DOM as HTML')
@arg('--images', '-i', default=False, help='enable images')
@arg('--screenshot', '-S', type=str, help='save screenshot to file')
def selenium_get_cli(
    url: str,
    sleep: int = 0,
    images: bool = False,
    screenshot: str = None,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Fetch a web page, run the JavaScript, and write the output to stdout.
    """
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument(f"user-agent={user_agent}")

    if not images:
        opts.add_argument('--blink-settings=imagesEnabled=false')

    with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts) as wd:
        try:
            selenium_get(wd, url, sleep=sleep, out=ostream)
        except Exception as e:
            logger.error(e)
        if screenshot:
            wd.save_screenshot(screenshot)


if __name__ == "__main__":
    main.run(selenium_get_cli)
