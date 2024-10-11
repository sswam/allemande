import os

# Disable DeprecationWarning https://github.com/jupyter/jupyter_core/issues/398
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

import io
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import logging
import argparse

import ally.geput as subject

__version__ = "0.1.4"

