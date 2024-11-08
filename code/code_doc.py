#!/usr/bin/env python3-allemande

"""
Document code files and their dependencies.
"""

import os
import re
import sys
from graphlib import TopologicalSorter
from typing import TextIO
from io import StringIO

from argh import arg
import llm
import cat_named

from ally import main, text

__version__ = "1.0.8"

logger = main.get_logger()


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
        return set(re.findall(r'^(?:import|from)\s+(\w+)', content, re.MULTILINE))
    elif ext == '.pl':
        return set(re.findall(r'^\s*use\s+(\S+)', content, re.MULTILINE))
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
        return set(re.findall(r'^(?:source|\.)\s+(\S+)', content, re.MULTILINE))
    else:
        logger.warning(f"Unsupported file type for {file}")
        return set()


def document_file(file: str, deps: set[str], prompt: str, model: str, pass_type: str) -> None:
    """Document a single file."""
    logger.info(f"Documenting: {file} ({pass_type})")

    content = [
        f"File: {file}",
        "Dependencies:",
        *([f"- {dep}" for dep in deps] if deps else ["None"]),
        "Content:",
    ]

    try:
        cat_named_output = cat_named.cat_named([file] + [f"{dep}.md" for dep in deps], missing_ok=True)
        content.append(cat_named_output)
    except Exception as e:
        logger.error(f"Error getting file content: {e}")
        content.append("Error: Unable to get file content")

    full_content = "\n".join(content)

    try:
        istream = StringIO(full_content)
        documented = llm.process(prompt, istream=istream, model=model)
        with open(f"{file}.md", "w") as f:
            f.write(documented)
        print(documented)
    except Exception as e:
        logger.error(f"Error documenting {file}: {e}")

    print()


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


@arg('files', nargs='*', help='Files to document')
@arg('--prompt', help='Custom prompt for documentation')
@arg('--model', help='AI model to use for documentation')
@arg('--dump-deps', choices=['tsv', 'graphviz', 'mermaid'], help='Dump dependencies in specified format')
def code_doc(
    *files: list[str],
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    prompt: str = "",
    model: str = "",
    dump_deps: str = None
) -> None:
    """Document code files and their dependencies."""
    get, put = main.io(istream, ostream)

    prompt = text.squeeze(f"""Please document this code file / module completely but very concisely in markdown.
    Emphasise recording the public API with signatures, a few examples, and concise descriptions.
    Provide a heading being the pathname to the module, a short description of the module as a whole,
    and a compact cheat-sheet for using the modules's public API. {prompt}""")

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
        return

    # Process files in order, reprocessing as needed to handle mutual dependencies
    processed = set()
    reprocess = []

    for file in sorted_files:
        if not os.path.isfile(file):
            continue

        deps = dep_cache.get(file, set())
        unmet = any(dep not in processed for dep in deps)

        if not unmet:
            document_file(file, deps, prompt, model, "Initial Pass")
            processed.add(file)

            new_reprocess = []
            for rfile in reprocess:
                rdeps = dep_cache.get(rfile, set())
                if all(rdep not in reprocess for rdep in rdeps):
                    document_file(rfile, rdeps, prompt, model, "Reprocess")
                    processed.add(rfile)
                else:
                    new_reprocess.append(rfile)
            reprocess = new_reprocess
        else:
            reprocess.append(file)

    if reprocess:
        logger.warning("Some files could not be processed with their full set of dependencies.")

        for rfile in reprocess:
            logger.warning(f"Processing {rfile} in final pass. Documentation may be incomplete.")
            document_file(rfile, dep_cache.get(rfile, set()), prompt, model, "Final Pass (Warning: Possible incomplete documentation)")


if __name__ == "__main__":
    main.run(code_doc)
