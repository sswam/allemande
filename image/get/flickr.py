You can use the `flickrapi` package to search for images on Flickr. To install the package, you can run:

```
pip install flickrapi
```

Then, you can create a function to search for images on Flickr. Here's an example:

```python
import flickrapi

FLICKR_API_KEY = 'YOUR_FLICKR_API_KEY'
FLICKR_SECRET = 'YOUR_FLICKR_SECRET'

# Initialize Flickr API
flickr = flickrapi.FlickrAPI(api_key=FLICKR_API_KEY, secret=FLICKR_SECRET, format='parsed-json')

def search_flickr(query, max_results=12, safe="off"):
	"""
	Search Flickr for `query` and return a list of image results.
	"""
	safety_levels = {
		'off': '1,2,3',
		'moderate': '1,2',
		'strict': '1'
	}

	# Flickr API `flickr.photos.search` documentation: https://www.flickr.com/services/api/flickr.photos.search.html
	response = flickr.photos.search(text=query, per_page=max_results, content_type=7, safe_search=safety_levels[safe], extras='url_l')

	results = []
	if 'photos' in response and 'photo' in response['photos']:
		for photo in response['photos']['photo']:
			if 'url_l' in photo:
				data = {
					'title': photo['title'],
					'url': photo['url_l'],
					'id': photo['id']
				}
				results.append(data)

	return results
```

Replace `'YOUR_FLICKR_API_KEY'` with your actual Flickr API key and `'YOUR_FLICKR_SECRET'` with your actual Flickr Secret. If you don't have an API key, you can obtain one by signing up for a [Flickr API account](https://www.flickr.com/services/api/misc.api_keys.html).

To integrate this function into your existing search script, add it to the `engines` dictionary:

```python
engines = {
	'Google': google_search,
#    'DuckDuckGo': duckduckgo_search,
#    'Bing': bing_search,
	'YouTube': youtube_search,
	'PornHub': pornhub_search,
	'Flickr': search_flickr,  # Add this line
}
```

Now you can search for images on Flickr by calling the `search` function with the `engine='Flickr'` argument:

```python
results = search(query, engine='Flickr', max_results=12, safe="off")
```
