Here's a function to search for images on Pexels:

```python
import os
from pexels_api import PexelsAPI

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")  # Replace with your Pexels API key or use environment variable
pexels_client = PexelsAPI(PEXELS_API_KEY)

def search_pexels_images(query, max_results=12):
	if not PEXELS_API_KEY:
		raise ValueError("PEXELS_API_KEY is not set. Please set your Pexels API key.")

	search_results = pexels_client.search(query, per_page=max_results)
	images = []
	for photo in search_results['photos']:
		images.append({
			'photographer': photo['photographer'],
			'url': photo['url'],
			'src': photo['src']
		})

	return images
```

You'll need to install the `pexels-api` package and set your Pexels API key to use this function. You can install the package using:

```bash
pip install pexels-api
```

To integrate this function into the search script, you can add the following:

1. Import required packages at the top of the script:

```python
import os
from pexels_api import PexelsAPI
```

2. Add your Pexels API key:

```python
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")  # Replace with your Pexels API key or use environment variable
pexels_client = PexelsAPI(PEXELS_API_KEY)
```

3. Add the `search_pexels_images` function to the `engines` dictionary:

```python
engines = {
	'Google': google_search,
	'YouTube': youtube_search,
	'PornHub': pornhub_search,
	'Pexels': search_pexels_images,
}
```

Now you can use the Pexels search engine by passing `'Pexels'` as the engine argument when calling `search`:

```python
images = search("nature", engine="Pexels", max_results=8)
print(images)
```

This will return images from Pexels related to the "nature" query.
