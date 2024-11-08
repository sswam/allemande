#!/usr/bin/env python3-allemande

"""
keyboard_layout.py - Generate SVG or HTML keyboard layout diagrams with key bindings.
"""

import sys
import logging
from typing import TextIO, Dict, List
import argparse
import html

from argh import arg
import xml.etree.ElementTree as ET

from ally import main

__version__ = "0.1.4"

logger = main.get_logger()

KEYBOARD_LAYOUT = [
    # Main keys
    [
        ['Esc', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'Mute'],
        ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'Backspace'],
        ['Tab', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '[', ']', '\\'],
        ['Caps', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', "'", 'Enter'],
        ['Shift', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/', 'Shift'],
        ['Ctrl', 'Super', 'Alt', 'Space', 'Alt', 'Fn', 'Ctrl']
    ],
    # Arrows and special keys
    [
        ['*1', '*2', '*3'],
        ['Ins', 'Home', 'PgUp'],
        ['Del', 'End', 'PgDn'],
        [],
        ['', '↑', ''],
        ['←', '↓', '→']
    ],
    # Numeric keypad
    [
        ['Calc', 'Print', 'Menu', 'Lock'],
        ['Num', '/', '*', '-'],
        ['7', '8', '9', '+'],
        ['4', '5', '6', ''],
        ['1', '2', '3', 'Enter'],
        ['0', '.', '', '']
    ]
]

KEY_WIDTH = 60
KEY_HEIGHT = 60
KEY_SPACING = 5
FONT_SIZE = 14
BINDING_FONT_SIZE = 9
CANVAS_WIDTH = 1600

def parse_key_bindings(input_file: TextIO) -> Dict[str, Dict[str, str]]:
    """Parse the input file and return a dictionary of key bindings."""
    bindings = {}
    for line in input_file:
        parts = line.strip().split('\t')
        if len(parts) == 2:
            key_combo, action = parts
            key_combo = key_combo.replace('$mod', 'mod').lower()
            key_parts = key_combo.split('+')
            # modifiers = sorted(key_parts[:-1])
            modifiers = key_parts[:-1]
            base_key = key_parts[-1]
            if base_key not in bindings:
                bindings[base_key] = {}
            mod_key = '+'.join(modifiers) if modifiers else 'default'
            bindings[base_key][mod_key] = action
    return bindings

def create_svg_element() -> ET.Element:
    """Create the root SVG element."""
    svg = ET.Element('svg', {
        'xmlns': 'http://www.w3.org/2000/svg',
        'width': str(CANVAS_WIDTH),
        'height': '500'
    })
    return svg

def create_key_svg(x: float, y: float, width: float, height: float, label: str, bindings: Dict[str, str], attached_bindings: set) -> ET.Element:
    """Create an SVG group element representing a key."""
    group = ET.Element('g')
    rect = ET.SubElement(group, 'rect', {
        'x': str(x),
        'y': str(y),
        'width': str(width),
        'height': str(height),
        'fill': 'white',
        'stroke': 'black',
        'stroke-width': '2'
    })
    text = ET.SubElement(group, 'text', {
        'x': str(x + width / 2),
        'y': str(y + height / 2),
        'text-anchor': 'middle',
        'dominant-baseline': 'central',
        'font-size': str(FONT_SIZE)
    })
    text.text = label

    # Draw key bindings
    positions = {
        'mod': (x + 5, y + height - 5, 'start', 'auto', 'blue'),
        'mod+shift': (x + 5, y + 10, 'start', 'hanging', 'green'),
        'mod+ctrl': (x + width - 5, y + height - 5, 'end', 'auto', 'red'),
        'mod+ctrl+shift': (x + width - 5, y + 10, 'end', 'hanging', 'purple'),
    }
    for modifiers, (tx, ty, anchor, baseline, color) in positions.items():
        action = bindings.get(modifiers)
        if action:
            mod_text = ET.SubElement(group, 'text', {
                'x': str(tx),
                'y': str(ty),
                'text-anchor': anchor,
                'dominant-baseline': baseline,
                'font-size': str(BINDING_FONT_SIZE),
                'fill': color
            })
            mod_text.text = action
            attached_bindings.add(f"{modifiers}+{label.lower()}" if modifiers != 'default' else label.lower())

    return group

def generate_keyboard_layout_svg(layout: List[List[List[str]]], bindings: Dict[str, Dict[str, str]], attached_bindings: set) -> ET.Element:
    svg = create_svg_element()
    x_offset = 20
    for section_index, section in enumerate(layout):
        y_offset = 20
        max_width = 0
        for row in section:
            key_widths = []
            wide_keys_total_width = 0
            normal_keys_total_width = 0
            for index, key in enumerate(row):
                width = KEY_WIDTH
                if key == '':
                    pass
                elif key in ['Tab']:
                    width *= 1.5
                elif key == '\\':
                    width *= 1.25
                elif key in ['Esc', 'Caps']:
                    width *= 1.75
                elif key == 'Shift':
                    width *= 2.25 if index == 0 else 2.75
                elif key in ['Ctrl', 'Alt', 'Super', 'Fn']:
                    width *= 1.25
                elif key == 'Backspace':
                    width *= 2.25
                elif key == 'Enter' and section_index == 0:
                    width *= 2.25
                elif key == 'Space':
                    width *= 6.25

                if width > KEY_WIDTH:
                    wide_keys_total_width += width
                else:
                    normal_keys_total_width += width

                key_widths.append(width)

            if section_index == 0 and wide_keys_total_width > 0:
                desired_row_width = 950
                total_gaps = KEY_SPACING * (len(row) - 1)
                wide_keys_scale = (desired_row_width - total_gaps - normal_keys_total_width) / wide_keys_total_width
            else:
                wide_keys_scale = 1

            current_x = x_offset
            for width, key in zip(key_widths, row):
                if width > KEY_WIDTH:
                    width *= wide_keys_scale
                height = KEY_HEIGHT
                if key in ['+', 'Enter'] and section_index == 2:
                    height = height * 2 + KEY_SPACING
                if key == '0' and section_index == 2:
                    width = width * 2 + KEY_SPACING
                if key == '':
                    current_x += width + KEY_SPACING
                    continue

                key_bindings = bindings.get(key.lower(), {})
                key_element = create_key_svg(current_x, y_offset, width, height, key, key_bindings, attached_bindings)
                svg.append(key_element)
                current_x += width + KEY_SPACING

            y_offset += KEY_HEIGHT + KEY_SPACING
            max_width = max(max_width, current_x - x_offset)
        x_offset += max_width + KEY_SPACING * 5
    return svg

def output_unattached_bindings(bindings: Dict[str, Dict[str, str]], attached_bindings: set) -> None:
    """Output all bindings that couldn't be attached to keys."""
    unattached = []
    for key, mods in bindings.items():
        for mod, action in mods.items():
            binding = f"{mod}+{key}" if mod != 'default' else key
            if binding not in attached_bindings:
                unattached.append(f"{binding}\t{action}")

    if unattached:
        print("Unattached bindings:", file=sys.stderr)
        for binding in sorted(unattached):
            print(binding, file=sys.stderr)

@arg('input_file', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help='Input file with key bindings')
@arg('--output', '-o', help='Output file')
@arg('--format', '-f', choices=['svg', 'html'], default='svg', help='Output format (svg or html)')
def keyboard_layout(
    input_file: TextIO,
    output: str = None,
    format: str = 'svg'
) -> None:
    """
    Generate a keyboard layout diagram with key bindings.
    """
    bindings = parse_key_bindings(input_file)
    attached_bindings = set()

    if format == 'svg':
        svg = generate_keyboard_layout_svg(KEYBOARD_LAYOUT, bindings, attached_bindings)
        tree = ET.ElementTree(svg)
        if output:
            tree.write(output, encoding='unicode', xml_declaration=True)
        else:
            tree.write(sys.stdout, encoding='unicode', xml_declaration=True)
    else:  # HTML
        print("HTML output is not yet implemented.")

    output_unattached_bindings(bindings, attached_bindings)

if __name__ == "__main__":
    main.run(keyboard_layout)
