#!/usr/bin/env python3
# map-find.py:	Search for a location using Google Maps API
import os
import requests
import argh

def search_location(location, api_key=os.environ.get("GOOGLE_MAPS_API_KEY")):
	url = "https://maps.googleapis.com/maps/api/geocode/json"
	params = {
		"address": location,
		"key": api_key
	}

	response = requests.get(url, params=params)
	data = response.json()

	if data["results"]:
		result = data["results"][0]
		lat, lon = (result["geometry"]["location"]["lat"],
					result["geometry"]["location"]["lng"])
		address = result["formatted_address"]
		return lat, lon, address
	else:
		return None, None, None

if __name__ == "__main__":
	argh.dispatch_command(search_location)
