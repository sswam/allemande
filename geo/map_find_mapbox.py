#!/usr/bin/env python3-allemande
""" map-find-mapbox:	Search for a location using Mapbox API """

import os
import requests
import argh

def search_location(location, access_token=os.environ.get("MAPBOX_API_KEY"), timeout=10):
	""" Search for a location using Mapbox API """
	url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{location}.json"
	params = {
		"access_token": access_token,
		"limit": 1
	}

	response = requests.get(url, params=params, timeout=timeout)
	data = response.json()

	if not data["features"]:
		return None, None, None

	feature = data["features"][0]
	lon, lat = feature["geometry"]["coordinates"]
	address = feature["place_name"]
	return lat, lon, address

if __name__ == "__main__":
	argh.dispatch_command(search_location)
