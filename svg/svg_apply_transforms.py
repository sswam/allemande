#!/usr/bin/env python3

# I'll edit the file to use a class and handle the 'places' parameter correctly. Here's the updated version:


import xml.etree.ElementTree as ET
import re


class SVGTransformer:
    """Class to handle SVG transformation operations."""

    def __init__(self, places: int = 2):
        """Initialize transformer with specified decimal places for rounding."""
        self.places = places

    def parse_transform(self, transform_str: str) -> tuple[float, float]:
        """Parse transform string and return translation values."""
        if not transform_str:
            return 0, 0

        match = re.match(r"translate\(([-\d.]+)\s*([-\d.]+)?\)", transform_str)
        if match:
            tx = float(match.group(1))
            ty = float(match.group(2) if match.group(2) else 0)
            return tx, ty
        return 0, 0

    def apply_transform_to_element(self, element: ET.Element, tx: float, ty: float) -> None:
        """Apply translation transform to element coordinates."""
        if "cx" in element.attrib:
            element.attrib["cx"] = f"{float(element.attrib['cx']) + tx:.{self.places}f}"
        if "cy" in element.attrib:
            element.attrib["cy"] = f"{float(element.attrib['cy']) + ty:.{self.places}f}"

    def process_svg(self, svg_string: str) -> str:
        """Process SVG string by applying transforms and returning modified SVG."""
        # Parse SVG
        root = ET.fromstring(svg_string)

        # Find all g elements
        for g in root.findall(".//g"):
            # Get transform values
            transform = g.get("transform", "")
            tx, ty = self.parse_transform(transform)

            # Apply transform to all children
            for child in list(g):
                self.apply_transform_to_element(child, tx, ty)
                # Move child to root
                root.append(child)

            # Remove g element
            root.remove(g)

        # Convert back to string
        return ET.tostring(root, encoding="unicode")


if __name__ == "__main__":
    # Test with your SVG
    svg_input = """<svg width="16" height="16" fill="currentColor" version="1.1" viewBox="0 0 16 16"><g transform="translate(-.19 .1)"><ellipse cx="7.9" cy="4.2" rx="4" ry="3"/><ellipse cx="12" cy="4.5" rx="4" ry="3"/><ellipse cx="7.2" cy="8.4" rx="4" ry="3"/><ellipse cx="11" cy="7.2" rx="4" ry="3"/><ellipse cx="4.6" cy="6.2" rx="4" ry="3"/><ellipse cx="3.5" cy="12" rx="1.2" ry=".9"/><ellipse cx="1.7" cy="14" rx=".8" ry=".6"/></g></svg>"""

    # Process the SVG
    transformer = SVGTransformer(places=2)
    result = transformer.process_svg(svg_input)
    print(result)

# TODO this is very limited and specific, needs to be generalized
