#!/usr/bin/env python3-allemande

"""Display EXIF data from images."""

# TODO PNG support

import os
import yaml
from pathlib import Path
import sys
import re

from PIL import Image, ExifTags
from PIL.ExifTags import IFD

from ally import main, logs  # type: ignore

__version__ = "0.1.1"

logger = logs.get_logger()


def get_comment_tag_id() -> int | None:
    """Get the tag ID for UserComment."""
    for tag_id, tag_name in ExifTags.TAGS.items():
        if tag_name == 'UserComment':
            return tag_id
    return None


COMMENT_TAG_ID = get_comment_tag_id()


def load_model_short_dict():
    """Load model short names from .yml files."""

    model_dict = {}
    art_path = Path(os.environ['ALLEMANDE_AGENTS']) / 'art'
    for yml_file in art_path.rglob('*.yml'):
        with open(yml_file) as f:
            data = yaml.safe_load(f)
            model_dict[data['model']] = yml_file.stem

    return model_dict


model_short_dict = load_model_short_dict()


def decode_backslashes(s: str | None) -> str | None:
    """Decode backslashes in a string."""
    if s is None:
        return None
    return s.encode('utf-8').decode('unicode_escape')


def strip_pony_score_tags(s: str | None) -> str | None:
    """Strip pony tags from a string."""
    if s is None:
        return None
    return re.sub(r"""
        ^\(?
        (score_\d+(?:_up)?,?\s*)+
        (?::[0-9.]+\),?\s*)?
    """, '', s, flags=re.VERBOSE)


def parse_comment(comment) -> tuple[str | None, str | None, str | None, str | None, str | None, str | None]:
    """Parse the image comment to extract image gen metadata and prompts"""
    prompt_pos, prompt_neg, seed, model, prompt_unp_pos, prompt_unp_neg = re.match(r"""
        ^(?:(.*)\n)?
        (?:Negative\ prompt:\ (.*)\n)?
        (?:.*?\ Seed:\ (\d+).*?\ Model:\ (.*?),)?
        (?:.*?Unprompted\ Prompt:\ "((?:\\.|.)*?)")?
        (?:.*?Unprompted\ Negative\ Prompt:\ "((?:\\.|.)*?)")?
    """, comment, flags=re.VERBOSE).groups()
    prompt_unp_pos = strip_pony_score_tags(decode_backslashes(prompt_unp_pos))
    prompt_unp_neg = strip_pony_score_tags(decode_backslashes(prompt_unp_neg))
    return seed, model, prompt_pos, prompt_neg, prompt_unp_pos, prompt_unp_neg


def get_comment(img_exif) -> str | None:
    """Get the UserComment from EXIF data."""
    exif_ifd = img_exif.get_ifd(ExifTags.IFD.Exif)
    if not exif_ifd or COMMENT_TAG_ID not in exif_ifd:
        return None
    comment_bytes = exif_ifd[COMMENT_TAG_ID]
    if isinstance(comment_bytes, str):
        return comment_bytes
    encoding = comment_bytes[:8]
    if encoding.endswith(b'\0'):
        encoding = encoding.rstrip(b'\0').decode('ascii')
        comment_bytes = comment_bytes[8:]
    else:
        encoding = "ASCII"
    if encoding == "UNICODE":
        comment = comment_bytes.decode('utf-16')
    elif encoding == "ASCII":
        comment = comment_bytes.decode('ascii', errors='ignore')
    elif encoding == "UTF-8":
        comment = comment_bytes.decode('utf-8', errors='ignore')
    else:
        logger.warning("Unknown EXIF UserComment encoding: %s", encoding)
        comment = comment_bytes.decode('utf-8', errors='ignore')
    return comment


def prompt_add_neg(prompt: str | None, prompt_neg: str | None) -> str:
    """Combine prompt and negative prompt."""
    if prompt is None:
        prompt = ""
    if prompt_neg:
        prompt += " NEGATIVE " + prompt_neg
    return prompt


from collections import namedtuple

Metadata = namedtuple('Metadata', ['seed', 'model', 'model_short', 'prompt_pos', 'prompt_neg', 'prompt_unp_pos', 'prompt_unp_neg', 'alt_text'])

def get_image_metadata(path: str) -> Metadata | None:
    """Extract and display EXIF data from an image file."""
    img = Image.open(path)
    img_exif = img.getexif()

    if img_exif is None:
        logger.warning('Image has no EXIF data: %s', path)
        return

    # # Display base IFD tags
    # for key, val in img_exif.items():
    #     tag = ExifTags.TAGS.get(key, str(key))
    #     print(f'{tag}:{val}')

    # # Display EXIF IFD tags
    # exif_ifd = img_exif.get_ifd(ExifTags.IFD.Exif)
    # if exif_ifd:
    #     for key, val in exif_ifd.items():
    #         tag = ExifTags.TAGS.get(key, str(key))
    #         print(f'{tag}:{val}')

    comment = get_comment(img_exif)
    if comment:
        # print(comment)
        seed, model, prompt_pos, prompt_neg, prompt_unp_pos, prompt_unp_neg = parse_comment(comment)
        model_short = model_short_dict.get(model, model)
        prompt = prompt_add_neg(prompt_pos, prompt_neg)
        prompt_unp = prompt_add_neg(prompt_unp_pos, prompt_unp_neg)
        alt_text = f"#{seed} {model_short}, {prompt_unp} ---- {prompt}"
    else:
        seed = model = model_short = prompt_pos = prompt_neg = prompt_unp_pos = prompt_unp_neg = None
        alt_text = ""

    return Metadata(seed, model, model_short, prompt_pos, prompt_neg, prompt_unp_pos, prompt_unp_neg, alt_text)


def none_to_empty(s: str | None) -> str:
    """Convert None to empty string."""
    return s if s is not None else ""


def exif(istream=sys.stdin, markdown: bool=False) -> None:
    """Process EXIF data from image files listed in input."""
    for line in istream:
        path = line.strip()
        md = None
        if not path:
            continue
        try:
            md = get_image_metadata(path)
        except Exception:  # pylint: disable=broad-except
            logger.error("Failed to process %s", path, exc_info=True)
        if not md:
            print()
        elif markdown:
            print(f"![{md.alt_text}]({path})")
        else:
            row = [path, md.seed, md.model, md.model_short, md.prompt_pos, md.prompt_neg, md.prompt_unp_pos, md.prompt_unp_neg]
            print("\t".join(map(none_to_empty, row)))


def setup_args(arg):
    """Set up command-line arguments. Currently not implemented."""
    arg("-m", "--markdown", action="store_true", help="output as markdown images")


if __name__ == "__main__":
    main.go(exif, setup_args)
