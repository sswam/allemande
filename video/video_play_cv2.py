#!/usr/bin/env python3

""" video-play-cv2.py: A Python script to play a video file using OpenCV. """

import numpy as np
import cv2
import sys

file = sys.argv[1]

cap = cv2.VideoCapture(file)

while(cap.isOpened()):
	ret, frame = cap.read()
	cv2.imshow('frame',frame)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

cap.release()
cv2.destroyAllWindows()


# The given Python script uses the OpenCV library to open and display a video
# file. The video file's name is provided as a command-line argument while
# running the script. The script reads each frame from the video and shows it in
# a window. It continues to display frames until the 'q' key is pressed or the
# video reaches its end, after which the program terminates.
