You can add a new function called `pixabay_search` to search for images on Pixabay using their API. First, you will need to get an API key from Pixabay by signing up for a free account and requesting an API key. Then, you can use the `requests` library to make an API call and parse the results.

Here is a sample `pixabay_search` function that you can integrate into your search script:

```python
def pixabay_search(query, max_results=12, api_key='YOUR_API_KEY'):
    """ Search Pixabay for `query` and return a list of image results """
    url = 'https://pixabay.com/api/'
    params = {
        'key': api_key,
        'q': query,
        'image_type': 'all',
        'per_page': max_results,
    }
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()

    data = response.json()
    search_results = data['hits']

    return [
        {
            'title': result['tags'],
            'url': result['pageURL'],
            'thumbnail': result['previewURL']
        } for result in search_results
    ]
```

Before using this function, replace `'YOUR_API_KEY'` with your actual Pixabay API key. You should also add the 'Pixabay' key to the `engines` dictionary like this:

```python
engines = {
	'Google': google_search,
	'YouTube': youtube_search,
	'PornHub': pornhub_search,
        'Pixabay': pixabay_search
}
```
