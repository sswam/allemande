#!/usr/bin/env python3
""" zoom_image.py: Zoom in on a specific point in an image """

import sys
import os
import argh
import logging
import cv2

logger = logging.getLogger(__name__)

def round_int(x):
	return int(round(x))

@argh.arg("input_image_path", help="Path to the input image")
@argh.arg("output_image_path", help="Path to the output zoomed image")
@argh.arg("-z", "--zoom-factor", help="Zoom scale factor")
@argh.arg("-x", "--x_coord", help="X Coordinate to zoom")
@argh.arg("-y", "--y_coord", help="Y Coordinate to zoom")
def zoom_image(input_image_path, output_image_path, zoom_factor=2.0, x_coord=0.0, y_coord=0.0):
	""" Zoom in on a specific point in an image """
	logger.info("Zooming image")

	# Load the image
	image = cv2.imread(input_image_path)

	# Set the zoom parameters
	if x_coord and y_coord:
		zoom_point = (x_coord, y_coord)  # (x, y) coordinates
	else:
		zoom_point = (image.shape[1] // 2, image.shape[0] // 2)  # Use the center of the image by default

	# Calculate the new dimensions after zooming
	new_width = int(image.shape[1] * zoom_factor)
	new_height = int(image.shape[0] * zoom_factor)

	logger.debug("Zoom point: %s", zoom_point)
	logger.debug("New dimensions: %s", (new_width, new_height))

	# Resize the image using the highest quality algorithm
	resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

	# Calculate the new position of the zoom point after the resize
	# We can potentially move the zoom point, but for now we'll just keep it where it is
	new_zoom_point = (zoom_point[0] * zoom_factor, zoom_point[1] * zoom_factor)

	# Crop the image around the new zoom point so that the output image has the same size as the input image
	# but keep the zoom point where it is
	left = new_zoom_point[0] - zoom_point[0]
	right = new_zoom_point[0] + (image.shape[1] - zoom_point[0])
	top = new_zoom_point[1] - zoom_point[1]
	bottom = new_zoom_point[1] + (image.shape[0] - zoom_point[1])

#	print(left, right, top, bottom)
#
#	if left < 0:
#		right += abs(left)
#		left = 0
#	print(left, right, top, bottom)
#	if right > resized.shape[1]:
#		left -= right - resized.shape[1]
#		right = resized.shape[1]
#	print(left, right, top, bottom)
#	if top < 0:
#		bottom += abs(top)
#		top = 0
#	print(left, right, top, bottom)
#	if bottom > resized.shape[0]:
#		top -= bottom - resized.shape[0]
#		bottom = resized.shape[0]
#	print(left, right, top, bottom)

	left, right, top, bottom = map(round_int, (left, right, top, bottom,))

	# pad original image with extra transparent pixels to fit the intended
	# crop, and adjust the crop accordingly.
	# We might not need this code yet but it doesn't hurt to have it here.

	# add pixels at left
	if left < 0:
		resized = cv2.copyMakeBorder(resized, 0, 0, abs(left), 0, cv2.BORDER_CONSTANT, value=(0,0,0))
		right += abs(left)
		left = 0
	
	# add pixels at right
	if right > resized.shape[1]:
		resized = cv2.copyMakeBorder(resized, 0, 0, 0, right - resized.shape[1], cv2.BORDER_CONSTANT, value=(0,0,0))
		left -= right - resized.shape[1]
		right = resized.shape[1]
	
	# add pixels at top
	if top < 0:
		resized = cv2.copyMakeBorder(resized, abs(top), 0, 0, 0, cv2.BORDER_CONSTANT, value=(0,0,0))
		bottom += abs(top)
		top = 0
	
	# add pixels at bottom
	if bottom > resized.shape[0]:
		resized = cv2.copyMakeBorder(resized, 0, bottom - resized.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(0,0,0))
		top -= bottom - resized.shape[0]
		bottom = resized.shape[0]


	logger.debug("Final crop: %s", (left, right, top, bottom))
	logger.debug("Final image size: %s", resized.shape)

	cropped = resized[top:bottom, left:right]

	# Save the output image
	cv2.imwrite(output_image_path, cropped)

if __name__ == "__main__":
	argh.dispatch_command(zoom_image)

