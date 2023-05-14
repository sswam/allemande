#!/usr/bin/env python3 

import os
import numpy as np
from PIL import Image

# Load image
img = Image.open('banner.png')
img_array = np.array(img)

offset = 256

# Save image
for i in range(1, 8):
	# Shift image
	shifted_img_array = np.roll(img_array, -offset, axis=1)
	shifted_img = Image.fromarray(shifted_img_array)
	shifted_img.save(f'banner{i}.png')
	img_array = shifted_img_array

if not os.path.exists('banner0.png'):
	os.symlink('banner.png', 'banner0.png')
