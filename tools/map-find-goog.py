#!/usr/bin/env python3
""" map-find-goog.py:	Search for a location using Google Maps API """

import os
import requests
import argh

def search_location(location, api_key=os.environ.get("GOOGLE_MAPS_API_KEY"), timeout=10):
	""" Search for a location using Google Maps API """
	url = "https://maps.googleapis.com/maps/api/geocode/json"
	params = {
		"address": location,
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
	return lat, lon, address

if __name__ == "__main__":
	argh.dispatch_command(search_location)
