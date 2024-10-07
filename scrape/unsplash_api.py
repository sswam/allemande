To integrate a function that searches for images on Unsplash, you can follow the steps below:

1. Register for an API key from Unsplash by signing up [here](https://unsplash.com/developers).

2. Add the `search_unsplash_images` function to your code. Pass the API key to the function as a parameter or set it as an environment variable.

3. Add `'Unsplash': search_unsplash_images` to the `engines` dictionary in your code.

4. Add support for the Unsplash search in the `list_to_markdown_table` and `search` functions.

Here is the function you can integrate into your search script:

```python
def search_unsplash_images(query, max_results=12, safe="off", limit_max_results=True, api_key=None):
	""" Search Unsplash for `query` and return a list of images """
	if api_key is None:
		raise ValueError("Unsplash API key is required")

	url = 'https://api.unsplash.com/search/photos'
	params = {
		'query': query,
		'per_page': max_results,
		'client_id': api_key,
	}
	headers = {
		'User-Agent': user_agent,
	}
	response = requests.get(url, headers=headers, params=params, timeout=timeout)
	response.raise_for_status()

	search_data = response.json()

	search_results = [
		{'title': result['description'] or result['alt_description'],
         'url': result['links']['html'],
         'thumbnail': result['urls']['thumb']}
		for result in search_data['results']
	]

	if limit_max_results:
		search_results = search_results[:max_results]

	return search_results
```

In the `engines` dictionary, add the `'Unsplash': search_unsplash_images` line:

```python
engines = {
	'Google': google_search,
	'YouTube': youtube_search,
	'PornHub': pornhub_search,
	'Unsplash': search_unsplash_images,  # Add this line
}
```

Add support for the Unsplash search in the `list_to_markdown_table` function by handling the Unsplash case:

```python
def list_to_markdown_table(items, engine):
	...
	# Add this block to handle Unsplash results
	if engine.lower() == 'unsplash':
		return "<br><div>" + ("\n".join([f'<a href="{esc(item["url"])}" target="_blank"><img class="thumb" src="{esc(item["thumbnail"])}" alt="{esc(item["title"])}"></a>' for item in items])) + "</div>"
```

Finally, add the Unsplash search engine option in the `parse_args` function:

```python
def parse_args():
     parser.add_argument('-engine', '-e', help='Search engine to use', default=dict_first(engines), choices=list(map(str.lower, engines.keys() + ['unsplash'])))  # Add 'unsplash' to the list of choices
```

Now you should be able to search for images on Unsplash by specifying the `-engine Unsplash` option when calling your script.
