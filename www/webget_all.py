#!/usr/bin/env python3

import os
import sys
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import webget

__version__ = "1.0.0"

logger = logging.getLogger(__name__)

def run_webget(url, filename=None, wget=False):
    args = [url]
    if filename:
        args.extend(['-O', filename])
    if wget:
        args.append('-w')
    return webget.webget(*args)

def webget_all(urls, parallel=2, number=False, pad=5, wget=False):
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        i = 0
        futures = []
        for url in urls:
            while number:
                filename = f"{i:0{pad}d}"
                parsed_url = urlparse(url)
                ext = os.path.splitext(parsed_url.path)[1]
                if ext:
                    filename += ext
                if not os.path.exists(filename):
                    break
                i += 1
            if number:
                future = executor.submit(run_webget, url, filename, wget)
            else:
                future = executor.submit(run_webget, url, wget=wget)
            futures.append(future)
            i += 1
        for future in futures:
            future.result()

def main():
    parser = argparse.ArgumentParser(description="Download multiple URLs concurrently using webget.")
    parser.add_argument("-p", "--parallel", type=int, default=8, help="Number of concurrent downloads")
    parser.add_argument("-n", "--number", action="store_true", help="Number output files")
    parser.add_argument("--pad", type=int, default=5, help="Padding width for numbered files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-w", "--wget", action="store_true", help="Use wget instead of requests")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    urls = [line.strip() for line in sys.stdin]
    webget_all(urls, args.parallel, args.number, args.pad, args.wget)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error: {type(e).__name__} - {str(e)}")
        sys.exit(1)
