#!/usr/bin/env python3

import os
from pathlib import Path
from bs4 import BeautifulSoup
import re
import argh


def create_symlink(resource_path):
    mtime = int(os.path.getmtime(resource_path))
    symlink_name = f'{resource_path.stem}@{mtime}{resource_path.suffix}'
    target = resource_path.parent / symlink_name
    if not target.exists():
        for symlink in resource_path.parent.glob(f'{resource_path.stem}@*{resource_path.suffix}'):
            if symlink.is_symlink():
                os.remove(symlink)
        os.symlink(resource_path.name, target)
    return symlink_name


def remove_timestamp_from_filename(filename):
    return re.sub(r'(@\d+)', '', filename)


def update_html_files(html_files, resource_files):
    for html_file in html_files:
        with open(html_file, 'r') as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        for element in soup():
            update_element = False
            attribute = None

            if element.name == 'link' and 'href' in element.attrs:
                attribute = 'href'
                update_element = element['href'].endswith('.css')
            elif element.name == 'script' and 'src' in element.attrs:
                attribute = 'src'
                update_element = element['src'].endswith('.js')
            elif element.name == 'img' and 'src' in element.attrs:
                attribute = 'src'
                update_element = element['src'].endswith(('.jpg', '.jpeg', '.png', '.gif'))

            if update_element:
                original_name = remove_timestamp_from_filename(element[attribute])
                resource_path = Path(original_name)
                if resource_path in resource_files:
                    new_symlink = resource_files[resource_path]
                    element[attribute] = str(new_symlink)

        with open(html_file, 'w') as file:
            file.write(str(soup))


def update_symlinks()
    resource_dir = Path('.')
    html_files = list(resource_dir.glob('*.html'))
    css_files = list(resource_dir.glob('**/*.css'))
    js_files = list(resource_dir.glob('**/*.js'))
    image_files = list(resource_dir.glob('**/*.[jp][pn]g')) + list(resource_dir.glob('**/*.gif'))

    resource_files = css_files + js_files + image_files
    new_symlinks = {}

    for resource_path in resource_files:
        if '@' in resource_path.name:
            continue
        new_symlink = create_symlink(resource_path)
        new_symlinks[resource_path] = resource_path.parent / new_symlink

    update_html_files(html_files, new_symlinks)


if __name__ == '__main__':
    argh.dispatch_command(update_symlinks)
