#!/usr/bin/env python3

""" search: Search the web from the command line """

import argparse
import logging

from typing import List, Dict

import io
import pprint
import csv
import json
import urllib
import html
import re

import requests
from bs4 import BeautifulSoup
import tabulate
from youtube_search import YoutubeSearch
import tabulate


from ucm import setup_logging, add_logging_options

logger = logging.getLogger(__name__)

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'

# TODO don't just hard code this
timeout = 30


def duckduckgo_search(query, max_results=12, safe="off", limit_max_results=True):
	""" Search DuckDuckGo for `query` and return a list of results """
	url = 'https://html.duckduckgo.com/html/'
	kp = {
		'off': -2,
		'moderate': -1,
		'strict': 1,
		'on': 1,
	}
	params = {
		'q': query,
		'kl': 'us-en',
		'kp': kp[safe],
	}
	headers = {
		'User-Agent': user_agent,
	}
	response = requests.get(url, headers=headers, data=params, timeout=timeout)
	response.raise_for_status()

	soup = BeautifulSoup(response.text, 'html.parser')

	search_results = []

	search_results2 = soup.find_all('h2', class_='result__title')

	for res in search_results2:
		res2 = {'title': result.a.text.strip(), 'url': result.a['href']}
		if res2 not in search_results:
			search_results.append(res2)

	search_results = search_results[:max_results]

	if limit_max_results:
		search_results = search_results[:max_results]

	logger.warning("Results: %r", search_results)

	return search_results


def google_search(query, max_results=12, safe="off", limit_max_results=True):
	""" Search Google for `query` and return a list of results """
	url = 'https://www.google.com/search'
	params = {
		'q': query,
		'safe': safe,
	}
	headers = {
		'User-Agent': user_agent,
	}

	search_results = []
	response = None
	soup = None

	start = 0

	while len(search_results) < max_results:
		if response is not None:
			start += 10
			params['start'] = start
			logger.warning("Getting next page of results, start=%d", start)

		if start > max_results * 1.5:
			logger.warning("Start is %d, which is > 1.5 * max_results (%d), breaking", start, max_results)
			break

		logger.warning("Searching at %s", url)

		response = requests.get(url, headers=headers, params=params, timeout=timeout)
		response.raise_for_status()

		soup = BeautifulSoup(response.text, 'html.parser')

		search_results2 = soup.find_all('div', class_='g')

		logger.warning("Found %d results", len(search_results2))

		for res in search_results2:
			h3 = res.find('h3')
			a = res.find('a')
			if not (h3 and a):
				continue
			res2 = {'title': h3.text.strip(), 'url': a['href']}
			if res2["url"].startswith("/"):
				continue
			if res2 not in search_results:
				search_results.append(res2)

		logger.warning("Total results so far: %d", len(search_results))

		if len(search_results2) == 0:
			logger.warning("No more results, breaking")
			break

	if limit_max_results:
		search_results = search_results[:max_results]

	return search_results


def bing_search(query, max_results=12, safe="off", limit_max_results=True):
	""" Search Bing for `query` and return a list of results """
	url = 'https://www.bing.com/search'
	params = {
		'q': query,
		'safeSearch': safe,
	}
	headers = {
		'User-Agent': user_agent,
	}
	response = requests.get(url, headers=headers, params=params, timeout=timeout)
	response.raise_for_status()

	soup = BeautifulSoup(response.text, 'html.parser')

	search_results = []

	search_results2 = soup.find_all('li', class_='b_algo')

	search_results2 = [{'title': result.find('h2').text.strip(), 'url': result.find('a').get('href')} for result in search_results2]
	search_results2 = [result for result in search_results2 if result['url'] is not None]

	for res in search_results2:
		if res not in search_results:
			search_results.append(res)

	search_results = search_results[:max_results]

	if limit_max_results:
		search_results = search_results[:max_results]

	return search_results


def youtube_search(query, max_results=12, detailed=False, safe="off", limit_max_results=True):
	""" Search YouTube for `query` and return a list of results """
	if safe != "off":
		logger.warning("Safe search not implemented for YouTube")
	search_results2 = YoutubeSearch(query, max_results=max_results).to_dict()

	for result in search_results2:
		result['url'] = 'https://www.youtube.com' + result['url_suffix']

	search_results = []

	for res in search_results2:
		# remove crap from thumbnail URL
		if 'thumbnails' in res and len(res['thumbnails']) > 0:
			res['thumbnail'] = re.sub(r'\?.*', '', res['thumbnails'][0])

		# remove crap from the main URL
		if re.match(r'https?://www.youtube.com/watch\?v=', res['url']):
			res['url'] = re.sub(r'&.*', '', res['url'])

		if res not in search_results:
			search_results.append(res)

	search_results = search_results[:max_results]

	if limit_max_results:
		search_results = search_results[:max_results]

	if detailed:
		return search_results

	return [{'title': result['title'], 'url': result['url'], 'thumbnail': result['thumbnail']} for result in search_results]


def pornhub_search(query, max_results=10, safe="off"):
	site = 'https://www.pornhub.com'
	url = site + '/video/search'

	params = {
		'search': query,
	}

	headers = {
		'User-Agent': user_agent,
	}
	response = requests.get(url, headers=headers, params=params)
	response.raise_for_status()

	soup = BeautifulSoup(response.text, 'html.parser')

	container = soup.find('ul', id='videoSearchResult')

	search_results = container.find_all('a', class_='linkVideoThumb')

#	def get_thumbnail_url(result):
#		thumb = result.find('img')
#		thumb_url = thumb.get('src') # or thumb.get('data-image') or thumb.get('data-mediumthumb')
#		return thumb_url

	search_results = search_results[:max_results]

	return [
		{'title': result['title'], 'url': site + result['href'], 'thumbnail': result.find('img')['src']}
		for result in search_results
		if not result['href'].startswith('javascript:')
	]


engines = {
	'Google': google_search,
#	'DuckDuckGo': duckduckgo_search,
#	'Bing': bing_search,
	'YouTube': youtube_search,
	'PornHub': pornhub_search,
}


agents = {
	'Goog': google_search,
#	'DuckDuckGo': duckduckgo_search,
#	'Bing': bing_search,
	'UTube': youtube_search,
	'Pr0nto': pornhub_search,
}


agent_engine = {
	'goog': 'Google',
	'utube': 'YouTube',
	'pr0nto': 'PornHub',
}


def esc(s):
	s = html.escape(s)  # Handles HTML entities
	s = s.replace("|", "&#124;")  # Handles "|" character for Markdown tables
	s = s.replace("\n", "&#10;")  # newlines
	return s


def list_to_markdown_table(items, engine):
	engine = agent_engine.get(engine.lower(), engine)
	i = 1
	for item in items:
		item['#'] = i
		i += 1
		url_enc = esc(item['url'])
		title_enc = esc(item['title'])
		item['page'] = f"""<a href="{url_enc}" target="_blank">{title_enc}</a>"""
		f"[{item['title']}]({item['url']})"
		if engine not in ('YouTube', 'PornHub'):
			item['site'] = urllib.parse.urlparse(item['url']).netloc
		if 'thumbnail' in item:
			# convert to markdown image
			image = f"""<img class="thumb" src="{esc(item['thumbnail'])}" alt="{title_enc}">"""
			del item['thumbnail']
			item['thumbnail'] = image
		if engine in ('YouTube', 'PornHub'):
			video_id = None
			params = urllib.parse.parse_qs(urllib.parse.urlparse(item['url']).query)
			video_id = params.get('v', [None])[0]
			if not video_id:
				video_id = params.get('viewkey', [None])[0]
			if not video_id:
				# Try shorts URL format
				# https://www.youtube.com/shorts/pbU5lUon9AU
				if re.match(r'^/shorts/', urllib.parse.urlparse(item['url']).path):
					video_id = urllib.parse.urlparse(item['url']).path.split('/')[-1]
			if not video_id:
				logger.warning("Could not parse YouTube video ID from URL %s", item['url'])
			if video_id:
				img = item['thumbnail']
				video = f"""<div class="embed" data-site="{engine.lower()}" data-videoid="{video_id}">""" + img + f"""<br><div class="caption">{item['page']}</div></div>"""
				item['video'] = video
				del item['thumbnail']
				del item['page']
		del item['url']
		del item['title']

	# check all items have video
	if engine in ('YouTube', 'PornHub') and all('video' in item for item in items):
		return "<br><div>" + ("\n".join([item['video'] for item in items])) + "</div>"
	return tabulate.tabulate(items, tablefmt="pipe", headers="keys")


def search(query, engine='duckduckgo', max_results=8, safe="off", markdown=False):
	""" Search `query` using `engine` and return a list of results """
	lc_keys_to_keys = {k.lower(): k for k in list(engines.keys()) + list(agents.keys())}
	key = lc_keys_to_keys[engine.lower()]
	eng = engines.get(key, agents.get(key))
	results = eng(query, max_results=max_results, safe=safe)
	results2 = results[:max_results]
	if markdown:
		return list_to_markdown_table(results2, engine)
	return results2


# output formatters


def format_csv(obj: List[Dict[str, str]], delimiter=',') -> str:
	""" Format `obj` as CSV """
	if not obj:
		return ""
	output = io.StringIO()
	writer = csv.DictWriter(output, fieldnames=obj[0].keys(), delimiter=delimiter, dialect='unix', quoting=csv.QUOTE_MINIMAL)
	writer.writeheader()
	writer.writerows(obj)
	return output.getvalue()


def format_tsv(obj: List[Dict[str, str]]) -> str:
	""" Format `obj` as TSV """
	return format_csv(obj, delimiter='\t')


def format_json(obj) -> str:
	""" Format `obj` as JSON """
	return json.dumps(obj, indent=4)


def format_python(obj) -> str:
	""" Format `obj` as Python code """
	return pprint.pformat(obj, indent=4)


def format_tabulate(obj: List[Dict[str, str]]) -> str:
	""" Format `obj` as a table """
	if not obj:
		return ""
	return tabulate.tabulate(obj, headers='keys')


formatters = {
	'tsv': format_tsv,
	'csv': format_csv,
	'json': format_json,
	'py': format_python,
	'txt': format_tabulate,
}


def dict_first(d):
	""" Return the first key in a dictionary """
	return next(iter(d))


def parse_args():
	""" Parse command line arguments """
	parser = argparse.ArgumentParser()
	add_logging_options(parser)
	parser.add_argument('queries', nargs='*', help='Search queries')
	parser.add_argument('-engine', '-e', help='Search engine to use', default=dict_first(engines), choices=list(map(str.lower, engines.keys())))
	parser.add_argument('-format', '-f', help='Output format', default=dict_first(formatters), choices=formatters.keys())
	parser.add_argument('-max-results', '-m', help='Maximum number of results to return', type=int, default=8)
	parser.add_argument('-safe', '-s', help='Safe search', default='off', choices=['off', 'moderate', 'strict'])
	args = parser.parse_args()
	return args


def main():
	""" Main function """
	args = parse_args()
	setup_logging(args)

	# search_queries = ['newest adafruit microcontroller boards', 'newest teensy microcontroller boards']
	# search_queries = ['newest adafruit microcontroller boards']

	for query in args.queries:
		results = search(query, engine=args.engine, max_results=args.max_results, safe=args.safe)

		# output using the specified formatter
		formatter = formatters[args.format]
		formatted_results = formatter(results).rstrip()
		print(formatted_results)

#		for result in results:
#			print(result.get('title'))
#			print(result['url'])
#			print()


if __name__ == '__main__':
	main()
