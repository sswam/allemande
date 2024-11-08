```python
#!/usr/bin/env python3-allemande
""" wp_images.py: """

import sys
import os
import logging
import requests

from wordpress_api import Client
from argh import arg, ArghParser

logger = logging.getLogger(__name__)

def list_images(api_url, username, password):
	""" List images in the WordPress Media Library """
	client = Client(api_url, username, password)

	images = client.get_media()
	for image in images:
		print(f"{image['title']['rendered']} - {image['source_url']}")

@arg('-n', '--normal', help='Path of normal image', required=True)
@arg('-k', '--2k', help='Path of @2K image', required=True)
def upload_image(api_url, username, password, normal, _2k):
	""" Upload an image and its @2K version to the WordPress Media Library """
	client = Client(api_url, username, password)

	# Upload normal image
	with open(normal, 'rb') as file:
		response = client.upload_media(file)
	print('Normal image uploaded:', response['source_url'])

	# Upload @2K image
	with open(_2k, 'rb') as file:
		response = client.upload_media(file)
	print('@2K image uploaded:', response['source_url'])

def main():
	parser = ArghParser()
	parser.add_commands([list_images, upload_image])
	parser.dispatch()

if __name__ == "__main__":
	main()
```

This modified script allows uploading both normal image and its @2K version in one go. The `upload_image` function now takes two file paths, one for the normal image and another for the @2K image. To use the new version of the script, pass both `-n` and `-k` options with the respective file paths:

```sh
python wp_images.py upload_image -n /path/to/normal/image.jpg -k /path/to/2k/image.jpg
```
