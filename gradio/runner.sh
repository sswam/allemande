#!/bin/bash -eu
set -a
RUNNER_CMD="$1"
GRADIO_ANALYTICS_ENABLED=False
exec ./runner.py "$@"
