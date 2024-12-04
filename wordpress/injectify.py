#!/usr/bin/env python3 

""" injectify.py: Create, read, update or delete a wordpress page or post """

import os
import requests
import argh
import json
import logging
import base64
import slug


# TODO look for an existing Python API to wordpress, I'm sure there is one!
# wordpress-api:
# - https://pypi.org/project/wordpress-api/
# - https://github.com/d3v-null/wp-api-python

# XXX deleting by title does not work

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
	path = str(path)
	if path and not path.startswith("/"):
		path = f"/{path}"
	return f"{site_url}/wp-json/wp/v2/{endpoint(item_type)}{path}"


def find_by_id(id, item_type="post"):
	""" Find a post or page by ID """
	global api_url, username, password, auth
	url = get_api_url(item_type, id)
	response = requests.get(url, auth=auth)
	item = response.json()
	return item


def find_by_slug(slug, item_type="post", status=None, many=False, underscore_to_hyphen=False):
	""" Find a post or page by slug """
	global api_url, username, password, auth
	if status is None:
		return find_by_slug(slug, item_type, "publish", many=many, underscore_to_hyphen=underscore_to_hyphen) or \
			find_by_slug(slug, item_type, "draft", many=many, underscore_to_hyphen=underscore_to_hyphen)
	url = get_api_url(item_type)
	if underscore_to_hyphen:
		slug = slug.slug(slug, lower=True)
	params = {
		'slug': slug,
		'per_page': 1,
	}
	if status:
		params['status'] = status
	reponse = requests.get(url, auth=auth, params=params)
	items = reponse.json()
	return items_check_number(items, "slug", slug, many=many)


def find_by_title(title, item_type="post", status=None, many=False):
	""" Find a post or page by title """
	global api_url, username, password, auth
	url = get_api_url(item_type)
	params = {
		'search': title,
		'per_page': 1,
	}
	if status:
		params['status'] = status
	response = requests.get(url, auth=auth, params=params)
	items = response.json()
	return items_check_number(items, "title", title, many=many)


def items_check_number(items, key, value, many=False):
	if many:
		return items
	if not items:
		return None
	if len(items) > 1:
		raise Exception(f"More than one {item_type} found with {key}, and many=False: {value}")
	return items[0]


def get_item_key(item):
	key = {
		"id": item["id"],
		"slug": item["slug"],
		"title": item["title"],
		"status": item["status"],
	}
	return key


def create_item(item_type, item, content, status="draft", media=None):
	""" Create a post or page """
	global api_url, username, password, auth
	url = get_api_url(item_type)
	data = {
		"content": content,
		"slug": item["slug"],
		"title": item["title"],
		"status": status or "draft",
	}
	response = requests.post(url, auth=auth, json=data)
	if response.status_code == 201:  # 201 is the status code for 'Created'
		logger.info(f"Created {item_type} successfully!")
	else:
		raise Exception(f"Could not create {item_type}")
	item = response.json()
	set_featured_media(item_type, item, media)
	return get_item_key(item)


def read_item(item_type, item, meta=False, raw=True):
	""" Read a post or page """
	global api_url, username, password, auth
	id = item["id"]
	data = {
		"context": "edit" if raw else "display",
	}
	url = f"{site_url}/wp-json/wp/v2/{endpoint(item_type)}/{id}"
	response = requests.get(url, auth=auth, params=data)
	if response.status_code == 404:
		logger.error(f"Could not find {item_type} with id {id}")
		return None
	item = response.json()
	if not meta:
		item = item["content"]
		if raw:
			item = item["raw"]
		else:
			item = item["rendered"]
	return item


def update_item(item_type, item, content, status=None, media=None):
	""" Update a post """
	global api_url, username, password, auth
	url = get_api_url(item_type, item["id"])
	data = {
		'content': content
	}
	if "slug" in item:
		data["slug"] = item["slug"]
	if status:
		data['status'] = status
	response = requests.post(url, auth=auth, json=data)
	if response.status_code == 200:
		logger.info(f"Updated {item_type} successfully!")
	else:
		raise Exception(f"Could not update {item_type}")
	item = response.json()
	set_featured_media(item_type, item, media)
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


def undelete_item(item_type, item_id):
	""" Undelete a post or page """
	raise Exception("Not implemented")  # TODO
	global api_url, username, password, auth
	url = f"{site_url}/wp-json/wp/v2/{endpoint(item_type)}/{item_id}/revisions"
	response = requests.get(url, auth=auth)

	if response.status_code != 200:
		raise Exception(f"Could not retrieve revisions for {item_type}")

	revisions = response.json()
	if not revisions:
		raise Exception(f"No revisions found for {item_type} with id {item_id}")

	restore_revision_url = f"{site_url}/wp-json/wp/v2/{endpoint(item_type)}/{item_id}/revisions/{revisions[0]['id']}"
	restore_response = requests.post(restore_revision_url, auth=auth)

	if restore_response.status_code != 200:
		raise Exception(f"Could not undelete {item_type}")

	logger.info(f"Undeleted {item_type} successfully!")
	item = restore_response.json()
	return get_item_key(item)


def list_items(item_type, status="draft", start_page=1, limit=None):
	""" List posts or pages """
	global api_url, username, password, auth
	url = get_api_url(item_type)
	items = []
	page = start_page
	while True:
		params = {
			'per_page': 100,
			'orderby': 'date',
			'order': 'asc',
			'page': page,
			'_fields': 'id,slug,title,status',
		}
		if status is not None:
			params["status"] = status
		response = requests.get(url, auth=auth, params=params)
		try:
			page_items = response.json()
		except json.decoder.JSONDecodeError:
			break
		items += page_items
		if len(page_items) < 100 or len(items) >= limit:
			break
	keys = []
	for item in items:
		keys.append(get_item_key(item))
	return keys


def set_featured_media(item_type, item, media):
	""" Set featured media """
	global api_url, username, password, auth
	if media is None:
		return
	url = get_api_url(item_type, item["id"])
	data = {
		'featured_media': int(media),
	}
	response = requests.post(url, auth=auth, json=data)
	if response.status_code == 200:
		logger.info(f"Set featured media to {media}")
	else:
		raise Exception(f"Could not set featured media {media}: {response}")
	# item = response.json()
	# return get_item_key(item)
	return response


def get_featured_media(item_type, item):
	""" Get featured media """
	global api_url, username, password, auth
	url = get_api_url(item_type, item["id"])
	params = {
		'_fields': 'featured_media',
	}
	response = requests.get(url, auth=auth, params=params)
	if response.status_code == 200:
		logger.info(f"Get featured media")
	else:
		raise Exception(f"Could not get featured media {media}: {response}")
	item = response.json()
	media = item.get("featured_media")
	return media


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
@argh.arg("--undelete", "-U", help="Undelete the item")
@argh.arg("--list", "-l", help="List items")
@argh.arg("--meta", "-m", help="When reading the item, include metadata")
@argh.arg("--force", "-F", help="Force the action")
@argh.arg("--media", "-M", help="Set featured media ID")
@argh.arg("--media-default", "-D", help="Set default featured media ID")
@argh.arg("--underscore-to-hyphen", "-H", help="Search for slugs with underscore and convert to the given slug")
def crud(file=None, content=None, title=None, status=None, post=False, page=False,
		item_type=None, id=None, slug=None, auto=False,
		create=False, read=False, update=False, delete=False, undelete=False,
		list=False, meta=False, force=False, media=None, media_default=None, underscore_to_hyphen=False):
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
		item_type = "post"
		post = True

	# other options

	if media:
		pass
	elif auto + create + read + update + delete + undelete + list != 1:
		raise Exception("Specify one of --auto, --create, --read, --update, --delete, --undelete, --list, --media")

	if file and content:
		raise Exception("You may not specify both --file and --content")

	if file:
		content = open(file, encoding="utf-8").read()

	if (content and (read or list or delete or undelete)) and not force:
		raise Exception("You may not specify --content with this command")

	if meta and not read:
		raise Exception("You may not specify --meta without --read")


	# look for an existing item, by id, slug, or title

	if id:
		item = find_by_id(id, item_type)
	elif slug:
		item = find_by_slug(slug, item_type, status=status, underscore_to_hyphen=underscore_to_hyphen)  # status
	elif title:
		item = find_by_title(title, item_type, status=status)
	elif list:
		item = None
	else:
		raise Exception("You must specify an id, slug or title")


	# get featured media for existing item
	if item and not media:
		media = get_featured_media("post", item)
		print("media ID old:", media)
	if item and not media:
		media = media_default


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
		logger.error("No content, but will not delete.")
		return
	elif auto and item:
		update = True
	elif auto:
		create = True


	# Get status from item if possible TODO
	if item:
		status = item.get("status") or "draft"

	# Get title from first line, if not provided

	if title is None and content:
		title = content.split("\n")[0]
		title = re.sub("<.*?>", "", title)
		title = re.sub("Title: ", "")

	# Get slug from title, if not provided

	if not slug and title:
		slug = slug.slug(title, lower=True, hyphen=True)


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
		return create_item(item_type, item, content, status, media=media)
	elif read:
		rv = read_item(item_type, item, meta=meta)
		# it might be nice if argh returned JSON by default
		if isinstance(rv, dict):
			rv = json.dumps(rv, indent=4)
		return rv
	elif update:
		if slug:
			item["slug"] = slug
		return update_item(item_type, item, content, media=media, status=status)
	elif delete:
		return delete_item(item_type, item)
	elif undelete:
		return undelete_item(item_type, item)
	elif list:
		return list_items(item_type, status)
	elif media:
		set_featured_media(item_type, item, media)
	else:
		raise Exception("Internal error: no operation found")


if __name__ == "__main__":
	argh.dispatch_command(crud)
