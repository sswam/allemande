#!/usr/bin/env python3-allemande

import os
import sys
import logging
import subprocess
import argparse
from pathlib import Path
import sqlite3
import requests
import http.cookiejar
from urllib.parse import urlparse

import argh

__version__ = "1.0.0"

logger = logging.getLogger(__name__)


def get_firefox_cookie_file():
    firefox_dir = Path.home() / ".mozilla" / "firefox"
    default_profile = next(firefox_dir.glob("*.default"), None)
    if default_profile:
        return default_profile / "cookies.sqlite"
    return None


def usage():
    print >>sys.stderr, "Usage: %s SQLITE3DB DOMAIN" % os.path.basename(sys.argv[0])
    sys.exit(1)


def fetch_cookies_from_sqlite(db_path, domain_pattern):
    """
    Fetch and print cookies from a SQLite database matching a domain pattern.
    """
    # Prepare the SQL query
    query = """
    SELECT host, path, isSecure, expiry, name, value 
    FROM moz_cookies 
    WHERE host LIKE ?
    """
    
    # Connect to the database
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute(query, [f'%{domain_pattern}%'])
        
        # Fetch all matching cookies
        cookies = cursor.fetchall()

    for cookie in cookies:
        host, path, is_secure, expiry, name, value = cookie
        
        # Format boolean values
        domain_dot = 'TRUE' if host.startswith('.') else 'FALSE'
        secure = 'TRUE' if is_secure else 'FALSE'

        # Print the formatted cookie
        print('\t'.join([host, domain_dot, path, secure, expiry, name, value]))

    return cookies


def convert_sqlite_to_txt(sqlite_file, txt_file):
    with open(txt_file, "w") as output_file:
        fetch_cookies_from_sqlite(sqlite_file, "%")
        output_file.write(cookies)


def write_safely_numbered(filename, content):
    base, ext = os.path.splitext(filename)
    counter = 1
    while True:
        try:
            with open(filename, 'xb') as f:
                f.write(content)
            break
        except FileExistsError:
            filename = f"{base}.{counter}{ext}"
            counter += 1


def requests_download(timeout=5, tries=5, content_disposition=False, output_file=None, verbose=False, referer=None, *urls):
    agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

    cf_sqlite = os.environ.get("CF_SQLITE")
    cf = os.environ.get("CF")

    if not cf_sqlite and not cf:
        cf = get_firefox_cookie_file()
        if cf:
            cf_sqlite = cf
            cf = cf.with_suffix(".txt")

    if cf_sqlite and cf_sqlite.exists() and cf_sqlite.stat().st_mtime > cf.stat().st_mtime:
        convert_sqlite_to_txt(cf_sqlite, cf)

    if cf:
        cookies = http.cookiejar.MozillaCookieJar(cf)
        cookies.load(ignore_discard=True, ignore_expires=True)
    else:
        cookies = http.cookiejar.CookieJar()

    session = requests.Session()
    session.cookies = cookies
    session.headers.update({'User-Agent': agent})

    if referer == "self":
        referer = next((url for url in urls if "://" in url), None)

    for url in urls:
        for attempt in range(tries):
            try:
                headers = {'Referer': referer} if referer else {}
                response = session.get(url, timeout=timeout, headers=headers, verify=False)
                response.raise_for_status()

                if content_disposition:
                    filename = get_filename_from_cd(response.headers.get('content-disposition'))
                else:
                    filename = output_file or os.path.basename(urlparse(url).path)

                filename = filename or "index.html"

                write_safely_numbered(filename, response.content)

                if verbose:
                    print(f"Downloaded: {url} -> {filename}")

                break  # Success, exit the retry loop
            except requests.RequestException as e:
                if verbose:
                    print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == tries - 1:
                    print(f"Failed to download {url} after {tries} attempts")


def get_filename_from_cd(cd):
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0].strip('"')


def wget_download(timeout=5, tries=5, content_disposition=False, output_file=None, verbose=False, referer=None, *urls):
    agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

    cf_sqlite = os.environ.get("CF_SQLITE")
    cf = os.environ.get("CF")

    if not cf_sqlite and not cf:
        cf = get_firefox_cookie_file()
        if cf:
            cf_sqlite = cf
            cf = cf.with_suffix(".txt")

    if cf_sqlite and cf_sqlite.exists() and cf_sqlite.stat().st_mtime > cf.stat().st_mtime:
        convert_sqlite_to_txt(cf_sqlite, cf)

    wget_args = [
        "wget",
        "-e", "robots=off",
        "--no-check-certificate",
        "-T", str(timeout),
        "--load-cookies", str(cf),
        "-U", agent,
        "--tries", str(tries),
    ]

    if content_disposition:
        wget_args.append("--content-disposition")

    if output_file:
        wget_args.extend(["-O", output_file])

    if verbose:
        wget_args.append("-v")

    if referer == "self":
        referer = next((url for url in urls if "://" in url), None)

    if referer:
        wget_args.extend(["--referer", referer])

    wget_args.extend(urls)

    subprocess.run(wget_args)


@argh.arg('-t', '--timeout', type=int, default=5, help='Timeout in seconds')
@argh.arg('-n', '--tries', type=int, default=5, help='Number of retries')
@argh.arg('-C', '--content-disposition', action='store_true', help='Honor Content-Disposition header')
@argh.arg('-O', '--output-file', help='Output file')
@argh.arg('-v', '--verbose', action='store_true', help='Verbose output')
@argh.arg('-r', '--referer', help='Referer URL')
@argh.arg('-w', '--wget', help='Use wget')
@argh.arg('urls', nargs='+', help='URLs to download')
def webget(timeout=5, tries=5, content_disposition=False, output_file=None, verbose=False, referer=None, wget=False, *urls):
    """
    A wget wrapper that pretends to be a browser.

    This script uses wget to download files while mimicking browser behavior.

    Usage:
        python wg.py [OPTIONS] URL [URL...]
    """
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING, format="%(message)s")

    try:
        downloader = wget_download if wget else requests_download
        downloader(timeout, tries, content_disposition, output_file, verbose, referer, *urls)
    except Exception as e:
        logger.error("Error: %s %s", type(e).__name__, str(e))
        raise
        if logging.getLogger().level == logging.DEBUG:
            raise
        sys.exit(1)

if __name__ == '__main__':
    argh.dispatch_command(webget)
