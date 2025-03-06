""" Allemande chat file format library """

from pathlib import Path


def safe_join(base_dir: Path | str, *paths: str | Path) -> Path:
    """
    Return a safe path under base_dir, or raise ValueError if the path is unsafe.

    Args:
        base_dir: Base directory path
        *paths: Additional path components to join

    Returns:
        Path: Safe resolved path

    Raises:
        ValueError: If resulting path would be outside base_dir
    """
    base_dir = Path(base_dir).resolve()

    # Join the paths first before resolving
    full_path = base_dir.joinpath(*[str(p) for p in paths])
    # Then resolve to handle any .. or . in the path
    full_path = full_path.resolve()

    try:
        # Use relative_to() to check if path is under base_dir
        full_path.relative_to(base_dir)
        return full_path
    except ValueError as e:
        raise ValueError(f"Path {full_path} is outside base directory {base_dir}") from e
