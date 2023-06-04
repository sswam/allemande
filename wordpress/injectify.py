#!/usr/bin/env python3 

""" wp.py: Create, read, update or delete a wordpress page or post """

import os
import requests
import argh
import json
import logging
import base64
from ucm_slugify import slugify


# TODO look for an existing Python API to wordpress, I'm sure there is one!
# wordpress-api:
# - https://pypi.org/project/wordpress-api/
# - https://github.com/d3v-null/wp-api-python

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

site_url=os.environ["WORDPRESS_SITE_URL"]
username=os.environ["WORDPRESS_USERNAME"]
password=os.environ["WORDPRESS_APP_PASSWORD"]

headers = {
	"Authorization": f"Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}"
}

def endpoint(type):
	""" Return the endpoint for the given type """
	return "pages" if type == "page" else "posts"


def find_by_title(title_to_find, type="post", many=False):
	""" Find a post or page by title """
	global site_url, username, password, headers
	url = f"{site_url}/wp-json/wp/v2/{endpoint(type)}"
	params = {
		'search': title_to_find,
		'per_page': 1
	}
	r = requests.get(url, headers=headers, params=params)
	items = r.json()
	if many:
		return items
	if not items:
		return None
	if len(items) > 1:
		raise Exception(f"More than one {type} found with title, and many=False: {title_to_find}")
	return items[0]

def find_by_id(id_to_find, type="post"):
	""" Find a post or page by ID """
	global site_url, username, password, headers
	url = f"{site_url}/wp-json/wp/v2/{endpoint(type)}/{id_to_find}"
	r = requests.get(url, headers=headers)
	item = r.json()
	return item


def find_by_slug(slug_to_find, type="post"):
	""" Find a post or page by slug """
	global site_url, username, password, headers
	url = f"{site_url}/wp-json/wp/v2/{endpoint(type)}"
	params = {
	    'slug': slug_to_find,
	    'per_page': 1
	}
	r = requests.get(url, headers=headers, params=params)
	items = r.json()
	return items


def update_item(type, title, content, status):
	""" Update a post """
	global site_url, username, password, headers
	data = {
		'content': content
	}
	url = f"{site_url}/wp-json/wp/v2/{endpoint(type)}"
	update_url = f"{url}/{post_id}"
	update_r = requests.post(update_url, headers=headers, json=data)

	if update_r.status_code == 200:
		logger.info(f"Updated {type} successfully!")
	else:
		raise Exception(f"Could not update {type}")


def create_item(type, title, content, status="draft", id=None, slug=None):
	""" Create a post or page """
	global site_url, username, password, headers

	# Set up the payload to send to WordPress

	payload = {
		"content": html_content,
		"title": title,
		"status": status,
		"id": id,
		"slug": slug,
	}

	# Send the post request to create a new page, passing the payload and authorization

	response = requests.post(api_url, json=payload, auth=auth)

	# Check if the request was successful
	if response.status_code == 201:  # 201 is the status code for 'Created'
		logger.info(f"Created {type} successfully!")
	else:
		raise Exception(f"Could not create {type}")


def read_item(type, title, content, status, id, slug):
	""" Read a post or page """
	global site_url, username, password, headers
	url = f"{site_url}/wp-json/wp/v2/{endpoint(type)}"
	r = requests.get(url, headers=headers)
	item = r.json()
	return item


# TODO CRUD boilerplate for any apppliation,
# or use this as inspiration for a more generic CRUD tool
# or for AI to create other CRUD tools.


# TODO move up
def setup(type, username, password, headers):
	endpoint = endpoint(type)
	auth = requests.auth.HTTPBasicAuth(username, password, headers)
	return endpoint, auth


@argh.arg("--file", "-f", help="file to upload")
@argh.arg("--content", "-C", help="content to upload")
@argh.arg("--title", "-t", help="Title of the item")
@argh.arg("--status", "-s", help="Status (draft, publish, private)")
@argh.arg("--post", "-p", help="Item is a post (default)")
@argh.arg("--page", "-P", help="Item is a page")
@argh.arg("--type", "-T", help="Type of the item (post, page)")
@argh.arg("--id", "-I", help="ID of the item")
@argh.arg("--slug", "-S", help="Slug of the item")
@argh.arg("--auto", "-a", help="Auto-detect the mode (add, update, delete)")
@argh.arg("--create", "-c", help="Create the item")
@argh.arg("--read", "-r", help="Read the item")
@argh.arg("--update", "-u", help="Update the item")
@argh.arg("--delete", "-d", help="Delete the item")
@argh.arg("--force", "-F", help="Force the action")
def crud(file=None, content=None, title=None, status="draft", post=False, page=False,
		type=None, id=None, slug=None, auto=False,
		create=False, read=False, update=False, force=False, delete=False):
	""" Create, update or delete a wordpress page or post """

	# type, post, and page

	if type and type not in ["post", "page"]:
		raise Exception("Specify a type (post or page)")

	if type == "post":
		post = True
	if type == "page":
		page = True

	if post + page > 1:
		raise Exception("Specify only one of --post or --page")

	if post:
		type = "post"
	elif page:
		type = "page"
	else:
		logger.warning("No type specified, assuming --post")
		post = True

	# other options

	if auto + create + read + update + delete != 1:
		raise Exception("Specify one of --auto, --create, --read, --update, --delete")

	if file and content:
		raise Exception("You may not specify both --file and --content")

	if file:
		content = open(file, encoding="utf-8").read()

	if (content and read) and not force:
		raise Exception("You may not specify both --content and --read")


	# look for an existing item, by id, slug, or title

	if id:
		item = find_by_id(id, type)
	elif slug:
		item = find_by_slug(slug, type)
	elif title:
		item = find_by_title(title, type)
	else:
		raise Exception("You must specify an id, slug or title")


	# check for conflicts with the item

	need_existing = (read or update or delete) and not force

	need_nonexisting = create and not force

	if need_existing and not item:
		raise Exception("Item not found")

	if need_nonexisting and item:
		raise Exception("Item already exists")


	# force the action

	if create and item:
		create = False
		update = True

	if update and not item:
		create = True
		update = False

	if delete and not item:
		return

	if auto and not content:
		delete = True


	# Get title from first line, if not provided

	if not title:
		title = html_content.split("\n")[0]
		title = re.sub("<.*?>", "", title)
		title = re.sub("Title: ", "")

	# Get slug from title, if not provided

	if not slug:
		slug = slugify(title)

	key = {
		"title": title,
		"id": id,
		"slug": slug,
	}

	# operations
	# TODO 
	# - list all pages
	# - search for pages by title keyword
	# TODO sync

	if create:
		return create_item(type, title, content, status, id, slug)
	elif read:
		return read_item(type, title, content, status, id, slug)
	elif update:
		return update_item(type, title, content, status, type)
	elif delete:
		return delete_item(item, content, title, status, type, endpoint, auth)
	else:
		raise Exception("Internal error: no operation found")


if __name__ == "__main__":
	argh.dispatch_command(crud)
