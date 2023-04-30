#!/usr/bin/env python3

import numpy as np
import cv2
import sys

file = sys.argv[1]

cap = cv2.VideoCapture(file)

frame_prev = None

diffs = []

while(cap.isOpened()):
	ret, frame = cap.read()
	frame = frame.astype(np.float32)
	# frame2 = frame.astype(np.uint8)
	# cv2.imshow('frame',frame2)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break
	if frame_prev is not None:
		diff = (frame - frame_prev) / 256
		diff_rms = np.sqrt(np.mean(diff ** 2))
		diffi = ((diff/2+0.5) * 256).astype(np.uint8)
		print(diff_rms)
		cv2.imshow('frame', diffi)
		diffs.append(diff_rms)
	frame_prev = frame

cap.release()
cv2.destroyAllWindows()
