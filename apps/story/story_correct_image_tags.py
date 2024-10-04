#!/usr/bin/env python3

""" Corrects image tags in a markdown file """

import sys
import re

def correct_image_tags(input_text):
    def fix_tag(match):
        full_tag = match.group(0)
        description = match.group(1)
        filename = match.group(2)
        width_height = match.group(3)

        # Remove backticks if present
        full_tag = full_tag.strip('`')

        # Remove (widthxheight) from description if present
        description = re.sub(r'\s*\(\d+x\d+\)$', '', description)

        # Replace spaces with underscores in filename
        filename = filename.replace(' ', '_')

        # Replace .jpg with .png
        filename = re.sub(r'\.jpg$', '.png', filename)

        # Reconstruct the tag
        corrected_tag = f'![{description}]({filename})'

        # Add width and height comment if present
        if width_height:
            corrected_tag += width_height

        return corrected_tag

    # Regular expression to match the image tag pattern
    pattern = r'`?!\[(.*?)\]\((.*?)\)(\s*<!--\s*\{.*?\}\s*-->)?`?'

    # Apply the fixes using re.sub with the fix_tag function
    corrected_text = re.sub(pattern, fix_tag, input_text)

    return corrected_text

# run it for each line of stdin -> stdou
def correct_image_tags_stdio():
    for line in sys.stdin:
        print(correct_image_tags(line.rstrip()))

def test_correct_image_tags():
    # Test the function
    test_input = '`![description of the file (1200x800)](file name.png)<!--{width=1200 height=800}-->`'
    result = correct_image_tags(test_input)
    print(result)

if __name__ == '__main__':
    correct_image_tags_stdio()
