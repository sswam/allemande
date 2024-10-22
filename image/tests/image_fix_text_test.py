import numpy as np
from PIL import Image

from image_fix_text import image_apply_background


def test_image_apply_background():
    # Let's do 4 different pixels, including translucent, transparent and opaque, and black and white
    image = np.array([
        [[0, 0, 0, 0], [255, 255, 255, 0]],
        [[0, 0, 0, 128], [255, 255, 255, 255]],
    ], dtype=np.uint8)

    # Test with a white background
    # Every pixel should be opaque in the result
    result = image_apply_background(image, (255, 255, 255, 0))
    assert np.all(result == np.array([
        [[0, 0, 0, 0], [255, 255, 255, 0]],
        [[128, 128, 128, 0], [255, 255, 255, 0]],
    ], dtype=np.uint8))

    # Test with a black background
    # Every pixel should be opaque in the result
    result = image_apply_background(image, (0, 0, 0, 0))
    assert np.all(result == np.array([
        [[0, 0, 0, 0], [255, 255, 255, 0]],
        [[0, 0, 0, 0], [0, 0, 0, 0]],
    ], dtype=np.uint8))

    # Test with a transparent background
    result = image_apply_background(image, (0, 0, 0, 255))
    assert np.all(result == np.array([
        [[0, 0, 0, 0], [255, 255, 255, 0]],
        [[0, 0, 0, 128], [0, 0, 0, 255]],
    ], dtype=np.uint8))

    # Test with a 25% translucent white background
    result = image_apply_background(image, (255, 255, 255, 64))
    assert np.all(result == np.array([
        [[0, 0, 0, 0], [255, 255, 255, 0]],
        [[128, 128, 128, 32], [255, 255, 255, 64]],
    ], dtype=np.uint8))
