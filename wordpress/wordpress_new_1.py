#!/usr/bin/env python3 

""" wordpress_put.py: Create a new page or post in WordPress from an HTML file, or update an existing page by title """

import os
import requests
import argh

# TODO look for an existing Python API to wordpress, I'm sure there is one!
# wordpress-api:
# - https://pypi.org/project/wordpress-api/
# - https://github.com/d3v-null/wp-api-python

site_url=os.environ["WORDPRESS_SITE_URL"]
username=os.environ["WORDPRESS_USERNAME"]
app_password=os.environ["WORDPRESS_APP_PASSWORD"]

def endpoint(type):
	return "pages" if type == "page" else "posts"

# Find the post by its title
def find_by_title(title_to_find, type="post"):
	url = f"{site_url}/wp-json/wp/v2/{endpoint(type)}"
	params = {
	    'search': title_to_find,
	    'per_page': 1
	}
	r = requests.get(url, headers=headers, params=params)
	items = r.json()
	return items

def find_by_title_one(title_to_find, type="post"):
	return find_by_title(title_to_find, type)[0]

if len(posts) > 0:
    post = posts[0]
    post_id = post['id']
    print(f"Post found with ID: {post_id}")

    # Update the existing post
    new_content = "Your new content goes here"
    data = {
        'content': new_content
    }
    update_url = f"{url}/{post_id}"
    update_r = requests.post(update_url, headers=headers, json=data)

    if update_r.status_code == 200:
        print("Post updated successfully!")
    else:
        print("Could not update the post.")
else:
    print("No post found with that title.")


@argh.arg("html_file", help="HTML file to upload")
@argh.arg("--title", help="Title of the item")
@argh.arg("--status", help="Status of the item (draft, publish, private)")
@argh.arg("--type", help="Type of the item (post, page)")
def add_or_update(html_file, title=None, status="draft", type="post"):
	""" Create a new page or post in WordPress from an HTML file """

	type_tc = type.title()

	# Full API endpoint for creating posts or pages
	api_url = f"{site_url}/wp-json/wp/v2/{endpoint(type)}"

	# Set up the HTTP Basic Auth object
	auth = requests.auth.HTTPBasicAuth(username, app_password)

	# Load the HTML file
	with open(html_file, "r") as file:
		html_content = file.read()

	# Get title from first line, if not provided
	if not title:
		title = html_content.split("\n")[0]
		title = title.replacer("<.*?>", "")
		title = title.replacer("Title: ", "")

	# Set up the payload to send to WordPress, including your content
	payload = {
		"content": html_content,
		"title": title,
		"status": status,
	}

	# Send the post request to create a new page, passing the payload and authorization
	response = requests.post(api_url, json=payload, auth=auth)

	# Check if the request was successful
	if response.status_code == 201:  # 201 is the status code for 'Created'
		print(f"{type_tc} created successfully!")
	else:
		print(f"There was an error creating the {type}:", response.text)

if __name__ == "__main__":
	argh.dispatch_command(wordpress_add)
