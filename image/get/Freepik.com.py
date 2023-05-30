You can add a new function called `freepik_search` to search for images on Freepik.com like this:

```python
def freepik_search(query, max_results=12, safe="off", limit_max_results=True):
	""" Search Freepik.com for `query` and return a list of image results """

	if safe != "off":
		logger.warning("Safe search not implemented for Freepik")

	url = 'https://www.freepik.com/index.php'
	params = {
		'goto': 'search', 'hub': 'images', 'query': query
	}
	headers = {'User-Agent': user_agent}

	response = requests.get(url, headers=headers, params=params, timeout=timeout)
	response.raise_for_status()

	soup = BeautifulSoup(response.text, 'html.parser')

	search_results = []

	search_results2 = soup.find_all('div', class_='showcase__item')

	for res in search_results2:
		a = res.find('a', class_='showcase__item-container')
		img = res.find('img', class_='showcase__image')
		if not (a and img):
			continue

		res2 = {'title': img['alt'].strip(), 'url': a['href'], 'thumbnail': img['data-src']}
		if res2 not in search_results:
			search_results.append(res2)

	search_results = search_results[:max_results]

	if limit_max_results:
		search_results = search_results[:max_results]

	return search_results
```

After adding the `freepik_search` function, include it in the `engines` dictionary like this:

```python
engines = {
	'Google': google_search,
	'YouTube': youtube_search,
	'PornHub': pornhub_search,
	'Freepik': freepik_search,
}
```

Now, you can use the new search function for Freepik.com by providing `Freepik` as the engine argument:

```python
results = search('flower', engine='Freepik', max_results=8)
```

This will allow you to search for images on Freepik.com using the `search` function.
