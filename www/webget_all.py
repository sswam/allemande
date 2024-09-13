#!/usr/bin/env python3

import os
import sys
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import subprocess

__version__ = "1.0.0"

logger = logging.getLogger(__name__)

def run_wg(url, filename=None):
    if filename:
        return subprocess.run(["wg", f"-O={filename}", url], check=True)
    else:
        return subprocess.run(["wg", url], check=True)

def wget_all(urls, parallel=2, number=False, pad=5):
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
                future = executor.submit(run_wg, url, filename)
            else:
                future = executor.submit(run_wg, url)
            futures.append(future)
            i += 1
        for future in futures:
            future.result()

def main():
    parser = argparse.ArgumentParser(description="Download multiple URLs concurrently using wg.")
    parser.add_argument("-p", "--parallel", type=int, default=8, help="Number of concurrent downloads")
    parser.add_argument("-n", "--number", action="store_true", help="Number output files")
    parser.add_argument("--pad", type=int, default=5, help="Padding width for numbered files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    urls = [line.strip() for line in sys.stdin]
    wget_all(urls, args.parallel, args.number, args.pad)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error: {type(e).__name__} - {str(e)}")
        sys.exit(1)
