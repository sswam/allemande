#!/usr/bin/env python3

"""
Analyze dependencies and generate dependency graph for code files.
"""

import os
import re
import sys
from graphlib import TopologicalSorter
from typing import TextIO

from argh import arg
from ally import main, text

__version__ = "1.0.8"

logger = main.get_logger()

shell_ignore = main.resource('tools/standard_tools.txt')

def get_shell_dependencies(content):
    dependencies = set()
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            words = re.split(r'\s+', line)
            if words[0] not in ['if', 'then', 'else', 'elif', 'fi', 'case', 'esac', 'for', 'while', 'until', 'do', 'done', 'function']:
                dependencies.add(words[0])
            for i, word in enumerate(words):
                if word in ['|', '{', '(', 'then', 'done'] and i + 1 < len(words):
                    dependencies.add(words[i+1])
    return dependencies

def get_perl_dependencies(content):
    dependencies = set()
    dependencies.update(re.findall(r'`([^`]+)`', content))  # backticks
    dependencies.update(re.findall(r'system\s*\(\s*"([^"]+)"', content))  # system calls
    dependencies.update(re.findall(r'qx/([^/]+)/', content))  # qx operator
    return dependencies

def get_python_dependencies(content):
    dependencies = set()
    dependencies.update(re.findall(r'subprocess\.(?:call|run|Popen)\s*\(\s*(?:\[|"|\')([^\s\'"]+)', content))  # subprocess
    dependencies.update(re.findall(r'os\.system\s*\(\s*(?:"|\')([^\'"]+)', content))  # os.system
    dependencies.update(re.findall(r'sh\.([^\s\(]+)', content))  # sh module
    return dependencies

def get_dependencies(file: str, system=False) -> set[str]:
    """Get dependencies based on file extension."""
    ext = os.path.splitext(file)[1].lower()
    try:
        with open(file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {file}")
        return set()

    if ext == '.py':
        dependencies = set(re.findall(r'^(?:import|from)\s+(\w+)', content, re.MULTILINE))
        dependencies.update(get_python_dependencies(content))
        return dependencies
    elif ext == '.pl':
        dependencies = set(re.findall(r'^\s*use\s+(\S+)', content, re.MULTILINE))
        dependencies.update(get_perl_dependencies(content))
        return dependencies
    elif ext in ['.c', '.h', '.cpp', '.cc', '.hpp', '.m']:
        if system:
            matches = re.findall(r'#(?:include|import)\s*[<"]([^">]+)[">]', content)
        else:
            matches = re.findall(r'#(?:include|import)\s*"([^"]+)"', content)
        return set(matches)
    elif ext == '.go':
        return set(re.findall(r'^import\s+\(?\s*"?([\w/]+)"?\)?', content, re.MULTILINE))
    elif ext == '.rs':
        return set(re.findall(r'^use\s+([\w::]+)', content, re.MULTILINE))
    elif ext == '.sh' or (ext == '' and re.match(r'^#!\s*(/usr/bin/env\s+)?(sh|bash|zsh|ksh|dash|ash)', content)):
        dependencies = set(re.findall(r'^(?:source|\.)\s+(\S+)', content, re.MULTILINE))
        dependencies.update(get_shell_dependencies(content))
        return dependencies
    elif ext in ['.md', '.html']:
        links = set(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))  # Markdown links
        links.update(re.findall(r'<a\s+href="([^"]+)"', content))  # HTML links
        images = set(re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content))  # Markdown images
        images.update(re.findall(r'<img\s+src="([^"]+)"', content))  # HTML images
        stylesheets = set(re.findall(r'<link\s+rel="stylesheet"\s+href="([^"]+)"', content))  # CSS links
        return links.union(images).union(stylesheets)
    else:
        logger.warning(f"Unsupported file type for {file}")
        return set()

def dump_dependencies(sorted_files: list[str], dep_cache: dict[str, set[str]], format: str) -> str:
    """Dump dependencies in specified format."""
    lines = []
    seen_files = set()
    if format == 'tsv':
        pass
    elif format == 'graphviz':
        lines.append("digraph G {")
    elif format == 'mermaid':
        lines.append("graph TD")
    else:
        raise ValueError(f"Unsupported format: {format}")
    for file in sorted_files:
        deps = dep_cache.get(file, set())
        if format == 'tsv':
            new_deps = [dep for dep in deps if dep not in seen_files]
            mutual_deps = '*' if new_deps else ''
            lines.append(f"{mutual_deps}\t{file}\t{'\t'.join(deps)}")
        else:
            for dep in deps:
                if format == 'graphviz':
                    lines.append(f'    "{file}" -> "{dep}";')
                elif format == 'mermaid':
                    lines.append(f'    {file} --> {dep}')
        seen_files.add(file)
    if format == 'graphviz':
        lines.append("}")
    return "\n".join(lines) + "\n"

@arg('files', nargs='*', help='Files to analyze')
@arg('--dump-deps', choices=['tsv', 'graphviz', 'mermaid'], help='Dump dependencies in specified format')
def analyze_deps(
    *files: list[str],
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    dump_deps: str = None
) -> None:
    """Analyze dependencies of code files."""
    get, put = main.io(istream, ostream)

    dep_cache: dict[str, set[str]] = {}
    graph = TopologicalSorter()

    for file in files:
        if os.path.isfile(file):
            deps = dep_cache[file] = get_dependencies(file)
            graph.add(file, *deps)
        else:
            logger.warning(f"File not found: {file}")

    try:
        sorted_files = list(graph.static_order())
    except ValueError as e:
        logger.error(f"Cyclic dependencies detected: {e}")
        sorted_files = files

    sorted_files.extend(f for f in files if f not in sorted_files)

    if dump_deps:
        put(dump_dependencies(sorted_files, dep_cache, dump_deps))

if __name__ == "__main__":
    main.run(analyze_deps)

