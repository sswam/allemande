#!/usr/bin/env python3 

import os
import requests
import argh

# TODO look for an existing Python API to wordpress, I'm sure there is one!
# wordpress-api:
# - https://pypi.org/project/wordpress-api/
# - https://github.com/d3v-null/wp-api-python

@argh.arg("html_file", help="HTML file to upload")
@argh.arg("--title", help="Title of the page")
@argh.arg("--status", help="Status of the page (draft, publish, private)")
@argh.arg("--type", help="Type of the page (page, post)")
@argh.arg("--site-url", help="URL of the WordPress site")
@argh.arg("--username", help="Username for the WordPress site")
@argh.arg("--app-password", help="Application password for the WordPress site")
def wordpress_add(
	html_file, title=None, status="draft", type="page",
	site_url=os.environ.get("WORDPRESS_SITE_URL"),
	username=os.environ.get("WORDPRESS_USERNAME"),
	app_password=os.environ.get("WORDPRESS_APP_PASSWORD"),
):
	""" Create a new page or post in WordPress from an HTML file """

	type_tc = type.title()

	# Full API endpoint for creating pages or posts
	endpoint = "pages" if type == "page" else "posts"
	api_url = f"{site_url}/wp-json/wp/v2/{endpoint}"

	# Set up the HTTP Basic Auth object
	auth = requests.auth.HTTPBasicAuth(username, app_password)

	# Load the HTML file
	with open(html_file, "r") as file:
		html_content = file.read()

	# Get title from first line of page, if not provided
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
