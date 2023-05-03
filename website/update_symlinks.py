#!/usr/bin/env python3

import os
from pathlib import Path
from bs4 import BeautifulSoup


def create_symlink(resource_path):
    mtime = int(os.path.getmtime(resource_path))
    symlink_name = f'{resource_path.stem}@{mtime}{resource_path.suffix}'
    target = resource_path.parent / symlink_name
    if not target.exists():
        for symlink in resource_path.parent.glob(f'{resource_path.stem}@*{resource_path.suffix}'):
            if symlink.is_symlink():
                os.remove(symlink)
        os.symlink(resource_path.name, resource_path.parent / symlink_name)
    return symlink_name


def update_html_files(html_files, resource_files):
    for html_file in html_files:
        with open(html_file, 'r') as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        for resource_path, new_symlink in resource_files.items():
            if resource_path.suffix == '.css':
                tag = 'link'
                attribute = 'href'
            elif resource_path.suffix == '.js':
                tag = 'script'
                attribute = 'src'
            elif resource_path.suffix in {'.jpg', '.jpeg', '.png', '.gif'}:
                tag = 'img'
                attribute = 'src'
            else:
                continue

            for element in soup.find_all(tag, **{attribute: str(resource_path)}):
                element[attribute] = str(new_symlink)

        with open(html_file, 'w') as file:
            file.write(str(soup))


if __name__ == '__main__':
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
