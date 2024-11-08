#!/usr/bin/env python3-allemande

""" wg.py: A simple script to download files from the web using cookies.txt """

import asyncio
import aiohttp
import argparse
import os
from http.cookies import SimpleCookie
from distutils import util
import argh


async def fetch_url(url, headers, params=None, retries=10, timeout=10, verbose=False, content_disposition=None):
	""" Fetch a URL """
	async with aiohttp.ClientSession(headers=headers) as session:
		for attempt in range(retries):
			try:
				async with session.get(url, params=params, timeout=timeout, ssl=False) as response:
					if content_disposition and "Content-Disposition" in response.headers:
						filename = response.headers["Content-Disposition"].split("filename=")[1].strip('"')
						with open(filename, "wb") as f:
							while (chunk := await response.content.read(1024)):
								f.write(chunk)
						print("Saved as:", filename)
					else:
						print(await response.text())
				break
			except Exception as e:
				if verbose:
					print("Retrying due to:", e)
		else:
			print(f"Failed after {retries} attempts")


def prepare_cookies(cookies_filename, allow_sqlite_conversions):
	""" Prepare cookies for the request """
	if not os.path.exists(cookies_filename) and allow_sqlite_conversions:
		try:
			from cookies_sql2txt import cookies_sql2txt
			sqlite_filename = cookies_filename.replace(".txt", ".sqlite")
			if os.path.exists(sqlite_filename) and os.path.getmtime(sqlite_filename) > os.path.getmtime(cookies_filename):
				cookies_sql2txt(sqlite_filename, cookies_filename)
		except ImportError:
			pass

	with open(cookies_filename) as cookies_file:
		cookies_raw = cookies_file.read()

	return SimpleCookie(cookies_raw)


def parse_extra_opts(extra_opts):
	""" Parse extra options """
	if not extra_opts:
		return None

	try:
		return dict(opt.split('=') for opt in extra_opts.split('&'))
	except ValueError:
		print("Invalid extra options")
		return None


def setup_headers(args, cookies):
	""" Setup headers for the request """
	headers = {
		"User-Agent": args.user_agent,
		"Cookie": "; ".join(f"{k}={v.value}" for k, v in cookies.items()),
	}
	if args.referer and args.referer.lower() != "self":
		headers["Referer"] = args.referer

	return headers


async def download_in_parallel(urls, headers, params=None, retries=10, timeout=10, verbose=False, content_disposition=False, parallel=1):
	""" Download files in parallel """
	semaphore = asyncio.Semaphore(value=parallel)

	async def fetch_with_semaphore(url):
		async with semaphore:
			await fetch_url(url, headers, params=params, retries=retries, timeout=timeout,
							verbose=verbose, content_disposition=content_disposition)

	tasks = [fetch_with_semaphore(url) for url in urls]
	await asyncio.gather(*tasks)


@argh.arg("url", help="Target URL", nargs="+")
@argh.arg("-i", "--stdin", help="Read URLs from stdin", action="store_true")
@argh.arg("-c", "--cookies-filename", help="Path to the cookies.txt file")
@argh.arg("-r", "--referer", help="Referer for the request (use 'self' for the same as the target URL)")
@argh.arg("-t", "--timeout", type=int, default=10, help="Timeout in seconds")
@argh.arg("-T", "--retries", type=int, default=10, help="Number of times to retry on error")
@argh.arg("-v", "--verbose", action="store_true", help="Verbose output")
@argh.arg("-a", "--user-agent", default="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36", help="User agent string")
@argh.arg("-C", "--content-disposition", action="store_true", help="Save with remote filename")
@argh.arg("--extra-opts", help="Additional URL parameters (e.g., 'key=value&key2=value2')")
@argh.arg("--allow-sqlite-conversions", type=lambda x: bool(util.strtobool(x)), nargs="?", const=True, default=False, help="Allow cookies SQLite to txt conversion")
@argh.arg("-p", "--parallel", type=int, default=1, help="Number of parallel downloads")
async def wg(url: list, cookies_filename=None, referer=None, timeout=10, retries=10, verbose=False, user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36", content_disposition=False, extra_opts=None, allow_sqlite_conversions=False, parallel=1):
	""" wg.py: A simple script to download files from the web using cookies.txt """
	cookies_filename = cookies_filename or os.path.expanduser("~/.mozilla/firefox/*.default/cookies.txt")
	cookies = prepare_cookies(cookies_filename, allow_sqlite_conversions)
	headers = setup_headers(argh.Parser().parse_args(), cookies)
	params = parse_extra_opts(extra_opts)

	if parallel > 1:
		await download_in_parallel(url, headers, params=params, retries=retries, timeout=timeout,
                                     verbose=verbose, content_disposition=content_disposition, parallel=parallel)
	else:
		for target_url in url:
			await fetch_url(target_url, headers, params=params, retries=retries, timeout=timeout,
							verbose=verbose, content_disposition=content_disposition)


if __name__ == "__main__":
	argh.dispatch(wg)
