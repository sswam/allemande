#!/usr/bin/env python3-allemande

""" Resize and crop images centered on the focal point. """

import cv2
import numpy as np
import sys
import argparse
import argh

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_focal_point(img):
	""" Find the focal point of an image. """
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	blur = cv2.GaussianBlur(gray, (5, 5), 0)
	_, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
	contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	focal_point = None
	max_area = 0
	for contour in contours:
		area = cv2.contourArea(contour)
		if area > max_area:
			max_area = area
			M = cv2.moments(contour)
			if M["m00"] != 0:
				cx = int(M["m10"] / M["m00"])
				cy = int(M["m01"] / M["m00"])
				focal_point = (cx, cy)
	return focal_point

@argh.arg("input_file", help="Input image file.")
@argh.arg("output_file", help="Output image file.")
@argh.arg("width", type=int, help="Width of the output image.")
@argh.arg("height", type=int, help="Height of the output image.")
@argh.arg("--no-center", dest="center_focal_point", action="store_false", help="Do not center image on focal point.")
@argh.arg("--crop-first", dest="crop_first", action="store_true", help="Crop first, then resize.")
@argh.arg("--interpolation", dest="interpolation", default=cv2.INTER_LANCZOS4, help="Interpolation method.")
def resize_crop_image(input_file, output_file, width, height, center_focal_point=True, crop_first=False, interpolation=cv2.INTER_LANCZOS4):
	""" Resize and crop images centered on the focal point. """

	img = cv2.imread(input_file)
	h, w, _ = img.shape

	logger.info("Input size: {}x{}".format(w, h))
	logger.info("Output size: {}x{}".format(width, height))
	focal_point = find_focal_point(img)
	logger.info("Focal point: {}".format(focal_point))

	if w / h < width / height:
		scale = width / w
	else:
		scale = height / h

	logger.info("Scale: {}".format(scale))

	if center_focal_point:
		if w / h < width / height:
			x1 = 0
			x2 = width
			y1 = scale * focal_point[1] - height/2
			y2 = scale * focal_point[1] + height/2
		else:
			y1 = 0
			y2 = height
			x1 = scale * focal_point[0] - width/2
			x2 = scale * focal_point[0] + width/2
	else:
		x1 = 0
		y1 = 0
		x2 = width
		y2 = height

	logger.info("Crop after scale: {}x{}-{}x{}".format(x1, y1, x2, y2))

	x1s = x1 / scale
	y1s = y1 / scale
	x2s = x2 / scale
	y2s = y2 / scale

	logger.info("Scaled crop: {}x{}-{}x{}".format(x1s, y1s, x2s, y2s))

	if crop_first:
		logger.info("Cropping first.")
		cropped_img = img[int(x1s):int(x2s), int(y1s):int(y2s)]
		resized_img = cv2.resize(cropped_img, (width, height), interpolation=interpolation)
	else:
		logger.info("Resizing first.")
		resized_img = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=interpolation)
		cropped_img = resized_img[x1:x2, y1:y2]

	# q. best quality option?
	# a. INTER_CUBIC is slowest but best quality
	# q. no lanczos?
	# a. INTER_LANCZOS4 is lanczos
	# q. that's better quality than INTER_CUBIC?
	# a. yes, but slower
	# q. any even better?
	# a. INTER_LANCZOS4 is the best

	logger.info("Cropped size: {}x{}".format(cropped_img.shape[1], cropped_img.shape[0]))
	cv2.imwrite(output_file, cropped_img)

if __name__ == "__main__":
    argh.dispatch_command(resize_crop_image)

#	parser = argparse.ArgumentParser(description="Resize and crop images centered on the focal point.")
#	parser.add_argument("input_file", help="Input image file.")
#	parser.add_argument("output_file", help="Output image file.")
#	parser.add_argument("width", type=int, help="Width of the output image.")
#	parser.add_argument("height", type=int, help="Height of the output image.")
#	parser.add_argument("--no-center", dest="center_focal_point", action="store_false",
#						help="Do not center image on focal point.")
#
