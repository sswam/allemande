#!/usr/bin/env python3

"""
Collects JavaScript code and selected HTML elements from HTML/Markdown files.
Combines them into a single output, optionally converting modern JS declarations to var.
"""

import re
from typing import Sequence
from bs4 import BeautifulSoup
import esprima  # type: ignore

from ally import main, logs  # type: ignore

__version__ = "0.1.2"

logger = logs.get_logger()


class CodeCollectorJS:
    """Collects JavaScript code and HTML elements from files using configurable selectors."""

    def __init__(self, selectors: list[str] | None = None) -> None:
        """Initialize collector with optional CSS selectors.

        Args:
            selectors: List of CSS selectors to extract matching elements
        """
        self.selectors = selectors or []
        self.scripts: dict[str, str] = {}    # Latest version of each script block
        self.elements: dict[str, str] = {}   # Latest version of each selected element

    def process_file(self, filename: str) -> None:
        """Process a single file and collect its code."""
        try:
            with open(filename, encoding='utf-8') as f:
                content = f.read()
            self.process_content(content)
        except OSError as e:
            logger.error("Failed to read file %s: %s", filename, e)
            raise

    def process_content(self, content: str) -> None:
        """Process HTML/Markdown content and collect code."""
        soup = BeautifulSoup(content, 'html.parser')

        for script in soup.find_all('script'):
            if script.string:
                self._process_script(script.string)

        for selector in self.selectors:
            for element in soup.select(selector):
                key = self._get_element_key(element)
                self.elements[key] = str(element)

    def _process_script(self, script_content: str) -> None:
        """Extract global declarations from JavaScript code."""
        try:
            ast = esprima.parseScript(script_content)
            code: list[str] = []
            for node in ast.body:
                if node.type == 'FunctionDeclaration':
                    name = node.id.name
                    self.scripts[name] = self._extract_source(script_content, node)
                elif node.type == 'VariableDeclaration':
                    for decl in node.declarations:
                        if hasattr(decl.id, 'name'):
                            name = decl.id.name
                            self.scripts[name] = self._extract_source(script_content, decl)
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("Failed to parse script: %s", e)

    def _extract_source(self, source: str, node) -> str:
        """Extract original source code for an AST node."""
        return source[node.range[0]:node.range[1]]

    def _get_element_key(self, element) -> str:
        """Generate a unique key for an element based on its attributes."""
        selector = self.selectors[0] if self.selectors else ''  # Get current selector
        if element.get('id'):
            return f"{selector}_{element['id']}"
        if element.get('class'):
            return f"{selector}_{'_'.join(element['class'])}"
        return f"{selector}_{str(hash(str(element)))}"

    def get_collected_code(self, remove_const_let: bool = False) -> str:
        """Return all collected code concatenated.

        Args:
            remove_const_let: If True, replace const/let declarations with var
        """
        code = []
        code.extend(self.elements.values())

        for script in self.scripts.values():
            if remove_const_let:
                script = re.sub(r'\b(const|let)\b', 'var', script)
            code.append(script)

        return '\n\n'.join(code)


def collect_code(
    files: Sequence[str],
    selectors: list[str] | None = None,
    remove_const_let: bool = False
) -> None:
    """Process files and print collected code to stdout."""
    collector = CodeCollectorJS(selectors)
    for file in files:
        collector.process_file(file)
    print(collector.get_collected_code(remove_const_let))


def setup_args(arg):
    """Set up command-line arguments."""
    arg("files", nargs="*", help="files to process")
    arg("-s", "--selector", action="append", help="CSS selector to extract")
    arg("-r", "--remove-const-let", action="store_true", help="replace const/let with var")


if __name__ == "__main__":
    main.go(collect_code, setup_args)


# Claude: You might want to consider these additional improvements for the future:
# 1. Add support for JSX/TSX parsing
# 2. Add options to format/minify output
# 3. Add support for source maps
# 4. Add ability to filter collected code by patterns
# 5. Add support for collecting from URLs
