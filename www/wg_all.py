#!/usr/bin/env python3-allemande

import os
import sys
import logging
import argparse
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
import subprocess

__version__ = "1.0.0"

logger = logging.getLogger(__name__)

def run_wg(url, filename=None):
    cmd = ["wg", url]
    if filename:
        cmd.extend(["-O", filename])

    try:
        subprocess.run(cmd, check=True)
        logging.info(f"Downloaded: {url}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to download {url}: {e}")

def wget_stream(istream=sys.stdin, parallel=2, number=False, pad=5):
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        i = 0
        futures = []

        for url in istream:
            url = url.strip()
            if not url:
                continue

            filename = None
            if number:
                while True:
                    filename = f"{i:0{pad}d}"
                    parsed_url = urlparse(url)
                    ext = os.path.splitext(parsed_url.path)[1]
                    if ext:
                        filename += ext
                    if not os.path.exists(filename):
                        break
                    i += 1

            future = executor.submit(run_wg, url, filename)
            futures.append(future)
            i += 1

            # Check and remove completed futures
            futures = [f for f in futures if not f.done()]

        # Wait for remaining futures to complete
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

    wget_stream(args.parallel, args.number, args.pad)

if __name__ == "__main__":
