import os
import io
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import logging
import argparse

import ally.meta as subject

subject_name = subject.__name__

__version__ = "0.1.4"


def test_get_module_name():
    assert subject.get_module_name() == f'meta_test'
    assert subject.get_module_name(ext=True) == f'meta_test.py'


def test_get_script_name():
    assert subject.get_script_name() == Path(sys.argv[0]).stem.replace("_", "-")
    assert subject.get_script_name(canon=False) == Path(sys.argv[0]).name
