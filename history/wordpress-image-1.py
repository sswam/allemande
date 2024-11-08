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

def upload_image(api_url, username, password, file_path):
	""" Upload an image to the WordPress Media Library """
	client = Client(api_url, username, password)

	with open(file_path, 'rb') as file:
		response = client.upload_media(file)

	print('Image uploaded:', response['source_url'])

def main():
	parser = ArghParser()
	parser.add_commands([list_images, upload_image])
	parser.dispatch()

if __name__ == "__main__":
	main()
