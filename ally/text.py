from typing import List, Union
import os


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
    return " ".join(text.strip().split())
