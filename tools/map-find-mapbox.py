#!/usr/bin/env python3
# map-find.py:	Search for a location using Mapbox API
import os
import requests
import argh

def search_location(location, access_token=os.environ.get("MAPBOX_API_KEY")):
	url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{location}.json"
	params = {
		"access_token": access_token,
		"limit": 1
	}

	response = requests.get(url, params=params)
	data = response.json()

	if data["features"]:
		feature = data["features"][0]
		lon, lat = feature["geometry"]["coordinates"]
		address = feature["place_name"]
		return lat, lon, address
	else:
		return None, None, None

if __name__ == "__main__":
	argh.dispatch_command(search_location)
