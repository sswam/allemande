"""Allemande YAML handler based on both ruamel.yaml and cyaml for speed and correctness"""

import re
from typing import Any, TextIO
import io

import ruamel.yaml
import yaml


# 1. Fast mode hard-depends on yaml.CSafeDumper; will raise AttributeError
# if libyaml C extension isn't installed. Add a fallback to SafeDumper or
# feature-detect availability.
# 
# 
# 4. Reading is forced to pure Python (pure=True) in ruamel, which can be
# significantly slower; consider allowing C-accelerated mode when available.


class YAML:
    """Allemande YAML handler based on both ruamel.yaml and cyaml for speed and correctness"""
    def __init__(self, fast_write: bool = False):
        # Initialize ruamel.yaml for reading
        self._ryaml = ruamel.yaml.YAML(typ='safe', pure=True)
        self._ryaml.default_flow_style = False
        self._ryaml.indent(mapping=2, sequence=4, offset=2)

        # Store write mode preference
        self._fast_write = fast_write

        # Add custom string presenter if needed
        if hasattr(self._ryaml, 'representer'):
            self._ryaml.representer.add_representer(str, self._str_presenter)

    @staticmethod
    def _str_presenter(dumper: Any, data: str) -> Any:
        """
        Presenter for strings that detects multi-line strings and formats them
        using the literal style (|) indicator
        """
        if re.search(r".\n.", data, flags=re.DOTALL):
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    def load(self, stream: str | TextIO) -> Any:
        """Load YAML content using ruamel.yaml"""
        return self._ryaml.load(stream)

    def safe_load(self, stream: str | TextIO) -> Any:
        """Safe load YAML content using ruamel.yaml"""
        return self._ryaml.load(stream)  # ruamel's load is already safe

    def dump(self, data: Any, stream: TextIO | None = None) -> str | None:
        """Dump YAML content using either cyaml or ruamel.yaml based on settings"""
        if self._fast_write:
            return yaml.dump(data, stream=stream, Dumper=yaml.CSafeDumper, default_flow_style=False, sort_keys=False)

        if stream is None:
            string_stream = io.StringIO()
            self._ryaml.dump(data, string_stream)
            return string_stream.getvalue()

        self._ryaml.dump(data, stream)
        return None

    def set_fast_write(self, enabled: bool = True) -> None:
        """Toggle between fast (cyaml) and careful (ruamel) writing"""
        self._fast_write = enabled


def create(fast_write: bool = False) -> YAML:
    """Factory function to create an YAML instance"""
    return YAML(fast_write=fast_write)


# Module-level convenience functions


_default_instance = YAML()


def load(stream: str | TextIO) -> Any:
    return _default_instance.load(stream)


def safe_load(stream: str | TextIO) -> Any:
    return _default_instance.safe_load(stream)


def dump(data: Any, stream: TextIO | None = None) -> str | None:
    return _default_instance.dump(data, stream)
