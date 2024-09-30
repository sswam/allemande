#!/usr/bin/env python3

"""
Fetches a web page using Selenium, runs the JavaScript,
and writes the output to stdout or a file.
"""

import sys
import time
import logging
from typing import TextIO
from pathlib import Path
from urllib.parse import urlencode

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from argh import arg

from ally import main

__version__ = "0.3.1"

logger = main.get_logger()

user_agent = (
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
	"AppleWebKit/537.36 (KHTML, like Gecko) "
	"Chrome/58.0.3029.110 Safari/537.3"
)

def scroll_to_bottom(wd, time_limit=30, scroll_limit=100000, scroll_wait=1, retry_each_scroll=3):
	""" Scroll to the bottom of the page. """
	start_time = time.time()
	last_height = wd.execute_script("return document.body.scrollHeight")
	scrolled = 0

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

def selenium_get(wd: webdriver.Chrome, url: str, sleep: int = 0, out: TextIO = sys.stdout,
				time_limit=30, scroll_limit=None, scroll_wait=1, retry_each_scroll=3,
				exe=None, script_wait=1, retry_script=3) -> None:
	"""Fetch a web page using Selenium and write the output to the specified stream."""
	logger.info("Loading page")
	wd.get(url)
	logger.info("Page loaded")

	if sleep:
		logger.info(f"Sleeping for {sleep} seconds")
		time.sleep(sleep)
		logger.info("Sleep completed")

	if exe:
		for _ in range(retry_script):
			if script_wait:
				time.sleep(script_wait)
			status = wd.execute_script(exe)
			if status:
				logger.warning("Script returned status: %s", status)
				continue
			break
		else:
			logger.warning("Script failed after %d retries", retry_script)

	if scroll_limit:
		scroll_to_bottom(wd, time_limit, scroll_limit, scroll_wait, retry_each_scroll)

	html = wd.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
	print(html, file=out)

@arg('url', help='URL of page to load')
@arg('--sleep', '-s', type=int, default=0, help='seconds to sleep before dumping DOM as HTML')
@arg('--images', '-i', default=False, help='enable images')
@arg('--screenshot', '-S', type=str, help='save screenshot to file')
@arg('--time-limit', '-t', help='Maximum time for scrolling, in seconds', type=int, default=30)
@arg('--scroll-limit', '-h', help='Maximum number of pixels to scroll down', type=int)
@arg('--scroll-wait', '-w', help='Time to wait after each scroll, in seconds', type=float, default=1)
@arg('--retry-each-scroll', '-r', help='Number of times to retry each scroll', type=int, default=3)
@arg('--script', '-c', help='JavaScript file to run before scrolling')
@arg('--exe', '-e', help='JavaScript to run before scrolling')
@arg('--script-wait', '-T', help='Time to wait after running script, in seconds', type=float, default=1)
@arg('--retry-script', '-R', help='Number of times to retry running script', type=int, default=3)
@arg('--facebook', '-f', help='Download from Facebook', action='store_true')
@arg('--output', '-o', help='Output file')
@arg('--params', '-p', help='URL parameters', nargs='+')
def selenium_get_cli(
	url: str,
	sleep: int = 0,
	images: bool = False,
	screenshot: str = None,
	time_limit: int = 30,
	scroll_limit: int = None,
	scroll_wait: float = 1,
	retry_each_scroll: int = 3,
	script: str = None,
	exe: str = None,
	script_wait: float = 1,
	retry_script: int = 3,
	facebook: bool = False,
	output: str = None,
	params: list = None,
	istream: TextIO = sys.stdin,
	ostream: TextIO = sys.stdout,
) -> None:
	"""
	Fetch a web page, run the JavaScript, and write the output to stdout or a file.
	"""
	opts = Options()
	opts.add_argument("--headless")
	opts.add_argument(f"user-agent={user_agent}")

	if not images:
		opts.add_argument('--blink-settings=imagesEnabled=false')

	program = Path(sys.argv[0])
	prog_dir = program.parent

	exe = exe or ''

	if script:
		exe += "\n" + open(script).read() + "\n"

	if facebook:
		exe += "\n" + (prog_dir/"facebook_scroller.js").read_text() + "\n"

	if params:
		url += '?' + urlencode(dict(param.split('=') for param in params))

	with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts) as wd:
		try:
			out = open(output, 'w') if output else ostream
			selenium_get(wd, url, sleep=sleep, out=out, time_limit=time_limit,
						scroll_limit=scroll_limit, scroll_wait=scroll_wait,
						retry_each_scroll=retry_each_scroll, exe=exe,
						script_wait=script_wait, retry_script=retry_script)
			if output:
				out.close()
		except Exception as e:
			logger.error(e)
		if screenshot:
			wd.save_screenshot(screenshot)

if __name__ == "__main__":
	main.run(selenium_get_cli)
