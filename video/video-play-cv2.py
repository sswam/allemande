#!/usr/bin/env python3

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
