#!/usr/bin/env python3-allemande

""" giles-get: fetch URLs from a Giles TSV file """

import sys
import argparse
import re
import subprocess
import logging
from concurrent.futures import ThreadPoolExecutor
import argh

import ucm


MAX_PARALLEL_DEFAULT = 10

opts = None

logger = logging.getLogger(__name__)


def fetch_url(title: str, url: str, number: int, format: str = "%03d_%s") -> None:
	""" fetch a URL and save it in a file """

	try:
		logger.info(f'Fetching {title} from {url}')

		# title remove bad chars
		title_clean = re.sub(r'\s', '_', title)
		title_clean = re.sub(r'[^\w._-]', '_', title_clean)

		logger.info(f'Cleaned title: {title_clean}')

		# fetch the URL, save in a file
		file = f'{title_clean}.html'

		if number:
			file = format % (number, file)

		# save the URL in a file
		url_file = format % (number, f'{title_clean}.html.url')
		with open(url_file, 'w') as f:
			f.write(f"{url}\n")

		if re.match(r"https?://(www.facebook.com|www.instagram.com)/", url):
			command = ['selenium-get', "-f", "-o", file, url]
			logger.warning(f'Using Selenium to fetch {url}')
		else:
			command = ['wg', f"-O={file}", url]

		logger.info(f'Running {" ".join(command)}')

		# run command
		subprocess.run(command, check=True)

	except Exception as e:
		logger.error(f'Error fetching {title} from {url}: {e}')

	return file


def giles_get(parallel: int = MAX_PARALLEL_DEFAULT, number: bool = True, start: int = 1) -> None:
	""" fetch URLs from a Giles TSV file """

	lines = sys.stdin.readlines()

	if re.match(r"^title\turl\b", lines[0], re.IGNORECASE):
		logger.info("Skipping header line")
		lines = lines[1:]
	else:
		logger.info("No header line found")

	files = []

	# run several in parallel using ThreadPoolExecutor
	with ThreadPoolExecutor(max_workers=parallel) as executor:
		number = start
		for line in lines:
			title, url = line.strip().split('\t')
			# collect output files returned from fetch_url
			# executor.submit(fetch_url, title, url, number)
			file = executor.submit(fetch_url, title, url, number).result()
			files.append(file)
			number += 1

	# check file type and rename if needed using the extension-fix tool
	command = ['extension-fix', *files]
	logger.info(f'Running {" ".join(command)}')

	# get the output in fixed_tsv
	fixed_tsv = subprocess.run(command, check=True, capture_output=True).stdout.decode('utf-8')

	files = []

	# write the final file names to stdout
	for line in fixed_tsv.split('\n'):
		if not line:
			continue
		_old_name, filename = line.split('\t')
		files.append(filename)

	return files


# TODO factor out this main biolerplate stuff

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	argh.add_commands(parser, [giles_get])
	argh.set_default_command(parser, giles_get)
	ucm.add_logging_options(parser)
	opts = parser.parse_args()
	ucm.setup_logging(opts)
	argh.dispatch(parser)
