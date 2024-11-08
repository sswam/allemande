#!/usr/bin/env python3-allemande
""" img2img.py: Convert an image to another image using the img2img API """

import sys
import os
import base64
import json
import cv2
import requests
import argh
import logging

logger = logging.getLogger(__name__)

@argh.arg("image_path", help="Path to the input image")
@argh.arg("-k", "--api-key", help="Access key for img2img API")
@argh.arg("-m", "--model-type", help="Model type for img2img API")
@argh.arg("-p", "--prompt", help="Prompt for the img2img API")
@argh.arg("-n", "--neg-prompt", help="Negative prompt for the img2img API")
@argh.arg("-c", "--cfg", help="Configuration for the img2img API")
@argh.arg("-f", "--factor", help="Factor for the img2img API")
@argh.arg("-t", "--time", help="Time for the img2img API")
@argh.arg("--msg", help="Message for the img2img API")
@argh.arg("--type", help="Type for the img2img API")
def convert_image(image_path, api_key, model_type, prompt="", neg_prompt="", cfg={}, factor=1, time=0, msg="", type=""):
	""" Convert an image to another image using the img2img API """
	logger.info("Converting image: %s", image_path)

	cv2_img = cv2.imread(image_path)

	# Convert cv2 image to base64 encoding
	_, buffer = cv2.imencode('.jpg', cv2_img)
	img_base64 = base64.b64encode(buffer).decode('utf-8')

	# Prepare API params
	params = {
		'model': model_type,
		'access_key': api_key,
		'data': img_base64,
		'datatype': 'base64',
		'prompt': prompt,
		'neg_prompt': neg_prompt,
		'cfg': cfg,
		'factor': factor,
		'time': time,
		'msg': msg,
		'type': type
	}

	# POST request to img2img API
	api_url = 'https://api.openai.com/v1/images/generations/ited/img'
	response = requests.post(api_url, json=params)

	if response.status_code == 200:
		return json.loads(response.text)
	else:
		return f"Error: {response.status_code} - {response.text}"

if __name__ == "__main__":
	argh.dispatch_command(convert_image)

