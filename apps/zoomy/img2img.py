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
def convert_image(
	image_path, init_images, resize_mode, denoising_strength, image_cfg_scale, mask,
	mask_blur, inpainting_fill, inpainting_mask_invert, initial_noise_multiplier, prompt,
	styles, seed, subseed, subseed_strength, seed_resize_from_h, seed_resize_from_w,
	sampler_name, batch_size, n_iter, steps, cfg_scale, width, height, restore_faces,
	tiling, do_not_save_samples, do_not_save_grid, negative_prompt, eta, s_churn, s_tmax,
	s_tmin, s_noise, override_settings, override_settings_restore_afterwards, script_args,
	sampler_index, include_init_images, script_name, send_images, save_images, alwayson_scripts):

	logger.info("Converting image: %s", image_path)

	cv2_img = cv2.imread(image_path)

	# Convert cv2 image to base64 encoding
	_, buffer = cv2.imencode('.jpg', cv2_img)
	img_base64 = base64.b64encode(buffer).decode('utf-8')

	# Prepare API params
	params = {
		'init_images': init_images,
		'resize_mode': resize_mode,
		'denoising_strength': denoising_strength,
		'image_cfg_scale': image_cfg_scale,
		'mask': mask,
		'mask_blur': mask_blur,
		'inpainting_fill': inpainting_fill,
		'inpaint_full_res': inpaint_full_res,
		'inpaint_full_res_padding': inpaint_full_res_padding,
		'inpainting_mask_invert': inpainting_mask_invert,
		'initial_noise_multiplier': initial_noise_multiplier,
		'prompt': prompt,
		'styles': styles,
		'seed': seed,
		'subseed': subseed,
		'subseed_strength': subseed_strength,
		'seed_resize_from_h': seed_resize_from_h,
		'seed_resize_from_w': seed_resize_from_w,
		'sampler_name': sampler_name,
		'batch_size': batch_size,
		'n_iter': n_iter,
		'steps': steps,
		'cfg_scale': cfg_scale,
		'width': width,
		'height': height,
		'restore_faces': restore_faces,
		'tiling': tiling,
		'do_not_save_samples': do_not_save_samples,
		'do_not_save_grid': do_not_save_grid,
		'negative_prompt': negative_prompt,
		'eta': eta,
		's_churn': s_churn,
		's_tmax': s_tmax,
		's_tmin': s_tmin,
		's_noise': s_noise,
		'override_settings': override_settings,
		'override_settings_restore_afterwards': override_settings_restore_afterwards,
		'script_args': script_args,
		'sampler_index': sampler_index,
		'include_init_images': include_init_images,
		'script_name': script_name,
		'send_images': send_images,
		'save_images': save_images,
		'alwayson_scripts': alwayson_scripts
	}

	# POST request to the local Automatic1111 Stable Diffusion WebUI img2img API
	api_url = ''
#	api_url = 'https://api.openai.com/v1/images/generations/ited/img'
	response = requests.post(api_url, json=params)

	if response.status_code == 200:
		return json.loads(response.text)
	else:
		return f"Error: {response.status_code} - {response.text}"

if __name__ == "__main__":
	argh.dispatch_command(convert_image)

