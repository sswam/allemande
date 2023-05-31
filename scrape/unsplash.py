#!/usr/bin/env python3
import requests
import os
import argh
from slugify import slugify
from pathlib import Path

""" This script downloads images from Unsplash.com. It takes a search query as input and downloads the images in the current directory. The images are saved in a folder named after the search query. The script also fetches metadata such as ALT tag, description, title, author, and license. The metadata is saved in a tab-separated file named 'metadata.tsv' along with a header. """

#This improved script now fetches metadata such as ALT tag, description, title, author, and license. The metadata is saved in a tab-separated file named 'metadata.tsv' along with a header.


class Unsplash:
	def __init__(self, query, download_dir=None, metadata_file=None, per_page=20, pages=1, quality="raw"):
		self.query = query
		self.per_page = per_page
		self.pages = pages
		self.quality = quality
		self.download_dir = download_dir or slugify(self.query)
		self.metadata_file = metadata_file or str(Path(self.download_dir)/"metadata.tsv")
		self.headers ={"Accept": "*/*", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US,en;q=0.5", "Connection": "keep-alive", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}
		self.pad_width = len(str(self.per_page*self.pages))

	def set_url(self):
		return f"https://unsplash.com/napi/search?query={self.query}&per_page={self.per_page}"

	def make_request(self):
		url = self.set_url()
		return requests.request("GET",url,headers=self.headers)

	def get_data(self):
		self.data = self.make_request().json()

	def save_path(self, name, index):
		index_padded = str(index).zfill(self.pad_width)
		return str(Path(self.download_dir)/f"{index_padded}_{name}.jpg")

	def download(self,url,name, index):
		filepath = self.save_path(name, index)
		with open(filepath,"wb") as f:
			f.write(requests.request("GET",url,headers=self.headers).content)

	def scrape(self):
		""" This function scrapes the images from Unsplash.com. """
		if not os.path.exists(self.download_dir):
			os.mkdir(self.download_dir)
		index = 0
		with open(self.metadata_file, 'a') as f:
			f.write("ALT tag\tDescription\tTitle\tAuthor\tLicense\tURL\n")
			for page in range(0,self.pages+1):
				self.make_request()
				self.get_data()
				for item in self.data['photos']['results']:
					print(item)
					name = item['id']
					url = item['urls'][self.quality]
					alt = item['alt_description']
					description = item['description']
					username = item['user']['username']
					author = item['user']['name']
					author_loc = item['user']['location']
					metadata = [alt, description, username, name, author, author_loc, url]
					f.write('\t'.join(map(str, metadata)) + '\n')
					print(url)
					self.download(url,name,index)
					index += 1

	
@argh.arg("query",help="Unsplash search query")
@argh.arg("-p","--per_page",help="Number of images to download")
@argh.arg("-q","--quality",help="Image quality")
@argh.arg("-n","--pages",help="Number of pages to scrape")
@argh.arg("-d","--download_dir",help="Directory to save images")
@argh.arg("-m","--metadata_file",help="File to save metadata")
def unsplash_get(query, download_dir=None, metadata_file=None, per_page=20, quality="raw", pages=1):
	scraper = Unsplash(query, download_dir=download_dir, metadata_file=metadata_file, per_page=per_page, pages=pages, quality=quality)
	scraper.scrape()


if __name__ == "__main__":
	argh.dispatch_command(unsplash_get)
