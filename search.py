#!/usr/bin/env python3

# search: Search the web from the command line

# TODO: update my existing google script to use this

import requests
from bs4 import BeautifulSoup

from ucm import setup_logging, add_logging_options

import argparse
import logging

from typing import List, Dict

import io, pprint, csv, json, tabulate

logger = logging.getLogger(__name__)

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'

from youtube_search import YoutubeSearch

def duckduckgo_search(query, max_results=10, safe="off"):
	url = 'https://html.duckduckgo.com/html/'
	kp = {
		'off': -2,
		'moderate': -1,
		'strict': 1,
	}
	params = {
		'q': query,
		'kl': 'us-en',
		'kp': safe,
	}
	headers = {
		'User-Agent': user_agent,
	}
	response = requests.get(url, headers=headers, params=params)
	response.raise_for_status()

	soup = BeautifulSoup(response.text, 'html.parser')

	search_results = soup.find_all('h2', class_='result__title')

	search_results = search_results[:max_results]

	return [{'title': result.a.text.strip(), 'url': result.a['href']} for result in search_results]

def google_search(query, max_results=10, safe="off"):
	url = 'https://www.google.com/search'
	params = {
		'q': query,
		'safe': safe,
	}
	headers = {
		'User-Agent': user_agent,
	}
	response = requests.get(url, headers=headers, params=params)
	response.raise_for_status()

	soup = BeautifulSoup(response.text, 'html.parser')

	search_results = soup.find_all('div', class_='g')

	search_results = search_results[:max_results]

	return [{'title': result.find('h3').text.strip(), 'url': result.find('a')['href']} for result in search_results]

def bing_search(query, max_results=10, safe="off"):
	url = 'https://www.bing.com/search'
	params = {
		'q': query,
		'safeSearch': safe,
	}
	headers = {
		'User-Agent': user_agent,
	}
	response = requests.get(url, headers=headers, params=params)
	response.raise_for_status()

	soup = BeautifulSoup(response.text, 'html.parser')

	search_results = soup.find_all('li', class_='b_algo')

	search_results = search_results[:max_results]

	return [{'title': result.find('h2').text.strip(), 'url': result.find('a')['href']} for result in search_results]

def youtube_search(query, max_results=10, detailed=False, safe="off"):
	# TODO safe search not implemented
	results = YoutubeSearch(query, max_results=max_results).to_dict()

	for result in results:
		result['url'] = 'https://www.youtube.com' + result['url_suffix']

	results = results[:max_results]

	if detailed:
		return results

	return [{'title': result['title'], 'url': result['url'], 'thumbnail': result['thumbnails'][0]} for result in results]

engines = {
	'ddg': duckduckgo_search,
	'google': google_search,
	'bing': bing_search,
	'youtube': youtube_search,
}

def search(query, engine='ddg', max_results=10, safe="off"):
	results = engines[engine](query, max_results=max_results, safe=safe)
	return results[:max_results]


# output formatters

def format_csv(object: List[Dict[str, str]], delimiter=',') -> str:
	output = io.StringIO()
	writer = csv.DictWriter(output, fieldnames=object[0].keys(), delimiter=delimiter, dialect='unix', quoting=csv.QUOTE_MINIMAL)
	writer.writeheader()
	writer.writerows(object)
	return output.getvalue()

def format_tsv(object: List[Dict[str, str]]) -> str:
	return format_csv(object, delimiter='\t')

def format_json(object) -> str:
	return json.dumps(object, indent=4)

def format_python(object) -> str:
	return pprint.pformat(object, indent=4)

def format_tabulate(object: List[Dict[str, str]]) -> str:
	return tabulate.tabulate(object, headers='keys')

formatters = {
	'tsv': format_tsv,
	'csv': format_csv,
	'json': format_json,
	'py': format_python,
	'txt': format_tabulate,
}

def dict_first(d):
	return next(iter(d))

def main():
	parser = argparse.ArgumentParser()
	add_logging_options(parser)

	parser.add_argument('queries', nargs='*', help='Search queries')
	parser.add_argument('-engine', '-e', help='Search engine to use', default=dict_first(engines), choices=engines.keys())
	parser.add_argument('-format', '-f', help='Output format', default=dict_first(formatters), choices=formatters.keys())
	parser.add_argument('-max-results', '-m', help='Maximum number of results to return', type=int, default=10)
	parser.add_argument('-safe', '-s', help='Safe search', default='off', choices=['off', 'moderate', 'strict'])

	args = parser.parse_args()

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
