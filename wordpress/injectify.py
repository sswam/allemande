#!/usr/bin/env python3 

""" injectify.py: Create, read, update or delete a wordpress page or post """

import os
import requests
import argh
import json
import logging
import base64
import slugify  # mine, not the broken old unmaintained one in PyPI


# TODO look for an existing Python API to wordpress, I'm sure there is one!
# wordpress-api:
# - https://pypi.org/project/wordpress-api/
# - https://github.com/d3v-null/wp-api-python

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

site_url = os.environ["WORDPRESS_SITE_URL"]
username = os.environ["WORDPRESS_USERNAME"]
password = os.environ["WORDPRESS_APP_PASSWORD"]
auth = requests.auth.HTTPBasicAuth(username, password)

api_url = f"{site_url}/wp-json/wp/v2"


def endpoint(item_type):
	""" Return the endpoint for the given item_type """
	return "pages" if item_type == "page" else "posts"


def get_api_url(item_type, path=""):
	""" Return the API URL for the given item_type """
	if path and not path.startswith("/"):
		path = f"/{path}"
	return f"{site_url}/wp-json/wp/v2/{endpoint(item_type)}{path}"

def find_by_title(title_to_find, item_type="post", many=False):
	""" Find a post or page by title """
	global api_url, username, password, auth
	url = get_api_url(item_type)
	params = {
		'search': title_to_find,
		'per_page': 1
	}
	response = requests.get(url, auth=auth, params=params)
	items = response.json()
	if many:
		return items
	if not items:
		return None
	if len(items) > 1:
		raise Exception(f"More than one {item_type} found with title, and many=False: {title_to_find}")
	return items[0]

def find_by_id(id_to_find, item_type="post"):
	""" Find a post or page by ID """
	global api_url, username, password, auth
	url = get_api_url(item_type, id_to_find)
	response = requests.get(url, auth=auth)
	item = response.json()
	return item


def find_by_slug(slug_to_find, item_type="post"):
	""" Find a post or page by slug """
	global api_url, username, password, auth
	url = get_api_url(item_type)
	params = {
		'slug': slug_to_find,
		'per_page': 1
	}
	reponse = requests.get(url, auth=auth, params=params)
	items = reponse.json()
	return items


def get_item_key(item):
	key = {
		"id": item["id"],
		"slug": item["slug"],
		"title": item["title"],
		"status": item["status"],
	}
	return key


def create_item(item_type, item, content, status="draft"):
	""" Create a post or page """
	global api_url, username, password, auth
	url = get_api_url(item_type)
	data = {
		"content": content,
		"slug": item["slug"],
		"title": item["title"],
		"status": status,
	}
	response = requests.post(url, auth=auth, json=data)
	if response.status_code == 201:  # 201 is the status code for 'Created'
		logger.info(f"Created {item_type} successfully!")
	else:
		raise Exception(f"Could not create {item_type}")
	item = response.json()
	return get_item_key(item)


def read_item(item_type, item, meta=False):
	""" Read a post or page """
	global api_url, username, password, auth
	id = item["id"]
	url = f"{site_url}/wp-json/wp/v2/{endpoint(item_type)}/{id}"
	response = requests.get(url, auth=auth)
	if response.status_code == 404:
		logger.error(f"Could not find {item_type} with id {id}")
		return None
	item = response.json()
	if not meta:
		item = item["content"]["rendered"]
	return item


def update_item(item_type, item, content, status):
	""" Update a post """
	global api_url, username, password, auth
	url = get_api_url(item_type, item["id"])
	data = {
		'content': content
	}
	response = requests.post(url, auth=auth, json=data)
	if response.status_code == 200:
		logger.info(f"Updated {item_type} successfully!")
	else:
		raise Exception(f"Could not update {item_type}")
	item = response.json()
	return get_item_key(item)


def delete_item(item_type, item):
	""" Delete a post or page """
	global api_url, username, password, auth
	id = item["id"]
	url = f"{site_url}/wp-json/wp/v2/{endpoint(item_type)}/{id}"
	response = requests.delete(url, auth=auth)
	if response.status_code == 200:
		logger.info(f"Deleted {item_type} successfully!")
	else:
		raise Exception(f"Could not delete {item_type}")
	item = response.json()
	return get_item_key(item)


def list_items(item_type, status="draft"):
	""" List posts or pages """
	global api_url, username, password, auth
	url = get_api_url(item_type)
	items = []
	page = 1
	while True:
		params = {
			'per_page': 100,
			'orderby': 'date',
			'order': 'asc',
			'page': page,
			'_fields': 'id,slug,title,status'
		}
		if status is not None:
			params["status"] = status
		response = requests.get(url, auth=auth, params=params)
		try:
			page_items = response.json()
		except json.decoder.JSONDecodeError:
			break
		items += page_items
		if len(page_items) < 100:
			break
	keys = []
	for item in items:
		keys.append(get_item_key(item))
	return keys


# TODO CRUD boilerplate for any apppliation,
# or use this as inspiration for a more generic CRUD tool
# or for AI to create other CRUD tools.


@argh.arg("--file", "-f", help="file to upload")
@argh.arg("--content", "-C", help="content to upload")
@argh.arg("--title", "-t", help="Title of the item")
@argh.arg("--status", "-s", help="Status (draft, publish, private)")
@argh.arg("--post", "-p", help="Item is a post (default)")
@argh.arg("--page", "-P", help="Item is a page")
@argh.arg("--item_type", "-T", help="item_type of the item (post, page)")
@argh.arg("--id", "-I", help="ID of the item")
@argh.arg("--slug", "-S", help="Slug of the item")
@argh.arg("--auto", "-a", help="Auto-detect the mode (add, update, delete)")
@argh.arg("--create", "-c", help="Create the item")
@argh.arg("--read", "-r", help="Read the item")
@argh.arg("--update", "-u", help="Update the item")
@argh.arg("--delete", "-d", help="Delete the item")
@argh.arg("--list", "-l", help="List items")
@argh.arg("--meta", "-m", help="When reading the item, include metadata")
@argh.arg("--force", "-F", help="Force the action")
def crud(file=None, content=None, title=None, status="draft", post=False, page=False,
		item_type=None, id=None, slug=None, auto=False,
		create=False, read=False, update=False, delete=False, list=False, meta=False, force=False):
	""" Create, update or delete a wordpress page or post """

	# item_type, post, and page

	if item_type and item_type not in ["post", "page"]:
		raise Exception("Specify a item_type (post or page)")

	if item_type == "post":
		post = True
	if item_type == "page":
		page = True

	if post + page > 1:
		raise Exception("Specify only one of --post or --page")

	if post:
		item_type = "post"
	elif page:
		item_type = "page"
	else:
		logger.warning("No item_type specified, assuming --post")
		post = True

	# other options

	if auto + create + read + update + delete + list != 1:
		raise Exception("Specify one of --auto, --create, --read, --update, --delete, --list")

	if file and content:
		raise Exception("You may not specify both --file and --content")

	if file:
		content = open(file, encoding="utf-8").read()

	if (content and (read or list or delete)) and not force:
		raise Exception("You may not specify --content with this command")

	if meta and not read:
		raise Exception("You may not specify --meta without --read")


	# look for an existing item, by id, slug, or title

	if id:
		item = find_by_id(id, item_type)
	elif slug:
		item = find_by_slug(slug, item_type)
	elif title:
		item = find_by_title(title, item_type)
	elif list:
		item = None
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

	if title is None and content:
		title = content.split("\n")[0]
		title = re.sub("<.*?>", "", title)
		title = re.sub("Title: ", "")

	# Get slug from title, if not provided

	if not slug and title:
		slug = slugify.slugify(title)

	item = item or {
		"id": id,
		"slug": slug,
		"title": title,
	}

	# operations
	# TODO 
	# - list all pages
	# - search for pages by title keyword
	# TODO sync

	if title is not None:
		item["title"] = title

	if create:
		return create_item(item_type, item, content, status)
	elif read:
		rv = read_item(item_type, item, meta=meta)
		if isinstance(rv, dict):
			rv = json.dumps(rv, indent=4)
		return rv
	elif update:
		return update_item(item_type, item, content, status)
	elif delete:
		return delete_item(item_type, item)
	elif list:
		return list_items(item_type, status)
	else:
		raise Exception("Internal error: no operation found")


if __name__ == "__main__":
	argh.dispatch_command(crud)
