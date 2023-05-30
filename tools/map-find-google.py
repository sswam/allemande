#!/usr/bin/env python3
""" map-find-goog.py:	Search for a location using Google Maps API """

import sys
import os
import requests
import argh
import logging
import urllib.parse
import sh

logger = logging.getLogger(__name__)

@argh.arg("query", help="Location to search for")
@argh.arg("-k", "--api-key", help="Google Maps API key")
@argh.arg("-t", "--timeout", help="Request timeout")
@argh.arg("-b", "--browse", help="Browse to the location in the default browser")
@argh.arg("-B", "--browser", help="Specify the browser to use")
@argh.arg("-f", "--fork", help="Run the browser in the background")
def search_location(query, api_key="$GOOGLE_MAPS_API_KEY", timeout=10, browse=False, browser=None, fork=True):
	""" Search for a location using Google Maps API """
	logger.info("Searching for place: %s", query)

	if browser:
		browse = True
	elif browse and not browser:
		browser = "xdg-open"

	if api_key.startswith("$"):
		api_key = os.environ.get(api_key[1:])

	url = "https://maps.googleapis.com/maps/api/geocode/json"
	params = {
		"address": query,
		"key": api_key
	}

	response = requests.get(url, params=params, timeout=timeout)
	data = response.json()

	if not data["results"]:
		return None, None, None

	result = data["results"][0]
	loc = result["geometry"]["location"]
	lat, lon = (loc["lat"], loc["lng"])
	address = result["formatted_address"]
	# urlencode properly
	query_enc = urllib.parse.quote_plus(query)
	url = f"https://www.google.com/maps/search/?api=1&query={query_enc}&center={lat},{lon}"

	if browse and (not fork or os.fork() == 0):
		sh.Command(browser)(url)
		if fork:
			sys.exit(0)

	return lat, lon, address, url

if __name__ == "__main__":
	argh.dispatch_command(search_location)
