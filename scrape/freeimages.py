You can add a `freeimages_search` function to search for images on freeimages.com. Here's the function you can integrate into your existing search script:

```python
def freeimages_search(query, max_results=12, limit_max_results=True):
	""" Search FreeImages for `query` and return a list of results """
	url = 'https://www.freeimages.com/search'
	params = {
		'q': query,
	}
	headers = {
		'User-Agent': user_agent,
	}
	response = requests.get(url, headers=headers, params=params, timeout=timeout)
	response.raise_for_status()

	soup = BeautifulSoup(response.text, 'html.parser')

	search_results = []

	search_results2 = soup.find_all('a', class_='search-result-asset-link')

	for res in search_results2:
		img = res.find('img')
		if img:
			title = img['alt'] if 'alt' in img.attrs else 'Untitled'
			thumbnail_url = img['src']
			image_page_url = 'https://www.freeimages.com' + res['href']
			search_results.append({'title': title, 'url': image_page_url, 'thumbnail': thumbnail_url})

	search_results = search_results[:max_results]

	if limit_max_results:
		search_results = search_results[:max_results]

	return search_results
```

Next, add the new search function to the `engines` and `agents` dictionaries:

```python
engines = {
	'Google': google_search,
	'FreeImages': freeimages_search,
	'YouTube': youtube_search,
	'PornHub': pornhub_search,
}

agents = {
	'Goog': google_search,
	'ImgFree': freeimages_search,
	'UTube': youtube_search,
	'Pr0nto': pornhub_search,
}

agent_engine = {
	'goog': 'Google',
	'imgfree': 'FreeImages',
	'utube': 'YouTube',
	'pr0nto': 'PornHub',
}
```

Now you can use the `freeimages_search` function by passing the engine name `'FreeImages'` or the agent name `'ImgFree'` to your existing search script.
