#!/usr/bin/env python3
""" html2selectors.py - Convert HTML to CSS selectors """

from lxml import html

import lxml.etree

import argparse
import sys
import re

def remove_comments(tree):
	comments = tree.xpath('//comment()')
	for comment in comments:
		comment.getparent().remove(comment)
	return tree

def get_selector(element, parent_selector=None):
	selector = element.tag
	if not isinstance(selector, str):
		raise TypeError(f'element.tag has unknown type: {type(selector)}')
	if element.get('id'):
		selector += f'#{element.get("id")}'
	if element.get('class'):
		selector += '.' + '.'.join(element.get('class').split())
	selectors = [selector]
	if parent_selector:
		selectors = parent_selector["selectors"] + selectors
	obj = {"selectors": selectors, "content": element.text, "n_descendants": 1}
	return obj

def get_selectors_recursive(element, parent_selector=None):
	selectors = []
	selector = get_selector(element, parent_selector)
	selectors.append(selector)
	for child in element:
		child_selectors = get_selectors_recursive(child, selector)
		selectors.extend(child_selectors)
		selector['n_descendants'] += sum(obj['n_descendants'] for obj in child_selectors)
	return selectors

def html_to_selectors(html_str, delimiter='\t', content=False, number=False):
	tree = html.fromstring(html_str)
	tree = remove_comments(tree)
	selectors = get_selectors_recursive(tree)
	def to_string(obj):
		selector = delimiter.join(obj['selectors'])
		if number:
			selector = f"{obj['n_descendants']}\t{selector}"
		if content and obj['content'] is not None:
			content_squashed = re.sub(r'\s+', ' ', obj['content'])
			selector = f"{selector}\t\t{content_squashed}"
		return selector
	if delimiter is not None:
		selectors = [to_string(obj) for obj in selectors]
	return selectors

def test_html_to_selectors():
	html_str = '<html><body class="dark"><p id="foo">hello</p></body></html>'
	selectors = html_to_selectors(html_str, delimiter=' > ')
	assert selectors == ['html', 'html > body.dark', 'html > body.dark > p#foo']

def main():
	parser = argparse.ArgumentParser(description='Convert HTML to CSS selectors', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-d', '--delimiter', default=r'\t', help='Delimiter between selectors')
	parser.add_argument('-c', '--content', action='store_true', help='Include content')
	parser.add_argument('-n', '--number', action='store_true', help='Include number of descendants')
	parser.add_argument('-t', '--test', action='store_true', help='Run tests')
	args = parser.parse_args()

	# unescape args.delimiter from e.g. r'\t' to '\t'
	args.delimiter = args.delimiter.encode().decode('unicode_escape')

	if args.test:
		test_html_to_selectors()
		return

	html_str = sys.stdin.read()
	selectors = html_to_selectors(html_str, delimiter=args.delimiter, content=args.content, number=args.number)
	for selector in selectors:
		print(selector)

if __name__ == '__main__':
	main()
