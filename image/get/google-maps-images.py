To integrate a function for searching Google Maps for images, you can use the following function:

```python
def google_maps_image_search(query, max_results=12):
	base_url = "https://www.google.com/maps"
	search_url = base_url + "/search/"

	headers = {
		'User-Agent': user_agent,
	}

	params = {
		'q': query,
	}

	response = requests.get(search_url, headers=headers, params=params, timeout=timeout)
	response.raise_for_status()

	soup = BeautifulSoup(response.text, 'html.parser')

	image_results = []

	image_tags = soup.find_all('img', class_='tactile-search-thumbnail-raster')

	for img_tag in image_tags:
		img_src = img_tag.get('src')
		if img_src:
			image_results.append({'image_url': img_src})

	return image_results[:max_results]
```

Then, to use this function with your script, add the following line to the `engines` dictionary:

```python
engines = {
	# ... other engines ...
	'GoogleMapsImages': google_maps_image_search,
}
```

Now you can use the `GoogleMapsImages` engine for searching Google Maps images. For example:

```python
results = search("Eiffel Tower", engine='GoogleMapsImages', max_results=8)
for result in results:
	print(result['image_url'])
```

Please note that this method might not be stable due to changes in the HTML structure of Google Maps. It's recommended to use Google Maps APIs for reliable and approved ways to access data from Google Maps.
