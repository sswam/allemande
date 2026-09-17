#!/usr/bin/env bash

# export PYTHON=
# export GIT=
# export VENV_DIR=

# export TORCH_COMMAND="pip install torch==2.12.0 torchvision==0.27.0"

export COMMANDLINE_ARGS="--uv --api --cuda-malloc --cuda-stream --disable-smart-memory --disable-sage --disable-flash --disable-xformers --skip-python-version-check --skip-torch-cuda-test --skip-version-check --skip-prepare-environment --skip-install"

# --fp32-vae

exec bash "$(dirname "$0")/webui.sh"
