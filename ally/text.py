from typing import List, Union
import os
import re

__version__ = "0.1.3"


def read_lines(
    files: Union[str, List[str]], strip: bool = True, lower: bool = False
) -> List[str]:
    """
    Read lines from one or more files.

    Args:
        files (Union[str, List[str]]): A single file path or a list of file paths.
        strip (bool): Whether to strip whitespace from each line. Default is True.
        lower (bool): Whether to convert each line to lowercase. Default is False.

    Returns:
        List[str]: A list of lines from all files.

    Raises:
        FileNotFoundError: If a specified file is not found.
        IOError: If there's an error reading a file.
    """
    all_lines = []

    if isinstance(files, str):
        files = [files]

    for file_path in files:
        with open(file_path, "r") as file:
            for line in file:
                if strip:
                    line = line.strip()
                if lower:
                    line = line.lower()
                all_lines.append(line)

    return all_lines


def squeeze(text: str) -> str:
    """ Squeeze whitespace in the text. """
    return re.sub(r"\s\s+", " ", text)


def stripper(text):
    match = re.match(r"(\s*)(.*\S|)(\s*)$", text, re.DOTALL)
    leading_spaces, text, final_spaces = match.groups()
    return leading_spaces, text, final_spaces


def get_last_n_lines(file_path: str, n: int) -> list[str]:
    """Return the last n lines from a file """
    with open(file_path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        block = 1024
        data = []
        remaining_lines = n
        while remaining_lines > 0 and size > 0:
            if size - block < 0:
                block = size
            size -= block
            f.seek(size, os.SEEK_SET)
            buffer = f.read(block)
            data.insert(0, buffer)
            remaining_lines -= buffer.count(b'\n')
        content = b''.join(data)
        return content.decode('utf-8').splitlines()[-n:]
