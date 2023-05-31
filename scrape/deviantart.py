You can add a `deviantart_search` function to search DeviantArt for images. Here's an example implementation that you can integrate into your existing code:

```python
def deviantart_search(query, max_results=12, limit_max_results=True):
	""" Search DeviantArt for `query` and return a list of results """
	url = 'https://www.deviantart.com/search/deviations'
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

	search_results2 = soup.find_all('a', class_='torpedo-thumb-link')

	for res in search_results2:
		title = res.get("title")
		if title is not None:
			search_results.append({"title": title, "url": res.get("href")})

	search_results = search_results[:max_results]

	if limit_max_results:
		search_results = search_results[:max_results]

	return search_results
```

Then, add 'DeviantArt' to the `engines` dictionary, like this:

```python
engines = {
	'Google': google_search,
	'YouTube': youtube_search,
	'PornHub': pornhub_search,
	'DeviantArt': deviantart_search,
}
```

Finally, you can test the DeviantArt search function with a query:

```python
print(search("landscape", engine="DeviantArt", max_results=5))
```

This will print the top 5 results for the "landscape" query on DeviantArt.
