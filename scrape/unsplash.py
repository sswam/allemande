#!/usr/bin/env python3
import requests
import os
import argh
from slugify import slugify

class Unsplash:
    def __init__(self, query, dir=None, per_page=20, quality="raw"):
        self.query = query
        self.per_page = per_page
        #self.page = 0
        self.quality = quality
        self.headers ={"Accept": "*/*", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US,en;q=0.5", "Connection": "keep-alive", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}
    
    def set_url(self):
        return f"https://unsplash.com/napi/search?query={self.query}&per_page={self.per_page}"

    def make_request(self):
        url = self.set_url()
        return requests.request("GET",url,headers=self.headers)

    def get_data(self):
        self.data = self.make_request().json()

    def save_path(self,name):
        download_dir = slugify(self.query)
        if not os.path.exists(download_dir):
            os.mkdir(download_dir)
        return f"{os.path.join(os.path.realpath(os.getcwd()),download_dir,name)}.jpg"

    def download(self,url,name):
        filepath = self.save_path(name)
        with open(filepath,"wb") as f:
            f.write(requests.request("GET",url,headers=self.headers).content)

    def Scraper(self,pages):
        for page in range(0,pages+1):
            self.make_request()
            self.get_data()
            for item in self.data['photos']['results']:
                name = item['id']
                url = item['urls'][self.quality]
                print(url)
                self.download(url,name)
            #self.pages += 1

@argh.arg("query",help="Unsplash search query")
@argh.arg("-p","--per_page",help="Number of images to download")
@argh.arg("-q","--quality",help="Image quality")
@argh.arg("-n","--pages",help="Number of pages to scrape")
@argh.arg("-d","--dir",help="Directory to save images")
def unsplash_get(query, dir=None, per_page=20, quality="raw", pages=1):
    scraper = Unsplash(query, per_page=per_page, quality=quality)
    scraper.Scraper(pages)

if __name__ == "__main__":
    argh.dispatch_command(unsplash_get)
